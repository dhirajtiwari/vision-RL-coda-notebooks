"""
Simulated Enterprise Applications API
======================================
Serves CRM, PIM, Claims, FSM, and Case Management endpoints from fixture data.

Run: python -m simulation.mock_enterprise_apps
     uvicorn simulation.mock_enterprise_apps:app --port 8090
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config.settings import settings

app = FastAPI(
    title="Enterprise Systems Simulator",
    description="Mock CRM, PIM, Claims, FSM, and Case Management for diagnostics demo",
    version="1.0.0",
)

SOURCES = settings.enterprise_sources_dir


def _load(name: str) -> dict[str, Any]:
    path = SOURCES / name
    if not path.exists():
        raise HTTPException(404, f"Fixture not found: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "enterprise-simulator", "timestamp": datetime.now(UTC).isoformat()}


@app.get("/api/pim/products")
def pim_products() -> dict[str, Any]:
    return _load("pim_catalog.json")


@app.get("/api/fsm/work-orders")
def fsm_work_orders(status: str = "closed") -> dict[str, Any]:
    data = _load("fsm_work_orders.json")
    if status != "closed":
        return {"closed_work_orders": []}
    return data


@app.get("/api/claims/closed")
def claims_closed() -> dict[str, Any]:
    return _load("claims_history.json")


@app.get("/api/crm/customers")
def crm_customers() -> dict[str, Any]:
    data = _load("crm_assets.json")
    return {"customers": data.get("customers", [])}


@app.get("/api/crm/customers/{customer_id}/assets")
def crm_customer_assets(customer_id: str) -> dict[str, Any]:
    data = _load("crm_assets.json")
    assets = [a for a in data.get("registered_assets", []) if a.get("customer_id") == customer_id]
    if not assets:
        raise HTTPException(404, f"No assets for customer {customer_id}")
    customer = next((c for c in data.get("customers", []) if c["customer_id"] == customer_id), None)
    return {"customer": customer, "registered_assets": assets}


@app.get("/api/crm/assets/{asset_id}")
def crm_asset(asset_id: str) -> dict[str, Any]:
    data = _load("crm_assets.json")
    asset = next((a for a in data.get("registered_assets", []) if a.get("asset_id") == asset_id), None)
    if not asset:
        raise HTTPException(404, f"Asset not found: {asset_id}")
    customer = next((c for c in data.get("customers", []) if c["customer_id"] == asset.get("customer_id")), None)
    return {"asset": asset, "customer": customer}


class CaseCreate(BaseModel):
    customer_id: str
    asset_id: str
    user_message: str
    diagnosis: dict[str, Any]
    escalation_reason: str = ""


@app.post("/api/cases")
def create_case(body: CaseCreate) -> dict[str, Any]:
    from utils.persistence import get_store

    case = {
        "case_id": f"CASE-{uuid.uuid4().hex[:8].upper()}",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "open",
        "source_system": "DiagnosticsPlatform",
        **body.model_dump(),
    }
    return get_store().save_case(case)


@app.get("/api/cases")
def list_cases() -> dict[str, Any]:
    from utils.persistence import get_store

    return {"cases": get_store().list_cases()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("simulation.mock_enterprise_apps:app", host="0.0.0.0", port=8090, reload=False)
