"""Case management handoff — create case in simulated CCaaS / claims system."""

from __future__ import annotations

from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.http_client import post_json
from utils.persistence import get_store


def create_case_from_escalation(
    *,
    customer_id: str,
    asset_id: str,
    user_message: str,
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    url = f"{settings.mock_enterprise_api_url.rstrip('/')}/api/cases"
    payload = {
        "customer_id": customer_id,
        "asset_id": asset_id,
        "user_message": user_message,
        "diagnosis": diagnosis,
        "escalation_reason": diagnosis.get("escalation_reason", ""),
    }
    try:
        return post_json(url, payload)
    except ConnectionError:
        case = get_store().save_case({
            "status": "open",
            "source_system": "DiagnosticsPlatform",
            **payload,
        })
        return {**case, "created": True, "fallback": "sqlite"}