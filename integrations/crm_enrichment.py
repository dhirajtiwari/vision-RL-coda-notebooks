"""Runtime CRM enrichment — bind customer asset and warranty context to diagnosis session."""

from __future__ import annotations

import json
from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.http_client import get_json

CRM_FIXTURE = settings.enterprise_sources_dir / "crm_assets.json"


def _fixture_enrich(customer_id: str | None, asset_id: str | None) -> dict[str, Any] | None:
    if not CRM_FIXTURE.exists():
        return None
    data = json.loads(CRM_FIXTURE.read_text(encoding="utf-8"))
    if asset_id:
        asset = next((a for a in data.get("registered_assets", []) if a.get("asset_id") == asset_id), None)
        if not asset:
            return None
        customer = next((c for c in data.get("customers", []) if c["customer_id"] == asset.get("customer_id")), None)
        return {
            "enriched": True,
            "customer_id": customer.get("customer_id") if customer else asset.get("customer_id"),
            "customer_name": customer.get("name") if customer else None,
            "asset_id": asset.get("asset_id"),
            "product_id": asset.get("product_id"),
            "serial_number": asset.get("serial_number"),
            "warranty_status": asset.get("warranty_status"),
            "warranty_expiry": asset.get("warranty_expiry"),
            "purchase_date": asset.get("purchase_date"),
            "source_system": "CRM",
            "source_record_id": asset_id,
        }
    if customer_id:
        customer = next((c for c in data.get("customers", []) if c["customer_id"] == customer_id), None)
        assets = [a for a in data.get("registered_assets", []) if a.get("customer_id") == customer_id]
        primary = assets[0] if assets else {}
        return {
            "enriched": True,
            "customer_id": customer_id,
            "customer_name": customer.get("name") if customer else None,
            "registered_assets": assets,
            "product_id": primary.get("product_id"),
            "asset_id": primary.get("asset_id"),
            "source_system": "CRM",
            "source_record_id": customer_id,
        }
    return None


def enrich_session_from_crm(
    customer_id: str | None = None,
    asset_id: str | None = None,
) -> dict[str, Any]:
    base = settings.resolved_crm_url()
    if not base:
        return {"enriched": False, "reason": "CRM not configured"}

    try:
        if asset_id:
            payload = get_json(f"{base.rstrip('/')}/assets/{asset_id}")
            asset = payload.get("asset", {})
            customer = payload.get("customer", {})
            return {
                "enriched": True,
                "customer_id": customer.get("customer_id"),
                "customer_name": customer.get("name"),
                "asset_id": asset.get("asset_id"),
                "product_id": asset.get("product_id"),
                "serial_number": asset.get("serial_number"),
                "warranty_status": asset.get("warranty_status"),
                "warranty_expiry": asset.get("warranty_expiry"),
                "purchase_date": asset.get("purchase_date"),
                "source_system": "CRM",
                "source_record_id": asset_id,
            }
        if customer_id:
            payload = get_json(f"{base.rstrip('/')}/customers/{customer_id}/assets")
            assets = payload.get("registered_assets", [])
            customer = payload.get("customer", {})
            primary = assets[0] if assets else {}
            return {
                "enriched": True,
                "customer_id": customer_id,
                "customer_name": customer.get("name"),
                "registered_assets": assets,
                "product_id": primary.get("product_id"),
                "asset_id": primary.get("asset_id"),
                "source_system": "CRM",
                "source_record_id": customer_id,
            }
    except ConnectionError:
        fallback = _fixture_enrich(customer_id, asset_id)
        if fallback:
            return fallback
        return {"enriched": False, "reason": "CRM unavailable and no fixture match"}

    return {"enriched": False, "reason": "customer_id or asset_id required"}