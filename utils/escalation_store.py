"""Persist escalation cases for the human agent dashboard."""

from __future__ import annotations

from typing import Any

from utils.persistence import get_store


def list_escalations(*, status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    rows = get_store().list_escalations(status=status)
    return rows[:limit] if limit else rows


def count_escalations(*, status: str | None = None) -> int:
    return get_store().count_escalations(status=status)


def save_escalation(
    user_message: str,
    diagnosis_payload: dict[str, Any],
    status: str = "open",
) -> dict[str, Any]:
    return get_store().save_escalation(user_message, diagnosis_payload, status=status)


def update_escalation_status(case_id: str, status: str) -> bool:
    return get_store().update_escalation_status(case_id, status)