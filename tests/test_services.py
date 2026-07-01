"""Tests for the shared diagnosis service orchestration and domain models."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from domain.models import DiagnosisOutcome, WarrantyDecision
from services.diagnosis_service import run_full_diagnosis


def test_warranty_gate_short_circuits_without_diagnosis():
    """An enriched but ineligible warranty blocks before any graph diagnosis."""
    outcome = run_full_diagnosis(
        "washer will not spin",
        crm_context={"enriched": True, "customer_id": "C1", "asset_id": "A1"},
        warranty={"eligible": False, "reason": "Warranty expired on 2020-01-01"},
    )
    assert isinstance(outcome, DiagnosisOutcome)
    assert outcome.warranty_blocked is True
    assert outcome.diagnosis == {}
    assert outcome.escalated is False
    assert "Warranty expired" in outcome.response


def test_warranty_decision_preserves_extra_policy_fields():
    payload = WarrantyDecision(
        eligible=True,
        reason="Warranty active",
        warranty_status="active",
        policy_reference="POL-123",
        covers_parts=True,
        estimated_parts_cost_usd=42.0,
    ).model_dump()
    assert payload["eligible"] is True
    assert payload["policy_reference"] == "POL-123"
    assert payload["estimated_parts_cost_usd"] == 42.0
