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
        customer = next(
            (c for c in data.get("customers", []) if c["customer_id"] == asset.get("customer_id")),
            None,
        )
        return _build_enrichment(
            customer=customer,
            asset=asset,
            requested_customer_id=customer_id,
            source_record_id=asset_id,
        )
    if customer_id:
        customer = next((c for c in data.get("customers", []) if c["customer_id"] == customer_id), None)
        assets = [a for a in data.get("registered_assets", []) if a.get("customer_id") == customer_id]
        primary = assets[0] if assets else {}
        return _build_enrichment(
            customer=customer,
            asset=primary,
            requested_customer_id=customer_id,
            source_record_id=customer_id,
            registered_assets=assets,
        )
    return None


def _build_enrichment(
    *,
    customer: dict[str, Any] | None,
    asset: dict[str, Any],
    requested_customer_id: str | None,
    source_record_id: str,
    registered_assets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    owner_id = customer.get("customer_id") if customer else asset.get("customer_id")
    owner_name = customer.get("name") if customer else None
    warnings: list[str] = []
    customer_asset_mismatch = False

    if requested_customer_id and owner_id and requested_customer_id != owner_id:
        customer_asset_mismatch = True
        warnings.append(
            f"Selected customer does not own asset `{asset.get('asset_id')}`. "
            f"Using asset owner **{owner_name or owner_id}**."
        )

    payload: dict[str, Any] = {
        "enriched": True,
        "customer_id": owner_id,
        "customer_name": owner_name,
        "asset_id": asset.get("asset_id"),
        "product_id": asset.get("product_id"),
        "serial_number": asset.get("serial_number"),
        "warranty_status": asset.get("warranty_status"),
        "warranty_expiry": asset.get("warranty_expiry"),
        "purchase_date": asset.get("purchase_date"),
        "source_system": "CRM",
        "source_record_id": source_record_id,
    }
    if registered_assets is not None:
        payload["registered_assets"] = registered_assets
    if requested_customer_id:
        payload["requested_customer_id"] = requested_customer_id
    if customer_asset_mismatch:
        payload["customer_asset_mismatch"] = True
    if warnings:
        payload["warnings"] = warnings
    return payload


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
            return _build_enrichment(
                customer=customer,
                asset=asset,
                requested_customer_id=customer_id,
                source_record_id=asset_id,
            )
        if customer_id:
            payload = get_json(f"{base.rstrip('/')}/customers/{customer_id}/assets")
            assets = payload.get("registered_assets", [])
            customer = payload.get("customer", {})
            primary = assets[0] if assets else {}
            return _build_enrichment(
                customer=customer,
                asset=primary,
                requested_customer_id=customer_id,
                source_record_id=customer_id,
                registered_assets=assets,
            )
    except ConnectionError:
        if settings.effective_fixture_fallback:
            fallback = _fixture_enrich(customer_id, asset_id)
            if fallback:
                fallback["source_mode"] = "fixture_fallback"
                return fallback
        return {"enriched": False, "reason": "CRM unavailable"}

    return {"enriched": False, "reason": "customer_id or asset_id required"}
