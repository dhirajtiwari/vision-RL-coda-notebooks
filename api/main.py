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

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from agents.diagnosis_graph import run_diagnosis
from api.schemas import ClaimStatus, DiagnoseRequest, DiagnoseResponse, GraphSubgraphResponse
from graph.graph_visualization import (
    diagnosis_subgraph_from_result,
    get_diagnosis_subgraph,
    get_ontology_schema,
    get_product_subgraph,
)
from config.settings import settings
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
    return GraphSubgraphResponse(
        **get_diagnosis_subgraph(product_id, symptom_ids=ids, failure_mode_id=failure_mode_id)
    )


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=False)