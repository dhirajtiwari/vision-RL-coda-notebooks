"""
Diagnostics REST API
====================
Enterprise-grade demo API wrapping LangGraph diagnosis with CRM enrichment.

Run: python -m api.main
     uvicorn api.main:app --port 8080
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from datetime import UTC

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from agents.diagnosis_graph import run_diagnosis
from api.schemas import ClaimStatus, DiagnoseRequest, DiagnoseResponse, GraphSubgraphResponse
from config.settings import settings

# Admin pipeline imports for enterprise control
from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl
from graph.enterprise_pipeline.pipelines.smoke_validation import run_smoke_validation
from graph.enterprise_pipeline.pipelines.staging_promotion import run_staging_promotion
from graph.graph_rag import list_products as list_all_products
from graph.graph_visualization import (
    diagnosis_subgraph_from_result,
    get_diagnosis_subgraph,
    get_ontology_schema,
    get_product_subgraph,
)
from graph.neo4j_client import close_driver, neo4j_health, verify_connection

# --- LLMOps: observability + guardrails (kickoff prompt §E/§H) ---------------
from guardrails.input import GuardrailViolation
from guardrails.output import validate_output
from guardrails.pipeline import guard_request
from guardrails.rate_limit import RateLimiter
from integrations.claims_workflow import (
    get_claim,
    list_submitted_claims,
    submit_claim_from_diagnosis,
    update_claim_status,
)
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility
from observability.logging_setup import get_logger, set_request_id, setup_logging
from observability.metrics import (
    METRICS_CONTENT_TYPE,
    observe_diagnosis,
    observe_request,
    render_latest_metrics,
)
from observability.tracing import instrument_fastapi, setup_tracing, span
from runtime.cache import cache_stats_snapshot
from runtime.concurrency_limit import ConcurrencyLimiter, ConcurrencyLimitExceeded
from runtime.partitioning import partition_for_rate_limit
from runtime.redis_client import close_redis_client, redis_health
from services.diagnosis_service import run_full_diagnosis
from utils.connector_status import integration_status
from utils.lineage_store import list_batches

# Configure structured logging + tracing at import time (idempotent).
setup_logging(
    level=settings.log_level,
    json_output=settings.log_json,
    redact=settings.enable_pii_redaction,
)
setup_tracing(
    enabled=settings.otel_enabled,
    service_name=settings.otel_service_name,
    otlp_endpoint=settings.otel_exporter_otlp_endpoint,
    sampler_ratio=settings.otel_traces_sampler_arg,
)

logger = get_logger("diagnostics.api")

_rate_limiter = RateLimiter.from_settings(settings)
_diagnose_limiter = ConcurrencyLimiter.from_settings(settings)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Application lifespan: close shared drivers on shutdown."""
    yield
    close_driver()
    close_redis_client()


app = FastAPI(
    title="Enterprise Diagnostics API",
    description="GraphRAG warranty diagnosis with CRM enrichment and provenance",
    version="1.0.0",
    lifespan=_lifespan,
)

# CORS for Next.js frontend (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach OpenTelemetry auto-instrumentation when OTEL_ENABLED=true (no-op otherwise).
instrument_fastapi(app)


@app.middleware("http")
async def _observability_and_limits(request: Request, call_next):
    """Per-request: correlation id, rate limiting, latency + metrics.

    Kickoff prompt §E (rate limiting) + §H (tracing/metrics/correlation ids).
    """
    import time
    import uuid

    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    set_request_id(request_id)

    # Rate limit keyed by tenant + client (admin token → customer → host).
    client_key = (
        request.headers.get("x-admin-token")
        or request.headers.get("x-customer-id")
        or (request.client.host if request.client else "anon")
    )
    tenant_id = request.headers.get("x-tenant-id") or settings.default_tenant_id
    route = request.url.path
    rate_key = partition_for_rate_limit(client_key=client_key, route=route, tenant_id=tenant_id)
    if route == "/diagnose" and not _rate_limiter.allow(rate_key):
        retry = _rate_limiter.retry_after(rate_key)
        observe_request(route, 429, 0.0)
        return JSONResponse(
            status_code=429,
            content={"detail": "rate limit exceeded"},
            headers={"Retry-After": str(retry), "X-Request-ID": request_id},
        )

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        observe_request(route, 500, time.perf_counter() - start)
        raise
    elapsed = time.perf_counter() - start
    observe_request(route, response.status_code, elapsed)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a controlled 500 instead of leaking stack traces to clients."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health() -> dict:
    nh = neo4j_health()
    return {
        "status": "ok",
        "neo4j": nh["production"]["connected"],
        "neo4j_detail": nh,
        "demo_mode": settings.demo_mode,
        "provenance_enabled": settings.enable_provenance,
        "runtime": {
            "caches": cache_stats_snapshot(),
            "redis": redis_health(),
            "rate_limit_backend": getattr(_rate_limiter, "backend", "memory"),
            "diagnose_concurrency_backend": getattr(_diagnose_limiter, "backend", "memory"),
            "max_concurrent_diagnoses": settings.max_concurrent_diagnoses,
            "enable_diagnose_cache": settings.enable_diagnose_cache,
            "cache_ttl_diagnose_seconds": settings.cache_ttl_diagnose_seconds,
            "etl_connector_max_workers": settings.etl_connector_max_workers,
            "neo4j_max_connection_pool_size": settings.neo4j_max_connection_pool_size,
            "default_tenant_id": settings.default_tenant_id,
        },
    }


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus scrape endpoint (kickoff prompt §H/§I)."""
    if not settings.enable_prometheus_metrics:
        raise HTTPException(404, "metrics disabled")
    return Response(content=render_latest_metrics(), media_type=METRICS_CONTENT_TYPE)


@app.get("/lineage/batches")
def lineage_batches(limit: int = 20) -> dict:
    return {"batches": list_batches(limit=limit)}


@app.get("/integrations/status")
def integrations_status() -> dict:
    return integration_status()


@app.get("/crm/customers")
def crm_list_customers() -> dict:
    """List CRM customers for asset-first Diagnosis Chat."""
    from integrations.crm_enrichment import list_crm_customers

    return {"customers": list_crm_customers()}


@app.get("/crm/customers/{customer_id}/assets")
def crm_customer_assets(customer_id: str) -> dict:
    """Registered appliances for a customer (product + warranty on each asset)."""
    from integrations.crm_enrichment import list_customer_assets

    data = list_customer_assets(customer_id)
    if not data.get("customer"):
        raise HTTPException(404, f"Customer not found: {customer_id}")
    return data


@app.get("/crm/assets/{asset_id}")
def crm_get_asset(asset_id: str) -> dict:
    from integrations.crm_enrichment import get_crm_asset

    data = get_crm_asset(asset_id)
    if not data:
        raise HTTPException(404, f"Asset not found: {asset_id}")
    return data


@app.get("/graph/ontology", response_model=GraphSubgraphResponse)
def graph_ontology() -> GraphSubgraphResponse:
    """ER-style ontology schema (node labels and relationship types)."""
    return GraphSubgraphResponse(**get_ontology_schema())


@app.get("/graph/product/{product_id}", response_model=GraphSubgraphResponse)
def graph_product(product_id: str) -> GraphSubgraphResponse:
    if not verify_connection():
        raise HTTPException(503, "Neo4j unavailable")
    data = get_product_subgraph(product_id)
    if not data["nodes"]:
        raise HTTPException(404, f"Product not found: {product_id}")
    return GraphSubgraphResponse(**data)


@app.get("/graph/diagnosis-subgraph", response_model=GraphSubgraphResponse)
def graph_diagnosis_subgraph(
    product_id: str,
    symptom_ids: str = "",
    failure_mode_id: str | None = None,
) -> GraphSubgraphResponse:
    if not verify_connection():
        raise HTTPException(503, "Neo4j unavailable")
    ids = [s.strip() for s in symptom_ids.split(",") if s.strip()]
    return GraphSubgraphResponse(**get_diagnosis_subgraph(product_id, symptom_ids=ids, failure_mode_id=failure_mode_id))


@app.get("/graph/rdf/schema")
def graph_rdf_schema() -> dict:
    """
    W3C OWL 2 TBox (schema-only) as Turtle + class/property inventory.

    RDF = triple data model; OWL = formal ontology vocabulary for this product domain.
    """
    from graph.rdf_ontology_export import (
        CLASSES,
        DATATYPE_PROPERTIES,
        OBJECT_PROPERTIES,
        WD,
        WD_ONTOLOGY,
        schema_only_turtle,
    )

    return {
        "standards": {
            "rdf": "https://www.w3.org/TR/rdf11-concepts/",
            "rdfs": "https://www.w3.org/TR/rdf-schema/",
            "owl2": "https://www.w3.org/TR/owl2-overview/",
        },
        "purposes": {
            "owl": "TBox — classes and properties (formal meaning of Product, Component, INDICATES, …).",
            "rdf": "ABox — instance facts as triples (this washer, this part, this edge).",
            "knowledge_graph": "Neo4j runtime property graph for GraphRAG + Explorer.",
        },
        "namespace": WD,
        "ontology_iri": WD_ONTOLOGY,
        "classes": [{"name": n, "comment": c} for n, c in CLASSES],
        "object_properties": [
            {"name": n, "domain": d, "range": r, "neo4j": neo, "comment": c} for n, d, r, c, neo in OBJECT_PROPERTIES
        ],
        "datatype_properties": [
            {"name": n, "domain": d, "range": r, "comment": c} for n, d, r, c in DATATYPE_PROPERTIES
        ],
        "turtle": schema_only_turtle(),
    }


@app.get("/graph/rdf/product/{product_id}")
def graph_rdf_product(product_id: str, include_schema: bool = True) -> dict:
    """Full product diagram as W3C Turtle (schema optional + product ABox)."""
    from graph.rdf_ontology_export import WD, product_full_turtle

    try:
        turtle = product_full_turtle(product_id, include_schema=include_schema)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {
        "product_id": product_id,
        "namespace": WD,
        "include_schema": include_schema,
        "turtle": turtle,
        "format": "text/turtle",
        "standards": {
            "rdf": "https://www.w3.org/TR/rdf11-concepts/",
            "owl2": "https://www.w3.org/TR/owl2-overview/",
        },
    }


@app.get("/graph/rdf/entity")
def graph_rdf_entity(
    label: str,
    entity_id: str,
    product_id: str | None = None,
) -> dict:
    """
    Complete OWL class definition + RDF instance triples for a Neo4j node
    (e.g. label=Component&entity_id=wm-c01). Used by Knowledge Explorer inspector.
    """
    from graph.rdf_ontology_export import describe_entity_rdf

    data = describe_entity_rdf(
        neo4j_label=label,
        entity_id=entity_id,
        product_id=product_id,
    )
    if not data.get("ok"):
        raise HTTPException(404, data.get("error") or "entity not found in ontology mapping")
    return data


@app.get("/claims")
def list_claims(limit: int = 50) -> dict:
    return {"claims": list_submitted_claims(limit=limit)}


@app.get("/claims/{claim_id}")
def claim_detail(claim_id: str) -> dict:
    claim = get_claim(claim_id)
    if not claim:
        raise HTTPException(404, f"Claim not found: {claim_id}")
    return claim


@app.post("/claims/submit")
def submit_claim(req: DiagnoseRequest) -> dict:
    if not verify_connection():
        raise HTTPException(503, "Neo4j unavailable")
    if not req.asset_id:
        raise HTTPException(400, "asset_id required for claim submission")

    crm = enrich_session_from_crm(customer_id=req.customer_id, asset_id=req.asset_id)
    product_id = req.product_id or crm.get("product_id")
    result = run_diagnosis(req.message, product_id=product_id, asset_id=req.asset_id)
    diagnosis = result.get("diagnosis") or {}

    claim = submit_claim_from_diagnosis(
        diagnosis=diagnosis,
        asset_id=req.asset_id,
        customer_id=crm.get("customer_id") or req.customer_id or "",
        user_message=req.message,
    )
    return {"claim": claim, "diagnosis": diagnosis}


@app.patch("/claims/{claim_id}/status")
def patch_claim_status(claim_id: str, status: ClaimStatus, agent_notes: str = "") -> dict:
    claim = update_claim_status(claim_id, status.value, agent_notes=agent_notes)
    if not claim:
        raise HTTPException(404, f"Claim not found: {claim_id}")
    return claim


@app.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(req: DiagnoseRequest) -> DiagnoseResponse:
    if not verify_connection():
        raise HTTPException(503, "Neo4j unavailable")

    # Admission control — bound concurrent graph diagnoses (process or Redis shared).
    slot = _diagnose_limiter.try_acquire()
    if slot is None:
        raise HTTPException(
            503,
            "too many concurrent diagnoses; retry shortly",
            headers={"Retry-After": "2"},
        )
    try:
        return _diagnose_inner(req)
    except ConcurrencyLimitExceeded:
        raise HTTPException(503, "too many concurrent diagnoses; retry shortly") from None
    finally:
        _diagnose_limiter.release(slot)


def _diagnose_inner(req: DiagnoseRequest) -> DiagnoseResponse:
    # Input guardrails (kickoff prompt §E): sanitise + block injection/jailbreak.
    try:
        message = guard_request(req.message, max_input_length=settings.max_input_length)
    except GuardrailViolation as violation:
        logger.warning("input guardrail blocked request: %s", violation.rule)
        raise HTTPException(400, f"input rejected: {violation.rule}") from violation

    crm = enrich_session_from_crm(customer_id=req.customer_id, asset_id=req.asset_id)
    # Asset-first: product comes from CRM asset when present; client product only for anonymous.
    product_id = req.product_id

    warranty: dict = {}
    if crm.get("enriched") and crm.get("warranty_status"):
        warranty = check_warranty_eligibility(crm)

    with span(
        "diagnosis.run",
        **{
            "diagnosis.product_id": (crm.get("product_id") or product_id or "auto"),
            "diagnosis.has_asset": bool(req.asset_id),
            "diagnosis.force_keep": bool(req.force_keep_context),
        },
    ) as current_span:
        outcome = run_full_diagnosis(
            message,
            product_id=product_id,
            asset_id=req.asset_id,
            crm_context=crm,
            warranty=warranty,
            force_keep_context=bool(req.force_keep_context),
        )

        if outcome.warranty_blocked:
            observe_diagnosis(0.0, escalated=False, reason="warranty_blocked")
            return DiagnoseResponse(
                response=outcome.response,
                crm_context=crm,
                warranty=outcome.warranty,
            )

        diagnosis = outcome.diagnosis
        provenance_trail = diagnosis.get("provenance_trail", [])
        confidence = float(diagnosis.get("confidence", 0.0) or 0.0)
        observe_diagnosis(
            confidence,
            escalated=bool(outcome.escalated),
            reason="low_confidence" if outcome.escalated else "none",
        )
        if current_span is not None:
            current_span.set_attribute("diagnosis.confidence", confidence)
            current_span.set_attribute("diagnosis.escalated", bool(outcome.escalated))

    graph_subgraph = diagnosis.get("graph_subgraph")
    if not graph_subgraph and diagnosis.get("product_id"):
        graph_subgraph = diagnosis_subgraph_from_result(diagnosis)

    # Output guardrails (kickoff prompt §E): cap length + redact PII in prose.
    guarded = validate_output(
        {"response": outcome.response},
        max_chars=settings.max_response_chars,
        redact_pii=settings.enable_pii_redaction,
    )

    return DiagnoseResponse(
        response=guarded["response"],
        diagnosis=diagnosis,
        escalated=outcome.escalated,
        case_id=outcome.case_id,
        crm_context=crm,
        warranty=warranty,
        provenance_trail=provenance_trail,
        graph_subgraph=graph_subgraph,
    )


# =============================================================================
# ADMIN MODULE — Enterprise Pipeline Control & Knowledge Base Onboarding
# =============================================================================
# Strategic design for enterprise tech landscape:
# - Staged pipeline: Fetch → Validate (smoke) → Review (human gate) → Promote
# - Dry-run / preview before any graph mutation
# - Approval required (simulates change control board)
# - Audit via lineage + simple admin log
# - Onboarding supports new products without breaking existing catalog
# - Complications addressed: data quality (smoke), rollback (re-run previous batch),
#   incremental vs full, visibility before production impact on live diagnosis.

ADMIN_REVIEW_STATE: dict = {
    "reviewed": False,
    "last_report": None,
    "last_smoke_ok": False,
    "change_preview": None,
    "journey": [],  # chronological onboarding log for Admin UI
    "last_promoted_at": None,
    "last_fetch_at": None,
    "ready_for_customer_test": False,
    # product_id -> selected bool (Admin change-set scope for materialize/promote)
    "product_selection": {},
    "ingest_plan": None,
    "last_sources_fingerprint": None,
    "materialize_done": False,
    "locked_selection_ids": [],
    "tbox_review_acknowledged": False,
}


def _admin_journey(
    step: str,
    action: str,
    summary: str,
    changes: dict | None = None,
    *,
    status: str = "ok",
) -> None:
    """Append guided-onboarding journey entry + durable audit line (survives restart)."""
    from graph.enterprise_pipeline.change_preview import journey_entry
    from utils.admin_audit import log_admin_event

    entry = journey_entry(step, action, summary, changes)
    log = list(ADMIN_REVIEW_STATE.get("journey") or [])
    log.append(entry)
    ADMIN_REVIEW_STATE["journey"] = log[-40:]
    # Audit must never break the control path
    with suppress(Exception):
        log_admin_event(
            step=step,
            action=action,
            summary=summary,
            changes=changes,
            status=status if status in ("ok", "error", "warn") else ("ok" if status != "failed" else "error"),
        )


def _refresh_change_preview(**kwargs) -> dict:
    """Rebuild change preview, applying persisted product selection."""
    from graph.enterprise_pipeline.change_preview import build_change_preview

    preview = build_change_preview(
        selection=ADMIN_REVIEW_STATE.get("product_selection") or {},
        include_pim_sources=True,
        **kwargs,
    )
    ADMIN_REVIEW_STATE["change_preview"] = preview
    # Keep selection map in sync with latest apply defaults
    if preview.get("product_selection"):
        ADMIN_REVIEW_STATE["product_selection"] = dict(preview["product_selection"])
    return preview


def _rebuild_ingest_plan() -> dict:
    """Detect diffs + recommend next actions; store on ADMIN_REVIEW_STATE."""
    from graph.enterprise_pipeline.ingest_plan import build_ingest_plan

    preview = ADMIN_REVIEW_STATE.get("change_preview")
    locked = list(ADMIN_REVIEW_STATE.get("locked_selection_ids") or [])
    selected = list((preview or {}).get("selected_product_ids") or [])
    if locked:
        selected = locked
    plan = build_ingest_plan(
        change_preview=preview,
        product_selection=ADMIN_REVIEW_STATE.get("product_selection") or {},
        selected_product_ids=selected,
        ontology_validation=ADMIN_REVIEW_STATE.get("ontology_validation"),
        smoke_ok=bool(ADMIN_REVIEW_STATE.get("last_smoke_ok")),
        human_reviewed=bool(ADMIN_REVIEW_STATE.get("reviewed")),
        last_sources_fingerprint=ADMIN_REVIEW_STATE.get("last_sources_fingerprint"),
        materialize_done=bool(ADMIN_REVIEW_STATE.get("materialize_done")),
        promote_done=bool(ADMIN_REVIEW_STATE.get("ready_for_customer_test")),
        fetch_done=bool(ADMIN_REVIEW_STATE.get("last_fetch_at") or ADMIN_REVIEW_STATE.get("last_report")),
        tbox_review_acknowledged=bool(ADMIN_REVIEW_STATE.get("tbox_review_acknowledged")),
    )
    # Update fingerprint baseline after plan (so next call can detect disk changes)
    fp = (plan.get("detected") or {}).get("sources_fingerprint") or {}
    if fp.get("fingerprint") and ADMIN_REVIEW_STATE.get("last_fetch_at"):
        # Only advance fingerprint when we have fetched; otherwise keep recommending fetch
        pass
    ADMIN_REVIEW_STATE["ingest_plan"] = plan
    return plan


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Guard for /admin/* routes.

    When `settings.admin_api_token` is set, every admin request must present a
    matching `X-Admin-Token` header. When it is empty (local demo default),
    access is open. This prevents unauthenticated graph mutation / file writes
    in any non-local deployment while keeping the local demo friction-free.
    """
    expected = settings.admin_api_token
    if not expected:
        return  # open access in local/demo mode
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")


@app.post("/admin/products/bulk-upsert", dependencies=[Depends(require_admin)])
def admin_bulk_upsert_products(payload: dict) -> dict:
    """
    Bulk add/update product ontology bundles in the enterprise catalog,
    optionally MERGE into Neo4j (staging or production).

    Body::
      {
        "products": [ { "product": {...}, "symptoms": [...], ... }, ... ],
        "promote_neo4j": true,
        "target_env": "staging",
        "dry_run": false
      }
    """
    from graph.enterprise_pipeline.product_ops import bulk_upsert_products

    products = payload.get("products") or []
    if not isinstance(products, list) or not products:
        raise HTTPException(400, "products[] required")
    return bulk_upsert_products(
        products,
        promote_neo4j=bool(payload.get("promote_neo4j", True)),
        target_env=str(payload.get("target_env") or "staging"),
        dry_run=bool(payload.get("dry_run", False)),
    )


@app.post("/admin/warranty/register-asset", dependencies=[Depends(require_admin)])
def admin_register_warranty_asset(payload: dict) -> dict:
    """
    Register a customer warranty purchase / installed unit (CRM + Neo4j Asset).

    Body: customer_id, asset_id, product_id, serial_number?, warranty_status?,
    warranty_expiry?, sku_id?, model_number?, promote_neo4j?, target_env?, dry_run?
    """
    from graph.enterprise_pipeline.product_ops import register_warranty_asset

    return register_warranty_asset(
        payload,
        promote_neo4j=bool(payload.get("promote_neo4j", True)),
        target_env=str(payload.get("target_env") or "production"),
        dry_run=bool(payload.get("dry_run", False)),
    )


@app.post("/admin/pipeline/dry-run-etl", dependencies=[Depends(require_admin)])
def admin_dry_run_etl() -> dict:
    """Stage 1: Fetch & transform without touching Neo4j. Returns preview + product change-set."""

    report = run_knowledge_etl(load_neo4j=False, dry_run=True)
    summaries = list(getattr(report, "product_summaries", None) or [])
    preview = _refresh_change_preview(
        incoming_products=summaries or None,
        source_label="dry_run_etl_fetch",
    )
    ADMIN_REVIEW_STATE["last_report"] = {
        "batch_id": report.batch_id,
        "sources": report.sources,
        "product_count": report.product_count,
        "errors": report.errors,
        "product_ids": [p.get("product_id") for p in summaries if p.get("product_id")],
    }
    ADMIN_REVIEW_STATE["last_fetch_at"] = preview.get("generated_at")
    ADMIN_REVIEW_STATE["reviewed"] = False  # new fetch invalidates prior approval
    ADMIN_REVIEW_STATE["ready_for_customer_test"] = False
    ADMIN_REVIEW_STATE["materialize_done"] = False
    # Reset validation when sources re-fetched
    ADMIN_REVIEW_STATE["ontology_validation"] = None
    ADMIN_REVIEW_STATE["tbox_review_acknowledged"] = False
    diff = preview.get("diff_vs_production") or {}
    summary = diff.get("summary") or {}
    sel = diff.get("selection_summary") or {}

    # Snapshot source fingerprint so later plans can detect disk changes
    from graph.enterprise_pipeline.ingest_plan import compute_sources_fingerprint

    fp = compute_sources_fingerprint()
    ADMIN_REVIEW_STATE["last_sources_fingerprint"] = fp.get("fingerprint")

    plan = _rebuild_ingest_plan()
    next_act = plan.get("next_action") or {}

    _admin_journey(
        "fetch",
        "dry_run_etl",
        preview.get("headline") or f"Fetched {report.product_count} products (dry-run)",
        {
            "batch_id": report.batch_id,
            "new_count": summary.get("new_count"),
            "updated_count": summary.get("updated_count"),
            "selected_total": sel.get("selected_total"),
            "product_count": report.product_count,
            "sources": {k: v.get("record_count") for k, v in (report.sources or {}).items()},
            "next_action": next_act.get("action_id"),
            "plan_headline": plan.get("headline"),
        },
    )
    return {
        "stage": "dry_run_etl",
        "batch_id": report.batch_id,
        "sources": report.sources,
        "product_count": report.product_count,
        "errors": report.errors,
        "product_summaries": summaries,
        "change_preview": preview,
        "product_selection": ADMIN_REVIEW_STATE.get("product_selection") or {},
        "ingest_plan": plan,
        "ui_result": {
            "title": "Fetch complete (dry-run — Neo4j not modified)",
            "headline": preview.get("headline"),
            "new_count": summary.get("new_count"),
            "updated_count": summary.get("updated_count"),
            "product_count": report.product_count,
            "sources": {k: v.get("record_count") for k, v in (report.sources or {}).items()},
            "plan_headline": plan.get("headline"),
            "next_step": next_act.get("title") or "Select products from recommended plan",
            "recommended_actions": [
                {"action_id": a.get("action_id"), "title": a.get("title"), "status": a.get("status")}
                for a in (plan.get("recommended_actions") or [])[:8]
            ],
        },
        "message": plan.get("headline")
        or preview.get("headline")
        or "Review recommended actions and select products to continue.",
    }


@app.get("/admin/pipeline/change-preview", dependencies=[Depends(require_admin)])
def admin_change_preview(refresh: bool = True, use_last_fetch: bool = False) -> dict:
    """
    What is coming vs live production graph.

    Default rebuild unions PIM sources + catalog so brand-new source products appear.
    Pass ``use_last_fetch=true`` to re-diff the last dry-run ETL product list only.
    Includes per-product selection (new vs update) for scoped promote.
    """
    if not refresh and ADMIN_REVIEW_STATE.get("change_preview"):
        plan = ADMIN_REVIEW_STATE.get("ingest_plan") or _rebuild_ingest_plan()
        return {
            "cached": True,
            "change_preview": ADMIN_REVIEW_STATE["change_preview"],
            "product_selection": ADMIN_REVIEW_STATE.get("product_selection") or {},
            "ingest_plan": plan,
            "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        }

    last = ADMIN_REVIEW_STATE.get("last_report") or {}
    incoming = None
    label = "pim_sources+catalog"
    cached_preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
    # Only reuse dry-run snapshot when explicitly requested (not on every refresh)
    if (
        use_last_fetch
        and cached_preview.get("incoming_products")
        and cached_preview.get("source_label") == "dry_run_etl_fetch"
    ):
        incoming = cached_preview["incoming_products"]
        label = "dry_run_etl_fetch"
    preview = _refresh_change_preview(
        incoming_products=incoming,
        source_label=label,
    )
    plan = _rebuild_ingest_plan()
    return {
        "cached": False,
        "change_preview": preview,
        "product_selection": ADMIN_REVIEW_STATE.get("product_selection") or {},
        "ingest_plan": plan,
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        "last_report": last,
    }


@app.get("/admin/pipeline/plan", dependencies=[Depends(require_admin)])
def admin_get_ingest_plan(refresh: bool = True) -> dict:
    """
    Recommended next actions after extract/diff.

    Detects new_product / product_update / tbox_extension / sources_changed and
    returns ordered recommended_actions + wizard_unlocks + fail-closed gates.
    """
    if refresh or not ADMIN_REVIEW_STATE.get("change_preview"):
        _refresh_change_preview()
    plan = _rebuild_ingest_plan()
    return {
        "ingest_plan": plan,
        "change_preview": ADMIN_REVIEW_STATE.get("change_preview"),
        "product_selection": ADMIN_REVIEW_STATE.get("product_selection") or {},
        "locked_selection_ids": ADMIN_REVIEW_STATE.get("locked_selection_ids") or [],
        "gates": plan.get("gates"),
        "next_action": plan.get("next_action"),
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
    }


@app.post("/admin/pipeline/plan/acknowledge-tbox", dependencies=[Depends(require_admin)])
def admin_acknowledge_tbox_review(payload: dict | None = None) -> dict:
    """Operator acknowledges TBox-extension candidates so ABox onboard can continue."""
    ADMIN_REVIEW_STATE["tbox_review_acknowledged"] = True
    plan = _rebuild_ingest_plan()
    _admin_journey(
        "tbox",
        "acknowledge_tbox_review",
        "TBox extension candidates acknowledged — ABox path may continue",
        {"next_action": (plan.get("next_action") or {}).get("action_id")},
    )
    return {
        "status": "ok",
        "tbox_review_acknowledged": True,
        "ingest_plan": plan,
        "message": "TBox review acknowledged. Proceed with product selection / ABox validation.",
    }


@app.post("/admin/pipeline/plan/lock-selection", dependencies=[Depends(require_admin)])
def admin_lock_selection(payload: dict) -> dict:
    """Lock product scope for subsequent materialize/promote (server-side)."""
    ids = payload.get("product_ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(400, "product_ids[] required")
    ids = [str(x) for x in ids if x]
    ADMIN_REVIEW_STATE["locked_selection_ids"] = ids
    # Sync selection map
    sel = dict(ADMIN_REVIEW_STATE.get("product_selection") or {})
    for k in list(sel.keys()):
        sel[k] = k in ids
    for pid in ids:
        sel[pid] = True
    ADMIN_REVIEW_STATE["product_selection"] = sel
    if ADMIN_REVIEW_STATE.get("change_preview"):
        from graph.enterprise_pipeline.change_preview import apply_product_selection

        ADMIN_REVIEW_STATE["change_preview"] = apply_product_selection(ADMIN_REVIEW_STATE["change_preview"], sel)
    plan = _rebuild_ingest_plan()
    _admin_journey(
        "select",
        "lock_selection",
        f"Locked {len(ids)} product(s) for KG scope",
        {"product_ids": ids, "next_action": (plan.get("next_action") or {}).get("action_id")},
    )
    return {
        "status": "ok",
        "locked_selection_ids": ids,
        "ingest_plan": plan,
        "change_preview": ADMIN_REVIEW_STATE.get("change_preview"),
        "message": f"Selection locked: {', '.join(ids[:12])}",
    }


@app.post("/admin/pipeline/selection", dependencies=[Depends(require_admin)])
def admin_set_product_selection(payload: dict) -> dict:
    """
    Select / deselect products from the change-set before materialize/promote.

    Body examples::

      {"product_id": "vac-001", "selected": true}
      {"selections": {"vac-001": true, "wm-001": false}}
      {"select_all_new": true}
      {"select_all_updated": false}
      {"select_all": false}
    """
    from graph.enterprise_pipeline.change_preview import apply_product_selection

    sel = dict(ADMIN_REVIEW_STATE.get("product_selection") or {})
    preview = ADMIN_REVIEW_STATE.get("change_preview")
    if not preview:
        preview = _refresh_change_preview()

    if "selections" in payload and isinstance(payload["selections"], dict):
        for k, v in payload["selections"].items():
            sel[str(k)] = bool(v)
    if "product_id" in payload:
        sel[str(payload["product_id"])] = bool(payload.get("selected", True))

    # Bulk helpers operate on current change lists
    diff = (preview or {}).get("diff_vs_production") or {}
    new_ids = [p.get("product_id") for p in (diff.get("new_products") or []) if p.get("product_id")]
    upd_ids = [p.get("product_id") for p in (diff.get("updated_products") or []) if p.get("product_id")]

    if "select_all" in payload:
        flag = bool(payload["select_all"])
        for pid in new_ids + upd_ids:
            sel[str(pid)] = flag
    if "select_all_new" in payload:
        flag = bool(payload["select_all_new"])
        for pid in new_ids:
            sel[str(pid)] = flag
    if "select_all_updated" in payload:
        flag = bool(payload["select_all_updated"])
        for pid in upd_ids:
            sel[str(pid)] = flag

    ADMIN_REVIEW_STATE["product_selection"] = sel
    preview = apply_product_selection(preview, sel)
    ADMIN_REVIEW_STATE["change_preview"] = preview
    # Keep locked ids in sync when operator checks boxes
    ADMIN_REVIEW_STATE["locked_selection_ids"] = list(preview.get("selected_product_ids") or [])
    plan = _rebuild_ingest_plan()
    sel_summary = (preview.get("diff_vs_production") or {}).get("selection_summary") or {}
    _admin_journey(
        "select",
        "product_selection",
        f"Selection updated: {sel_summary.get('selected_total', 0)} product(s) marked for KG "
        f"({sel_summary.get('selected_new_count', 0)} new, {sel_summary.get('selected_updated_count', 0)} updates)",
        {
            "selected_product_ids": sel_summary.get("selected_product_ids") or [],
            "selected_new_count": sel_summary.get("selected_new_count"),
            "selected_updated_count": sel_summary.get("selected_updated_count"),
            "next_action": (plan.get("next_action") or {}).get("action_id"),
        },
    )
    return {
        "status": "ok",
        "product_selection": sel,
        "change_preview": preview,
        "selected_product_ids": preview.get("selected_product_ids") or [],
        "selection_summary": sel_summary,
        "ingest_plan": plan,
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        "message": "Only selected products will be included on promote (when a selection is set).",
    }


@app.get("/admin/pipeline/selection", dependencies=[Depends(require_admin)])
def admin_get_product_selection() -> dict:
    preview = ADMIN_REVIEW_STATE.get("change_preview") or _refresh_change_preview()
    return {
        "product_selection": ADMIN_REVIEW_STATE.get("product_selection") or {},
        "selected_product_ids": preview.get("selected_product_ids") or [],
        "selection_summary": (preview.get("diff_vs_production") or {}).get("selection_summary"),
        "change_preview": preview,
    }


@app.get("/admin/ontology/tbox", dependencies=[Depends(require_admin)])
def admin_ontology_tbox() -> dict:
    """
    W3C-aligned TBox (rule book): OWL classes + properties used by this platform.

    Ontology is defined *before* product ABox instances are accepted into the KG.
    """
    from graph.enterprise_pipeline.ontology_validate import tbox_summary

    return {
        "stage": "tbox",
        "role": "Ontology / TBox — formal schema (rule book) before product RDF/ABox",
        **tbox_summary(),
    }


@app.post("/admin/ontology/validate-selection", dependencies=[Depends(require_admin)])
def admin_ontology_validate_selection(payload: dict | None = None) -> dict:
    """
    Validate selected (or all new) product ABox bundles against the TBox shapes.

    Rejects orphan links, missing INDICATES evidence, unknown list keys — so
    irrelevant / malformed data cannot pollute diagnosis accuracy.
    """
    from graph.enterprise_pipeline.ontology_validate import (
        load_pim_bundles,
        validate_catalog_products,
    )

    payload = payload or {}
    preview = ADMIN_REVIEW_STATE.get("change_preview") or _refresh_change_preview()
    selected = list(preview.get("selected_product_ids") or [])
    if payload.get("product_ids"):
        selected = [str(x) for x in payload["product_ids"]]
    if not selected and payload.get("all_new"):
        selected = [
            p.get("product_id")
            for p in ((preview.get("diff_vs_production") or {}).get("new_products") or [])
            if p.get("product_id")
        ]

    bundles = load_pim_bundles()
    # Also allow catalog if richer
    try:
        import json

        if settings.enterprise_catalog_file.exists():
            cat = json.loads(settings.enterprise_catalog_file.read_text(encoding="utf-8"))
            cat_products = cat.get("products") or []
            by_id = {}
            for b in bundles + [x for x in cat_products if isinstance(x, dict)]:
                core = b.get("product") if isinstance(b.get("product"), dict) else b
                pid = (core or {}).get("product_id")
                if pid:
                    by_id[str(pid)] = b
            bundles = list(by_id.values())
    except Exception:
        pass

    report = validate_catalog_products(
        bundles,
        product_ids=selected or None,
    )
    ADMIN_REVIEW_STATE["ontology_validation"] = report
    plan = _rebuild_ingest_plan()
    _admin_journey(
        "ontology",
        "validate_abox",
        report.get("headline") or "Ontology validation finished",
        {
            "passed_count": report.get("passed_count"),
            "failed_count": report.get("failed_count"),
            "passed_product_ids": report.get("passed_product_ids"),
            "failed_product_ids": report.get("failed_product_ids"),
            "next_action": (plan.get("next_action") or {}).get("action_id"),
        },
    )
    return {
        "stage": "ontology_validate",
        "selected_product_ids": selected,
        **report,
        "ingest_plan": plan,
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        "message": report.get("headline"),
    }


@app.post("/admin/pipeline/validate", dependencies=[Depends(require_admin)])
def admin_validate() -> dict:
    """Stage 2: Run smoke tests against current graph. Critical enterprise gate."""
    smoke = run_smoke_validation()
    ADMIN_REVIEW_STATE["last_smoke_ok"] = smoke.ok
    plan = _rebuild_ingest_plan()
    _admin_journey(
        "validate",
        "smoke_validation",
        f"Smoke {'passed' if smoke.ok else 'FAILED'} ({smoke.passed} ok / {smoke.failed} failed)",
        {
            "ok": smoke.ok,
            "passed": smoke.passed,
            "failed": smoke.failed,
            "next_action": (plan.get("next_action") or {}).get("action_id"),
        },
    )
    return {
        "stage": "smoke_validation",
        "ok": smoke.ok,
        "passed": smoke.passed,
        "failed": smoke.failed,
        "details": smoke.details[-20:],
        "ingest_plan": plan,
        "message": "All critical scenarios must pass before promotion."
        if not smoke.ok
        else "Smoke passed. Review the change-set, then Approve.",
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
    }


@app.get("/admin/pipeline/review", dependencies=[Depends(require_admin)])
def admin_review() -> dict:
    """Stage 3: Human review gate. Shows what is staged and requires explicit approval."""
    last = ADMIN_REVIEW_STATE.get("last_report") or {}
    smoke_ok = ADMIN_REVIEW_STATE.get("last_smoke_ok", False)
    preview = ADMIN_REVIEW_STATE.get("change_preview")
    return {
        "stage": "review",
        "staged_changes": last,
        "change_preview": preview,
        "smoke_passed": smoke_ok,
        "reviewed": ADMIN_REVIEW_STATE.get("reviewed", False),
        "recommendation": (
            "Review new/updated products below, then Approve before Promote. " "Models enterprise change control."
        ),
        "can_promote": smoke_ok and ADMIN_REVIEW_STATE.get("reviewed", False),
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        "ready_for_customer_test": ADMIN_REVIEW_STATE.get("ready_for_customer_test", False),
    }


@app.post("/admin/pipeline/approve-review", dependencies=[Depends(require_admin)])
def admin_approve_review() -> dict:
    """Admin explicitly approves the reviewed changes (enterprise gate)."""
    ADMIN_REVIEW_STATE["reviewed"] = True
    diff = (ADMIN_REVIEW_STATE.get("change_preview") or {}).get("diff_vs_production") or {}
    summary = diff.get("summary") or {}
    plan = _rebuild_ingest_plan()
    _admin_journey(
        "approve",
        "approve_review",
        "Human review approved — promote unlocked",
        {
            "new_count": summary.get("new_count"),
            "updated_count": summary.get("updated_count"),
            "next_action": (plan.get("next_action") or {}).get("action_id"),
        },
    )
    return {
        "status": "approved",
        "message": "Changes reviewed and approved. Promotion now allowed.",
        "ingest_plan": plan,
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
    }


@app.post("/admin/pipeline/promote", dependencies=[Depends(require_admin)])
def admin_promote() -> dict:
    """Stage 4: Promote validated data to the live knowledge graph (Neo4j).

    When Admin has set a product selection, only those product bundles are MERGEd.
    """
    from datetime import datetime

    from runtime.partitioning import product_id_from_record

    if not ADMIN_REVIEW_STATE.get("last_smoke_ok"):
        return {"error": "Smoke validation must pass before promotion."}
    if not ADMIN_REVIEW_STATE.get("reviewed"):
        return {"error": "Human review approval required. Call /admin/pipeline/approve-review first."}

    preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
    # Normalize selected ids via shared partition helper (same extraction as ETL)
    raw_selected = list(preview.get("selected_product_ids") or [])
    selected_ids = [str(pid) for pid in raw_selected if pid]
    # Also accept selection map entries that may only appear as product shells
    for pid, on in (ADMIN_REVIEW_STATE.get("product_selection") or {}).items():
        if on and str(pid) not in selected_ids:
            # product_id_from_record works on dict records; plain ids pass through as str
            normalized = product_id_from_record({"product_id": pid}) or str(pid)
            if normalized:
                selected_ids.append(str(normalized))

    has_actionable = bool(
        ((preview.get("diff_vs_production") or {}).get("summary") or {}).get("has_actionable_changes")
    )
    if has_actionable and selected_ids == []:
        # Distinguish "no selection state" vs "user deselected all"
        sel_map = ADMIN_REVIEW_STATE.get("product_selection") or {}
        if sel_map and not any(sel_map.values()):
            return {
                "error": "No products selected. Select at least one NEW or UPDATE product before promote.",
            }

    promo = run_staging_promotion(
        smoke_passed=True,
        product_ids=selected_ids or None,
    )
    ADMIN_REVIEW_STATE["reviewed"] = False  # reset gate after promote
    ADMIN_REVIEW_STATE["last_promoted_at"] = datetime.now(UTC).isoformat()
    ADMIN_REVIEW_STATE["ready_for_customer_test"] = bool(getattr(promo, "promoted", False))
    with suppress(Exception):
        _refresh_change_preview()
    _admin_journey(
        "promote",
        "promote_production",
        (
            f"Promoted {len(selected_ids)} selected product(s) to production Neo4j"
            if selected_ids
            else "Knowledge base promoted to production Neo4j — ready for customer persona tests"
        )
        if getattr(promo, "promoted", False)
        else "Promotion attempted",
        {
            "promoted": getattr(promo, "promoted", False),
            "batch_id": getattr(promo, "batch_id", None),
            "entity_counts": getattr(promo, "entity_counts", {}),
            "selected_product_ids": selected_ids,
            "product_ids_promoted": getattr(promo, "product_ids_promoted", None),
        },
    )
    return {
        "stage": "promotion",
        "promoted": promo.promoted,
        "batch_id": getattr(promo, "batch_id", None),
        "entity_counts": getattr(promo, "entity_counts", {}),
        "selected_product_ids": selected_ids,
        "product_ids_promoted": getattr(promo, "product_ids_promoted", None),
        "message": (
            f"Promoted selected products ({', '.join(selected_ids[:8])}{'…' if len(selected_ids) > 8 else ''}). "
            "Switch to Customer persona and run Diagnosis Chat."
            if selected_ids
            else "Knowledge base updated. Switch to Customer persona and run Diagnosis Chat."
        ),
        "ready_for_customer_test": ADMIN_REVIEW_STATE["ready_for_customer_test"],
        "change_preview": ADMIN_REVIEW_STATE.get("change_preview"),
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        "errors": getattr(promo, "errors", []),
    }


@app.post("/admin/onboard-product", dependencies=[Depends(require_admin)])
def admin_onboard_product(payload: dict) -> dict:
    """
    Strategic onboarding for new products.
    Accepts a minimal product definition and incorporates it into the enterprise catalog.
    In real enterprise this would go through schema validation, dedup, approval workflows.
    """
    from graph.enterprise_pipeline.change_preview import build_change_preview
    from runtime.partitioning import product_id_from_record

    required = ["product_id", "name"]
    if not all(k in payload for k in required):
        raise HTTPException(400, "product_id and name are required")

    catalog_path = settings.enterprise_catalog_file
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text())
    else:
        catalog = {"products": [], "symptoms": [], "failure_modes": [], "parts": []}

    # Prevent duplicates (handles both flat and nested product bundles)
    existing: set[str] = set()
    for p in catalog.get("products", []):
        if isinstance(p, dict):
            pid = p.get("product_id") or product_id_from_record(p)
            if pid:
                existing.add(str(pid))
    if payload["product_id"] in existing:
        return {"status": "duplicate", "message": "Product already exists in catalog."}

    # Minimal incorporation (extend as needed for full enterprise data)
    new_product = {
        "product_id": payload["product_id"],
        "name": payload["name"],
        "family": payload.get("family", "appliance"),
        "oem": payload.get("oem", "OEM-Demo"),
    }
    catalog.setdefault("products", []).append(new_product)

    # Optional: add symptoms / failure modes if provided
    if "symptoms" in payload:
        catalog.setdefault("symptoms", []).extend(payload["symptoms"])
    if "failure_modes" in payload:
        catalog.setdefault("failure_modes", []).extend(payload["failure_modes"])

    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    settings.data_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    with suppress(Exception):
        ADMIN_REVIEW_STATE["change_preview"] = build_change_preview(include_pim_sources=True)
    _admin_journey(
        "onboard",
        "onboard_product",
        f"Staged product {payload['product_id']} into catalog (not live until promote)",
        {"product_id": payload["product_id"], "name": payload.get("name")},
    )

    return {
        "status": "staged",
        "product_id": payload["product_id"],
        "message": "Product added to staging catalog. Run Fetch → review changes → Validate → Approve → Promote.",
        "catalog_products": len(catalog.get("products", [])),
        "change_preview": ADMIN_REVIEW_STATE.get("change_preview"),
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
    }


@app.get("/admin/pipeline/status", dependencies=[Depends(require_admin)])
def admin_pipeline_status() -> dict:
    """Current state of the knowledge base onboarding process."""
    from graph.enterprise_pipeline.change_preview import load_catalog_products

    catalog_products = 0
    catalog_summaries: list = []
    if settings.enterprise_catalog_file.exists():
        try:
            catalog = json.loads(settings.enterprise_catalog_file.read_text())
            catalog_products = len(catalog.get("products", []))
            catalog_summaries = load_catalog_products()
        except Exception:
            pass

    # Keep a fresh-enough preview when missing (cheap if Neo4j up)
    if not ADMIN_REVIEW_STATE.get("change_preview"):
        with suppress(Exception):
            _refresh_change_preview()

    preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
    if not preview:
        try:
            preview = _refresh_change_preview()
        except Exception:
            preview = {}
    plan = _rebuild_ingest_plan()
    diff = preview.get("diff_vs_production") or {}
    diff_summary = diff.get("summary") or {}
    sel_summary = diff.get("selection_summary") or {}

    return {
        "review_state": {
            "reviewed": ADMIN_REVIEW_STATE.get("reviewed", False),
            "last_smoke_ok": ADMIN_REVIEW_STATE.get("last_smoke_ok", False),
            "last_report": ADMIN_REVIEW_STATE.get("last_report"),
            "last_fetch_at": ADMIN_REVIEW_STATE.get("last_fetch_at"),
            "last_promoted_at": ADMIN_REVIEW_STATE.get("last_promoted_at"),
            "ready_for_customer_test": ADMIN_REVIEW_STATE.get("ready_for_customer_test", False),
            "materialize_done": ADMIN_REVIEW_STATE.get("materialize_done", False),
        },
        "catalog_stats": {
            "path": str(settings.enterprise_catalog_file),
            "exists": settings.enterprise_catalog_file.exists(),
            "products": catalog_products,
        },
        "lineage_last": list_batches(limit=3),
        "change_preview": preview,
        "product_selection": ADMIN_REVIEW_STATE.get("product_selection") or {},
        "selected_product_ids": preview.get("selected_product_ids") or [],
        "locked_selection_ids": ADMIN_REVIEW_STATE.get("locked_selection_ids") or [],
        "ingest_plan": plan,
        "journey": ADMIN_REVIEW_STATE.get("journey") or [],
        "onboarding_progress": {
            "fetched": bool(ADMIN_REVIEW_STATE.get("last_fetch_at") or ADMIN_REVIEW_STATE.get("last_report")),
            "has_actionable_changes": bool(diff_summary.get("has_actionable_changes")),
            "new_count": diff_summary.get("new_count", 0),
            "updated_count": diff_summary.get("updated_count", 0),
            "selected_total": sel_summary.get("selected_total", 0),
            "selected_new_count": sel_summary.get("selected_new_count", 0),
            "selected_updated_count": sel_summary.get("selected_updated_count", 0),
            "smoke_passed": bool(ADMIN_REVIEW_STATE.get("last_smoke_ok")),
            "reviewed": bool(ADMIN_REVIEW_STATE.get("reviewed")),
            "ready_for_customer_test": bool(ADMIN_REVIEW_STATE.get("ready_for_customer_test")),
            "materialize_done": bool(ADMIN_REVIEW_STATE.get("materialize_done")),
            "next_action": (plan.get("next_action") or {}).get("action_id"),
            "catalog_product_ids": [p.get("product_id") for p in catalog_summaries],
        },
    }


# ----- Multi-source KG ingestion control plane (structured / semi / unstructured) -----


@app.get("/admin/pipeline/entity-delta", dependencies=[Depends(require_admin)])
def admin_entity_delta(
    product_ids: str | None = None,
    compare_env: str = "production",
) -> dict:
    """Entity-level ABox delta for selected products (catalog vs Neo4j).

    Shows NEW symptoms / failure modes / diagnostic steps / parts — not just
    product-count UPDATE. Also reports whether entities are fully loaded on
    staging vs production (Docker Neo4j ports).
    """
    from graph.enterprise_pipeline.entity_delta import build_selection_entity_deltas

    ids: list[str] = []
    if product_ids:
        ids = [p.strip() for p in product_ids.split(",") if p.strip()]
    if not ids:
        ids = list(ADMIN_REVIEW_STATE.get("locked_selection_ids") or [])
    if not ids:
        preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
        ids = list(preview.get("selected_product_ids") or [])
    if not ids:
        sel = ADMIN_REVIEW_STATE.get("product_selection") or {}
        ids = [str(k) for k, v in sel.items() if v]

    env = compare_env if compare_env in ("production", "staging") else "production"
    bundle = build_selection_entity_deltas(ids, compare_env=env)
    # Attach field_changes from change_preview when available
    preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
    diff = preview.get("diff_vs_production") or {}
    field_by_id = {}
    for row in list(diff.get("updated_products") or []) + list(diff.get("new_products") or []):
        pid = row.get("product_id")
        if pid:
            field_by_id[str(pid)] = {
                "field_changes": row.get("field_changes") or [],
                "reason": row.get("reason"),
                "live": row.get("live"),
                "badge": row.get("badge"),
            }
    for p in bundle.get("products") or []:
        extra = field_by_id.get(str(p.get("product_id")))
        if extra:
            p["field_changes"] = extra["field_changes"]
            p["diff_reason"] = extra["reason"]
            p["live_summary"] = extra.get("live")
    return bundle


@app.get("/admin/pipeline/neo4j-verify", dependencies=[Depends(require_admin)])
def admin_neo4j_verify(product_ids: str | None = None) -> dict:
    """Post-promote check: are selection entities present in staging + production Neo4j?"""
    from config.settings import settings as _settings
    from graph.enterprise_pipeline.entity_delta import build_selection_entity_deltas
    from graph.neo4j_client import verify_connection

    ids: list[str] = []
    if product_ids:
        ids = [p.strip() for p in product_ids.split(",") if p.strip()]
    if not ids:
        ids = list(ADMIN_REVIEW_STATE.get("locked_selection_ids") or [])
    if not ids:
        preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
        ids = list(preview.get("selected_product_ids") or [])

    bundle = build_selection_entity_deltas(ids, compare_env="production")
    return {
        "product_ids": ids,
        "connectivity": {
            "production": {
                "uri": _settings.neo4j_uri,
                "connected": bool(verify_connection("production")),
            },
            "staging": {
                "uri": _settings.neo4j_staging_uri,
                "connected": bool(verify_connection("staging")),
            },
        },
        "summary": bundle.get("summary"),
        "products": [
            {
                "product_id": p.get("product_id"),
                "headline": p.get("headline"),
                "change_kind": p.get("change_kind"),
                "count_matrix": p.get("count_matrix"),
                "production": (p.get("neo4j") or {}).get("production"),
                "staging": (p.get("neo4j") or {}).get("staging"),
                "human_summary": (p.get("human_summary") or [])[:12],
            }
            for p in (bundle.get("products") or [])
        ],
        "ready_for_diagnosis_chat": bool((bundle.get("summary") or {}).get("all_fully_loaded_production")),
        "note": (
            "Diagnosis Chat reads production Neo4j only. "
            "Staging success does not affect customer chat until production promote."
        ),
    }


@app.get("/admin/audit/history", dependencies=[Depends(require_admin)])
def admin_audit_history(limit: int = 40) -> dict:
    """Durable + session audit for Admin onboarding (JSONL + pipeline runs + ETL batches).

    Complements the in-memory journey (lost on API restart) with append-only files under
    data/lineage/.
    """
    from utils.admin_audit import build_audit_bundle

    limit = max(1, min(int(limit or 40), 200))
    bundle = build_audit_bundle(limit=limit)
    bundle["session_journey"] = list(ADMIN_REVIEW_STATE.get("journey") or [])
    bundle["review_state"] = {
        "reviewed": bool(ADMIN_REVIEW_STATE.get("reviewed")),
        "last_smoke_ok": bool(ADMIN_REVIEW_STATE.get("last_smoke_ok")),
        "materialize_done": bool(ADMIN_REVIEW_STATE.get("materialize_done")),
        "ready_for_customer_test": bool(ADMIN_REVIEW_STATE.get("ready_for_customer_test")),
        "last_fetch_at": ADMIN_REVIEW_STATE.get("last_fetch_at"),
        "last_promoted_at": ADMIN_REVIEW_STATE.get("last_promoted_at"),
        "locked_selection_ids": list(ADMIN_REVIEW_STATE.get("locked_selection_ids") or []),
    }
    return bundle


@app.get("/admin/kg-pipelines", dependencies=[Depends(require_admin)])
def admin_list_kg_pipelines() -> dict:
    """Catalog of multi-source knowledge graph ingestion pipelines."""
    from graph.enterprise_pipeline.control_plane import list_pipelines

    return {
        "pipelines": [p.to_dict() for p in list_pipelines()],
        "modes": ["bootstrap", "incremental", "on_demand"],
        "source_kinds": ["structured", "semi_structured", "unstructured", "mixed", "internal"],
        "docs": "docs/20-Enterprise-KG-Ingestion-Pipeline-Architecture.md",
    }


@app.get("/admin/kg-pipelines/runs", dependencies=[Depends(require_admin)])
def admin_list_kg_pipeline_runs(limit: int = 30) -> dict:
    from graph.enterprise_pipeline.control_plane import list_runs

    return {"runs": list_runs(limit=limit)}


@app.get("/admin/kg-pipelines/runs/{run_id}", dependencies=[Depends(require_admin)])
def admin_get_kg_pipeline_run(run_id: str) -> dict:
    from graph.enterprise_pipeline.control_plane import get_run

    data = get_run(run_id)
    if not data:
        raise HTTPException(404, f"Run not found: {run_id}")
    return data


def _kg_safe_data_path(rel: str) -> Path:
    """Resolve a path under project data/ for admin preview (no path escape)."""
    root = (settings.project_root / "data").resolve()
    raw = (rel or "").strip().lstrip("/")
    if raw.startswith("data/"):
        raw = raw[len("data/") :]
    candidate = (root / raw).resolve()
    if not str(candidate).startswith(str(root)):
        raise HTTPException(400, "path must be under data/")
    # Only allow known source/staging/enterprise fixture trees
    allowed_prefixes = (
        root / "pipeline_sources",
        root / "pipeline_staging",
        root / "enterprise_sources",
    )
    if not any(str(candidate).startswith(str(p.resolve())) or candidate == p.resolve() for p in allowed_prefixes):
        raise HTTPException(400, "path not in pipeline_sources, pipeline_staging, or enterprise_sources")
    return candidate


def _preview_source_file(path: Path, max_chars: int = 2500) -> dict:
    """Lightweight pre-run inventory for one source file (no pipeline execution)."""
    rel = str(path.relative_to(settings.project_root))
    kind = "other"
    mode = "unknown"
    parts = path.parts
    if "semi_structured" in parts:
        kind = "semi_structured"
    elif "unstructured" in parts:
        kind = "unstructured"
    elif "structured" in parts or "enterprise_sources" in parts:
        kind = "structured"
    if "bootstrap" in parts:
        mode = "bootstrap"
    elif "incremental" in parts:
        mode = "incremental"

    text = ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"path": rel, "error": str(exc)}

    preview = text[:max_chars]
    truncated = len(text) > max_chars
    summary: dict = {
        "path": rel,
        "name": path.name,
        "bytes": path.stat().st_size,
        "kind": kind,
        "mode_folder": mode,
        "suffix": path.suffix.lower(),
        "preview": preview,
        "truncated": truncated,
        "line_count": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
    }

    # Schema-on-read samples so Admin can show inventory *before* pipelines run
    samples: list = []
    product_ids: set[str] = set()
    error_codes: set[str] = set()
    if path.suffix.lower() == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                if row.get("product_id"):
                    product_ids.add(str(row["product_id"]))
                if len(samples) < 5:
                    samples.append(row)
        summary["record_count"] = len([ln for ln in text.splitlines() if ln.strip()])
        summary["samples"] = samples
        summary["product_ids"] = sorted(product_ids)
    elif path.suffix.lower() == ".csv":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        header = lines[0].split(",") if lines else []
        summary["headers"] = header
        summary["record_count"] = max(0, len(lines) - 1)
        for ln in lines[1:6]:
            cols = ln.split(",")
            row = dict(zip(header, cols, strict=False)) if header else {"raw": ln}
            samples.append(row)
            if "product_id" in row and row["product_id"]:
                product_ids.add(row["product_id"])
        summary["samples"] = samples
        summary["product_ids"] = sorted(product_ids)
    elif path.suffix.lower() in (".txt", ".md"):
        import re

        for m in re.findall(r"\bE\d{2,3}\b", text, flags=re.I):
            error_codes.add(m.upper())
        for m in re.findall(r"\b((?:wm|dw|mw|rf|ov)-\d{3})\b", text, flags=re.I):
            product_ids.add(m.lower())
        for m in re.findall(r"((?:wm|dw|mw|rf|ov)-\d{3})", path.stem, flags=re.I):
            product_ids.add(m.lower())
        summary["error_codes_guess"] = sorted(error_codes)[:12]
        summary["product_ids"] = sorted(product_ids)
        summary["record_count"] = 1
    elif path.suffix.lower() == ".json":
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                summary["record_count"] = len(parsed)
                summary["samples"] = parsed[:3]
            elif isinstance(parsed, dict):
                # common fixture shapes
                for key in ("products", "records", "items", "assets", "claims"):
                    if isinstance(parsed.get(key), list):
                        summary["record_count"] = len(parsed[key])
                        summary["samples"] = parsed[key][:3]
                        break
                else:
                    summary["record_count"] = 1
            else:
                summary["record_count"] = 1
        except json.JSONDecodeError:
            summary["record_count"] = 0
    else:
        summary["record_count"] = 0

    return summary


@app.get("/admin/kg-pipelines/artifacts", dependencies=[Depends(require_admin)])
def admin_list_kg_pipeline_artifacts() -> dict:
    """List fixture source packs and staging artifacts for the Control Room."""
    root = settings.project_root / "data"
    sources = root / "pipeline_sources"
    staging = root / "pipeline_staging"
    enterprise = root / "enterprise_sources"

    def _list_files(base, limit: int = 40) -> list[dict]:
        if not base.exists():
            return []
        files = []
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.name != ".gitkeep":
                files.append(
                    {
                        "path": str(p.relative_to(settings.project_root)),
                        "bytes": p.stat().st_size,
                        "name": p.name,
                    }
                )
            if len(files) >= limit:
                break
        return files

    return {
        "source_packs": _list_files(sources),
        "staging_artifacts": _list_files(staging),
        "enterprise_sources": _list_files(enterprise, limit=20),
        "roots": {
            "sources": str(sources),
            "staging": str(staging),
            "enterprise_sources": str(enterprise),
            "how_to_add": {
                "semi_structured_bootstrap": "data/pipeline_sources/semi_structured/bootstrap/*.csv|*.jsonl",
                "semi_structured_incremental": "data/pipeline_sources/semi_structured/incremental/*.csv|*.jsonl",
                "unstructured_bootstrap": "data/pipeline_sources/unstructured/bootstrap/*.txt|*.md",
                "structured": "PIM/CRM/FSM/Claims via connectors or data/enterprise_sources fixtures",
            },
        },
    }


@app.get("/admin/kg-pipelines/sources/inventory", dependencies=[Depends(require_admin)])
def admin_kg_sources_inventory(mode: str = "bootstrap") -> dict:
    """
    Pre-run source inventory: list files + parse samples *without* running pipelines.

    Use this in Admin so operators see what will be extracted before clicking Run.
    mode: bootstrap | incremental | all
    """
    sources_root = settings.project_root / "data" / "pipeline_sources"
    enterprise_root = settings.project_root / "data" / "enterprise_sources"
    mode = (mode or "bootstrap").lower()
    if mode not in ("bootstrap", "incremental", "all", "on_demand"):
        mode = "all"

    files: list[Path] = []
    if sources_root.exists():
        for p in sorted(sources_root.rglob("*")):
            if not p.is_file() or p.name in (".gitkeep", "README.md"):
                continue
            parts = set(p.parts)
            in_bootstrap = "bootstrap" in parts
            in_incremental = "incremental" in parts
            if mode == "bootstrap":
                # Full-build packs + files not under incremental/
                if in_incremental and not in_bootstrap:
                    continue
            elif mode == "incremental" and not in_incremental:
                # Live deltas only (semi incremental folder)
                continue
            # mode all | on_demand → every pack
            files.append(p)
    if enterprise_root.exists() and mode in ("bootstrap", "all", "on_demand"):
        for p in sorted(enterprise_root.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".json", ".jsonl", ".csv", ".txt", ".md"):
                files.append(p)

    previews = [_preview_source_file(p) for p in files[:60]]
    by_kind: dict[str, list] = {}
    all_products: set[str] = set()
    total_records = 0
    for item in previews:
        k = item.get("kind") or "other"
        by_kind.setdefault(k, []).append(item)
        for pid in item.get("product_ids") or []:
            all_products.add(pid)
        total_records += int(item.get("record_count") or 0)

    return {
        "mode_filter": mode,
        "file_count": len(previews),
        "total_records_estimate": total_records,
        "product_ids_seen": sorted(all_products),
        "by_kind": by_kind,
        "files": previews,
        "roots": {
            "pipeline_sources": str(sources_root),
            "enterprise_sources": str(enterprise_root),
        },
        "how_to_add_files": [
            "1. Drop CSV/JSONL into data/pipeline_sources/semi_structured/bootstrap/ (full build) or .../incremental/ (deltas).",
            "2. Drop manuals/tickets as .txt or .md into data/pipeline_sources/unstructured/bootstrap/.",
            "3. Structured PIM/CRM data comes from live APIs when configured, else data/enterprise_sources fixtures.",
            "4. Click Refresh inventory here — samples appear before any pipeline run.",
            "5. Run semi_structured_ingest / unstructured_extract (or bootstrap_all) to materialize staging JSON.",
            "6. Promote graph only after smoke + review to load Neo4j.",
        ],
    }


@app.get("/admin/kg-pipelines/sources/preview", dependencies=[Depends(require_admin)])
def admin_kg_source_preview(path: str, max_chars: int = 4000) -> dict:
    """Preview a single source or staging artifact file (path relative to project or data/)."""
    if max_chars < 200:
        max_chars = 200
    if max_chars > 20000:
        max_chars = 20000
    p = _kg_safe_data_path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(404, f"file not found: {path}")
    return _preview_source_file(p, max_chars=max_chars)


@app.post("/admin/kg-pipelines/{pipeline_id}/run", dependencies=[Depends(require_admin)])
def admin_run_kg_pipeline(
    pipeline_id: str,
    mode: str = "on_demand",
    dry_run: bool = False,
    target_env: str = "staging",
    product_ids: str | None = None,
    use_selection: bool = True,
) -> dict:
    """
    Run a KG ingestion pipeline.

    mode: bootstrap | incremental | on_demand
    dry_run: preview without writing catalog/graph where supported
    target_env: staging | production (promote_graph)
    product_ids: optional comma-separated filter (overrides Admin selection when set)
    use_selection: when true (default), apply Admin change-set selection to
      materialize / promote / bootstrap so only checked products are processed
    """
    from graph.enterprise_pipeline.control_plane import run_pipeline

    selected: list[str] | None = None
    if product_ids:
        selected = [p.strip() for p in product_ids.split(",") if p.strip()]
    elif use_selection:
        # Prefer locked selection, then preview checkboxes
        selected = list(ADMIN_REVIEW_STATE.get("locked_selection_ids") or [])
        if not selected:
            preview = ADMIN_REVIEW_STATE.get("change_preview") or {}
            selected = list(preview.get("selected_product_ids") or [])
        if not selected:
            sel_map = ADMIN_REVIEW_STATE.get("product_selection") or {}
            selected = [str(k) for k, v in sel_map.items() if v]
        # Empty selection with use_selection: for materialize/promote/bootstrap require explicit picks
        if not selected and pipeline_id in (
            "bootstrap_all",
            "incremental_sync",
            "knowledge_materialize",
            "promote_graph",
        ):
            return {
                "run_id": None,
                "pipeline_id": pipeline_id,
                "status": "failed",
                "errors": [
                    "No products selected. Follow ingest plan: select NEW/UPDATE products, "
                    "validate ABox, then materialize/promote selection only."
                ],
                "stages": [],
                "ingest_plan": ADMIN_REVIEW_STATE.get("ingest_plan") or _rebuild_ingest_plan(),
                "message": "Blocked: empty product selection",
            }
        if not selected:
            selected = None

    # Fail-closed: materialize requires plan gate (validate ABox passed)
    if pipeline_id in ("knowledge_materialize", "bootstrap_all", "incremental_sync") and not dry_run:
        plan = _rebuild_ingest_plan()
        gates = plan.get("gates") or {}
        if not gates.get("allow_materialize"):
            return {
                "run_id": None,
                "pipeline_id": pipeline_id,
                "status": "failed",
                "errors": [
                    gates.get("block_reason") or "Ingest plan blocks materialize — complete recommended checks first."
                ],
                "stages": [],
                "ingest_plan": plan,
                "message": "Blocked by ingest plan",
            }

    report = run_pipeline(
        pipeline_id,
        mode=mode,
        dry_run=dry_run,
        target_env=target_env,
        product_ids=selected,
    )

    # Sync classic review gates + onboarding journey after control-plane runs
    if pipeline_id in ("smoke_validate", "bootstrap_all"):
        smoke_stage = next((s for s in report.stages if "smoke" in (s.name or "").lower()), None)
        if smoke_stage is not None:
            ADMIN_REVIEW_STATE["last_smoke_ok"] = smoke_stage.status.value == "success"

    if pipeline_id in ("bootstrap_all", "incremental_sync", "knowledge_materialize", "structured_extract"):
        try:
            from graph.enterprise_pipeline.change_preview import build_change_preview

            ADMIN_REVIEW_STATE["change_preview"] = build_change_preview(include_pim_sources=True)
            ADMIN_REVIEW_STATE["last_fetch_at"] = ADMIN_REVIEW_STATE["change_preview"].get("generated_at")
            if not dry_run and pipeline_id in ("bootstrap_all", "incremental_sync", "knowledge_materialize"):
                ADMIN_REVIEW_STATE["reviewed"] = False
                ADMIN_REVIEW_STATE["ready_for_customer_test"] = False
                if report.status.value in ("success", "partial") and pipeline_id in (
                    "knowledge_materialize",
                    "bootstrap_all",
                    "incremental_sync",
                ):
                    ADMIN_REVIEW_STATE["materialize_done"] = True
            headline = (ADMIN_REVIEW_STATE["change_preview"] or {}).get("headline") or pipeline_id
            _admin_journey(
                "ingest" if pipeline_id != "structured_extract" else "fetch",
                pipeline_id,
                f"{pipeline_id} · {report.status.value}. {headline}" + (f" · scope={selected}" if selected else ""),
                {
                    "run_id": report.run_id,
                    "status": report.status.value,
                    "dry_run": dry_run,
                    "product_ids": selected,
                },
            )
        except Exception:
            _admin_journey(
                "ingest",
                pipeline_id,
                f"{pipeline_id}: {report.status.value}",
                {"run_id": report.run_id},
            )
    elif pipeline_id == "smoke_validate":
        ok = bool(ADMIN_REVIEW_STATE.get("last_smoke_ok"))
        _admin_journey(
            "validate",
            "smoke_validate",
            f"Smoke {'passed' if ok else 'FAILED'} · {report.status.value}",
            {"run_id": report.run_id, "ok": ok},
        )
    elif pipeline_id == "promote_graph":
        if report.status.value == "success" and not dry_run:
            if target_env == "production":
                ADMIN_REVIEW_STATE["ready_for_customer_test"] = True
            try:
                from graph.enterprise_pipeline.change_preview import build_change_preview

                ADMIN_REVIEW_STATE["change_preview"] = build_change_preview(include_pim_sources=True)
            except Exception:
                pass
        _admin_journey(
            "promote",
            f"promote_graph:{target_env}",
            f"Promote graph → {target_env}: {report.status.value}",
            {"run_id": report.run_id, "target_env": target_env, "dry_run": dry_run},
        )
    else:
        _admin_journey(
            "pipeline",
            pipeline_id,
            f"{pipeline_id}: {report.status.value}",
            {"run_id": report.run_id, "mode": mode, "dry_run": dry_run},
        )

    plan = _rebuild_ingest_plan()
    out = report.to_dict()
    out["change_preview"] = ADMIN_REVIEW_STATE.get("change_preview")
    out["journey"] = ADMIN_REVIEW_STATE.get("journey") or []
    out["ready_for_customer_test"] = ADMIN_REVIEW_STATE.get("ready_for_customer_test", False)
    out["product_ids_filter"] = selected
    out["ingest_plan"] = plan
    out["message"] = (
        f"{pipeline_id}: {report.status.value}"
        + (f" · products={selected}" if selected else "")
        + (f" · dry_run={dry_run}" if dry_run else "")
    )
    return out


@app.get("/products")
def get_products():
    """List available products for UI selectors. Fetches real products from the knowledge graph."""
    try:
        products = list_all_products() or []
        if not products:
            # Fallback with more known products from the system
            products = [
                {"product_id": "wm-001", "name": "Front Load Washing Machine 8kg"},
                {"product_id": "dw-001", "name": "Built-in Dishwasher 12 Place Setting"},
                {"product_id": "mw-001", "name": "Convection Microwave 25L"},
                {"product_id": "oem-sam-wf45", "name": "Samsung WF45T6000AW Front Load Washer"},
                {"product_id": "oem-lg-wm4000", "name": "LG WM4000HWA Front Load Washer"},
            ]
        return {"products": products}
    except Exception:
        # Comprehensive fallback
        return {
            "products": [
                {"product_id": "wm-001", "name": "Front Load Washing Machine 8kg"},
                {"product_id": "dw-001", "name": "Built-in Dishwasher 12 Place Setting"},
                {"product_id": "mw-001", "name": "Convection Microwave 25L"},
                {"product_id": "oem-sam-wf45", "name": "Samsung WF45T6000AW Front Load Washer"},
                {"product_id": "oem-lg-wm4000", "name": "LG WM4000HWA Front Load Washer"},
            ]
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=False)
