"""Warranty eligibility gate using CRM asset + claims policy metadata."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from config.settings import settings
from domain.models import WarrantyDecision
from graph.enterprise_pipeline.http_client import get_json

CLAIMS_FIXTURE = settings.enterprise_sources_dir / "claims_history.json"


def check_warranty_eligibility(
    asset: dict[str, Any],
    *,
    predicted_parts: list[dict[str, Any]] | None = None,
    failure_mode_id: str | None = None,
) -> dict[str, Any]:
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
            if CLAIMS_FIXTURE.exists():
                data = json.loads(CLAIMS_FIXTURE.read_text(encoding="utf-8"))
                policies = data.get("warranty_policies", [])

    policy = policies[0] if policies else {}
    parts_cost = 0.0
    if predicted_parts:
        parts_cost = sum((p.get("estimated_cost_usd") or 0) * (p.get("quantity") or 1) for p in predicted_parts)

    parts_covered = policy.get("covers_parts", True)
    labor_covered = policy.get("covers_labor", True)
    max_parts = policy.get("max_parts_cost_usd")

    coverage_notes: list[str] = []
    if failure_mode_id:
        coverage_notes.append(f"Diagnosis failure mode: {failure_mode_id}")
    if predicted_parts:
        coverage_notes.append(f"Estimated parts cost: ${parts_cost:.2f}")
        if max_parts and parts_cost > max_parts:
            eligible = False
            reason = f"Estimated parts cost ${parts_cost:.2f} exceeds policy cap ${max_parts:.2f}"
        elif not parts_covered:
            coverage_notes.append("Policy excludes parts coverage")

    return WarrantyDecision(
        eligible=eligible,
        reason=reason,
        warranty_status=status,
        warranty_expiry=expiry,
        policy_reference=policy.get("policy_id"),
        covers_parts=parts_covered,
        covers_labor=labor_covered,
        estimated_parts_cost_usd=round(parts_cost, 2) if predicted_parts else None,
        coverage_notes=coverage_notes,
        source_system="CRM+Claims",
    ).model_dump()
