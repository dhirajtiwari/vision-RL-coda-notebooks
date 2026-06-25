"""Warranty eligibility gate using CRM asset + claims policy metadata."""

from __future__ import annotations

from datetime import date
from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.http_client import get_json


def check_warranty_eligibility(asset: dict[str, Any]) -> dict[str, Any]:
    status = asset.get("warranty_status", "unknown")
    expiry = asset.get("warranty_expiry", "")
    eligible = status == "active"
    reason = "Warranty active" if eligible else f"Warranty status: {status}"

    if expiry:
        try:
            expiry_date = date.fromisoformat(expiry)
            if expiry_date < date.today():
                eligible = False
                reason = f"Warranty expired on {expiry}"
        except ValueError:
            pass

    policies: list[dict] = []
    claims_url = settings.resolved_claims_url()
    if claims_url:
        try:
            data = get_json(f"{claims_url.rstrip('/')}/closed")
            policies = data.get("warranty_policies", [])
        except ConnectionError:
            pass

    return {
        "eligible": eligible,
        "reason": reason,
        "warranty_status": status,
        "warranty_expiry": expiry,
        "policy_reference": policies[0].get("policy_id") if policies else None,
        "source_system": "CRM+Claims",
    }