"""Persist escalation cases for the human agent dashboard."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import settings


def _ensure_file() -> None:
    settings.escalations_file.parent.mkdir(parents=True, exist_ok=True)
    if not settings.escalations_file.exists():
        settings.escalations_file.write_text("[]", encoding="utf-8")


def list_escalations() -> list[dict[str, Any]]:
    _ensure_file()
    return json.loads(settings.escalations_file.read_text(encoding="utf-8"))


def save_escalation(
    user_message: str,
    diagnosis_payload: dict[str, Any],
    status: str = "open",
) -> dict[str, Any]:
    _ensure_file()
    cases = list_escalations()
    case = {
        "case_id": str(uuid.uuid4())[:8],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "user_message": user_message,
        "diagnosis": diagnosis_payload,
    }
    cases.insert(0, case)
    settings.escalations_file.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    return case


def update_escalation_status(case_id: str, status: str) -> bool:
    cases = list_escalations()
    updated = False
    for case in cases:
        if case["case_id"] == case_id:
            case["status"] = status
            case["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break
    if updated:
        settings.escalations_file.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    return updated