"""Runtime CRM enrichment — bind customer asset and warranty context to diagnosis session."""

from __future__ import annotations

from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.http_client import get_json


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
    except ConnectionError as exc:
        return {"enriched": False, "reason": str(exc)}

    return {"enriched": False, "reason": "customer_id or asset_id required"}