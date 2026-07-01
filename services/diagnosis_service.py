"""
Diagnosis orchestration service.

Single source of truth for the customer-facing diagnosis workflow so the REST
API and the Streamlit UI cannot drift apart. The business rules encapsulated
here are:

  1. Warranty gate  — if the asset is enriched from CRM and the warranty is not
     eligible, short-circuit with an out-of-warranty message.
  2. Graph diagnosis — run the LangGraph/GraphRAG diagnosis.
  3. Escalation handoff — when the diagnosis escalates and we have a CRM-bound
     customer + asset, open a case in the (simulated) case-management system.

Both entry points call :func:`run_full_diagnosis`; neither reimplements these
rules.
"""

from __future__ import annotations

from agents.diagnosis_graph import run_diagnosis
from domain.models import DiagnosisOutcome
from integrations.case_management import create_case_from_escalation


def _out_of_warranty_message(warranty: dict) -> str:
    return (
        f"Warranty check: {warranty.get('reason')}. "
        "Please contact support for out-of-warranty options."
    )


def run_full_diagnosis(
    message: str,
    *,
    product_id: str | None = None,
    asset_id: str | None = None,
    crm_context: dict | None = None,
    warranty: dict | None = None,
) -> DiagnosisOutcome:
    """
    Execute warranty gating, diagnosis, and escalation handoff.

    Args:
        message: the customer's free-text description.
        product_id: optional resolved product id (falls back to CRM/asset).
        asset_id: optional CRM asset id (binds model/SKU/BOM for parts).
        crm_context: CRM enrichment result (``enriched`` flag drives gating).
        warranty: warranty decision dict (only enforced when CRM-enriched).
    """
    crm_context = crm_context or {}
    warranty = warranty or {}
    active_warranty = warranty if crm_context.get("enriched") else {}

    # 1. Warranty gate.
    if active_warranty and not active_warranty.get("eligible"):
        return DiagnosisOutcome(
            response=_out_of_warranty_message(active_warranty),
            warranty_blocked=True,
            warranty=active_warranty,
            crm_context=crm_context,
        )

    # 2. Graph diagnosis (asset binding only when CRM-enriched).
    result = run_diagnosis(
        message,
        product_id=product_id,
        asset_id=asset_id if crm_context.get("enriched") else None,
    )
    diagnosis = result.get("diagnosis") or {}
    escalated = bool(result.get("escalated"))
    case_id = result.get("case_id")

    # 3. Escalation handoff to the (simulated) case-management system.
    if escalated and crm_context.get("customer_id") and crm_context.get("asset_id"):
        case = create_case_from_escalation(
            customer_id=crm_context["customer_id"],
            asset_id=crm_context["asset_id"],
            user_message=message,
            diagnosis=diagnosis,
        )
        if case.get("case_id"):
            case_id = case["case_id"]

    return DiagnosisOutcome(
        response=result.get("response", ""),
        diagnosis=diagnosis,
        escalated=escalated,
        case_id=case_id,
        warranty=active_warranty,
        crm_context=crm_context,
    )
