"""
Diagnostics REST API
====================
Enterprise-grade demo API wrapping LangGraph diagnosis with CRM enrichment.

Run: python -m api.main
     uvicorn api.main:app --port 8080
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from graph.neo4j_client import close_driver, verify_connection
from integrations.claims_workflow import (
    get_claim,
    list_submitted_claims,
    submit_claim_from_diagnosis,
    update_claim_status,
)
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility
from services.diagnosis_service import run_full_diagnosis
from utils.connector_status import integration_status
from utils.lineage_store import list_batches

logger = logging.getLogger("diagnostics.api")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Application lifespan: close the shared Neo4j driver on shutdown."""
    yield
    close_driver()


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


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a controlled 500 instead of leaking stack traces to clients."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "neo4j": verify_connection(),
        "demo_mode": settings.demo_mode,
        "provenance_enabled": settings.enable_provenance,
    }


@app.get("/lineage/batches")
def lineage_batches(limit: int = 20) -> dict:
    return {"batches": list_batches(limit=limit)}


@app.get("/integrations/status")
def integrations_status() -> dict:
    return integration_status()


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

    crm = enrich_session_from_crm(customer_id=req.customer_id, asset_id=req.asset_id)
    product_id = req.product_id or crm.get("product_id")

    warranty: dict = {}
    if crm.get("enriched") and crm.get("warranty_status"):
        warranty = check_warranty_eligibility(crm)

    outcome = run_full_diagnosis(
        req.message,
        product_id=product_id,
        asset_id=req.asset_id,
        crm_context=crm,
        warranty=warranty,
    )

    if outcome.warranty_blocked:
        return DiagnoseResponse(
            response=outcome.response,
            crm_context=crm,
            warranty=outcome.warranty,
        )

    diagnosis = outcome.diagnosis
    provenance_trail = diagnosis.get("provenance_trail", [])

    graph_subgraph = diagnosis.get("graph_subgraph")
    if not graph_subgraph and diagnosis.get("product_id"):
        graph_subgraph = diagnosis_subgraph_from_result(diagnosis)

    return DiagnoseResponse(
        response=outcome.response,
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

ADMIN_REVIEW_STATE: dict = {"reviewed": False, "last_report": None, "last_smoke_ok": False}


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


@app.post("/admin/pipeline/dry-run-etl", dependencies=[Depends(require_admin)])
def admin_dry_run_etl() -> dict:
    """Stage 1: Fetch & transform without touching Neo4j. Returns preview report."""
    report = run_knowledge_etl(load_neo4j=False, dry_run=True)
    ADMIN_REVIEW_STATE["last_report"] = {
        "batch_id": report.batch_id,
        "sources": report.sources,
        "product_count": report.product_count,
        "errors": report.errors,
    }
    return {
        "stage": "dry_run_etl",
        "batch_id": report.batch_id,
        "sources": report.sources,
        "product_count": report.product_count,
        "errors": report.errors,
        "message": "Review the source counts and errors before proceeding to validation.",
    }


@app.post("/admin/pipeline/validate", dependencies=[Depends(require_admin)])
def admin_validate() -> dict:
    """Stage 2: Run smoke tests against current graph. Critical enterprise gate."""
    smoke = run_smoke_validation()
    ADMIN_REVIEW_STATE["last_smoke_ok"] = smoke.ok
    return {
        "stage": "smoke_validation",
        "ok": smoke.ok,
        "passed": smoke.passed,
        "failed": smoke.failed,
        "details": smoke.details[-20:],
        "message": "All critical scenarios must pass before promotion."
        if not smoke.ok
        else "Smoke passed. Ready for human review.",
    }


@app.get("/admin/pipeline/review", dependencies=[Depends(require_admin)])
def admin_review() -> dict:
    """Stage 3: Human review gate. Shows what is staged and requires explicit approval."""
    last = ADMIN_REVIEW_STATE.get("last_report") or {}
    smoke_ok = ADMIN_REVIEW_STATE.get("last_smoke_ok", False)
    return {
        "stage": "review",
        "staged_changes": last,
        "smoke_passed": smoke_ok,
        "reviewed": ADMIN_REVIEW_STATE.get("reviewed", False),
        "recommendation": "Review source counts, entity impact, and test results. Check 'Reviewed' before promoting.",
        "can_promote": smoke_ok and ADMIN_REVIEW_STATE.get("reviewed", False),
    }


@app.post("/admin/pipeline/approve-review", dependencies=[Depends(require_admin)])
def admin_approve_review() -> dict:
    """Admin explicitly approves the reviewed changes (enterprise gate)."""
    ADMIN_REVIEW_STATE["reviewed"] = True
    return {"status": "approved", "message": "Changes reviewed and approved. Promotion now allowed."}


@app.post("/admin/pipeline/promote", dependencies=[Depends(require_admin)])
def admin_promote() -> dict:
    """Stage 4: Promote validated data to the live knowledge graph (Neo4j)."""
    if not ADMIN_REVIEW_STATE.get("last_smoke_ok"):
        return {"error": "Smoke validation must pass before promotion."}
    if not ADMIN_REVIEW_STATE.get("reviewed"):
        return {"error": "Human review approval required. Call /admin/pipeline/approve-review first."}

    promo = run_staging_promotion(smoke_passed=True)
    ADMIN_REVIEW_STATE["reviewed"] = False  # reset gate after promote
    return {
        "stage": "promotion",
        "promoted": promo.promoted,
        "batch_id": getattr(promo, "batch_id", None),
        "entity_counts": getattr(promo, "entity_counts", {}),
        "message": "Knowledge base updated. New products and data are now live for diagnosis.",
    }


@app.post("/admin/onboard-product", dependencies=[Depends(require_admin)])
def admin_onboard_product(payload: dict) -> dict:
    """
    Strategic onboarding for new products.
    Accepts a minimal product definition and incorporates it into the enterprise catalog.
    In real enterprise this would go through schema validation, dedup, approval workflows.
    """
    required = ["product_id", "name"]
    if not all(k in payload for k in required):
        raise HTTPException(400, "product_id and name are required")

    catalog_path = settings.enterprise_catalog_file
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text())
    else:
        catalog = {"products": [], "symptoms": [], "failure_modes": [], "parts": []}

    # Prevent duplicates
    existing = {p["product_id"] for p in catalog.get("products", [])}
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

    return {
        "status": "staged",
        "product_id": payload["product_id"],
        "message": "Product added to staging catalog. Run Dry-run ETL → Validate → Review → Promote to incorporate into GraphRAG.",
        "catalog_products": len(catalog.get("products", [])),
    }


@app.get("/admin/pipeline/status", dependencies=[Depends(require_admin)])
def admin_pipeline_status() -> dict:
    """Current state of the knowledge base onboarding process."""
    catalog_products = 0
    if settings.enterprise_catalog_file.exists():
        try:
            catalog = json.loads(settings.enterprise_catalog_file.read_text())
            catalog_products = len(catalog.get("products", []))
        except Exception:
            pass

    return {
        "review_state": ADMIN_REVIEW_STATE,
        "catalog_stats": {
            "path": str(settings.enterprise_catalog_file),
            "exists": settings.enterprise_catalog_file.exists(),
            "products": catalog_products,
        },
        "lineage_last": list_batches(limit=3),
    }


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
