"""
Diagnostics REST API
====================
Enterprise-grade demo API wrapping LangGraph diagnosis with CRM enrichment.

Run: python -m api.main
     uvicorn api.main:app --port 8080
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException

from agents.diagnosis_graph import run_diagnosis
from api.schemas import DiagnoseRequest, DiagnoseResponse
from config.settings import settings
from graph.neo4j_client import verify_connection
from integrations.case_management import create_case_from_escalation
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility
from utils.lineage_store import list_batches

app = FastAPI(
    title="Enterprise Diagnostics API",
    description="GraphRAG warranty diagnosis with CRM enrichment and provenance",
    version="1.0.0",
)


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


@app.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(req: DiagnoseRequest) -> DiagnoseResponse:
    if not verify_connection():
        raise HTTPException(503, "Neo4j unavailable")

    crm = enrich_session_from_crm(customer_id=req.customer_id, asset_id=req.asset_id)
    product_id = req.product_id or crm.get("product_id")

    warranty: dict = {}
    if crm.get("enriched") and crm.get("warranty_status"):
        warranty = check_warranty_eligibility(crm)
        if not warranty.get("eligible"):
            return DiagnoseResponse(
                response=f"Warranty check: {warranty.get('reason')}. Please contact support for out-of-warranty options.",
                crm_context=crm,
                warranty=warranty,
            )

    result = run_diagnosis(req.message, product_id=product_id)
    diagnosis = result.get("diagnosis") or {}
    provenance_trail = diagnosis.get("provenance_trail", [])

    case_id = result.get("case_id")
    if result.get("escalated") and crm.get("customer_id") and crm.get("asset_id"):
        case = create_case_from_escalation(
            customer_id=crm["customer_id"],
            asset_id=crm["asset_id"],
            user_message=req.message,
            diagnosis=diagnosis,
        )
        if case.get("case_id"):
            case_id = case["case_id"]

    return DiagnoseResponse(
        response=result["response"],
        diagnosis=diagnosis,
        escalated=result.get("escalated", False),
        case_id=case_id,
        crm_context=crm,
        warranty=warranty,
        provenance_trail=provenance_trail,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host=settings.api_host, port=settings.api_port, reload=False)