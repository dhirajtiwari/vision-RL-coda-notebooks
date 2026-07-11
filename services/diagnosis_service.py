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
from config.settings import settings
from domain.models import DiagnosisOutcome
from integrations.case_management import create_case_from_escalation
from runtime.diagnose_cache import cache_get_diagnosis, cache_set_diagnosis, diagnose_cache_key


def _out_of_warranty_message(warranty: dict) -> str:
    return f"Warranty check: {warranty.get('reason')}. Please contact support for out-of-warranty options."


def run_full_diagnosis(
    message: str,
    *,
    product_id: str | None = None,
    asset_id: str | None = None,
    crm_context: dict | None = None,
    warranty: dict | None = None,
    tenant_id: str | None = None,
    use_cache: bool | None = None,
    force_keep_context: bool = False,
) -> DiagnosisOutcome:
    """
    Execute warranty gating, diagnosis, and escalation handoff.

    Args:
        message: the customer's free-text description.
        product_id: optional resolved product id (falls back to CRM/asset).
        asset_id: optional CRM asset id (binds model/SKU/BOM for parts).
        crm_context: CRM enrichment result (``enriched`` flag drives gating).
        warranty: warranty decision dict (only enforced when CRM-enriched).
        tenant_id: optional tenant for cache partition.
        use_cache: override settings.enable_diagnose_cache for this call.
    """
    crm_context = crm_context or {}
    warranty = warranty or {}
    active_warranty = warranty if crm_context.get("enriched") else {}

    crm_product_id = crm_context.get("product_id") if crm_context.get("enriched") else None
    # Asset-first: when CRM asset is bound, product is derived from asset (not free-form override).
    identified = bool(crm_context.get("enriched") and (asset_id or crm_context.get("asset_id")))
    effective_product_id = crm_product_id if identified else product_id
    # Client product_id only used in anonymous mode or as invariant check inside resolve
    client_product_id = None if identified else product_id
    if identified and product_id and crm_product_id and product_id != crm_product_id:
        # Pass conflicting product so resolve fails API invariant
        client_product_id = product_id

    # 1. Warranty gate — from CRM asset only (identified session).
    if identified and active_warranty and not active_warranty.get("eligible"):
        return DiagnosisOutcome(
            response=_out_of_warranty_message(active_warranty),
            warranty_blocked=True,
            warranty=active_warranty,
            crm_context=crm_context,
        )

    effective_asset = (asset_id or crm_context.get("asset_id")) if identified else None
    cache_enabled = settings.enable_diagnose_cache if use_cache is None else use_cache
    cache_key = ""
    if cache_enabled and not force_keep_context:
        cache_key = diagnose_cache_key(
            message,
            product_id=effective_product_id or client_product_id,
            asset_id=effective_asset,
            tenant_id=tenant_id or settings.default_tenant_id,
        )
        hit = cache_get_diagnosis(cache_key)
        if hit is not None:
            outcome = DiagnosisOutcome(
                response=hit.get("response", ""),
                diagnosis=hit.get("diagnosis") or {},
                escalated=bool(hit.get("escalated")),
                case_id=hit.get("case_id"),
                warranty=active_warranty if identified else {},
                crm_context=crm_context,
            )
            if isinstance(outcome.diagnosis, dict):
                outcome.diagnosis = {**outcome.diagnosis, "_cache_hit": True}
            return outcome

    # 2. Graph diagnosis — asset-first when CRM-bound (product from asset; client product only for invariant / anonymous).
    result = run_diagnosis(
        message,
        product_id=client_product_id,
        asset_id=effective_asset,
        crm_product_id=crm_product_id,
        force_keep_context=force_keep_context,
        crm_context=crm_context if identified else None,
    )
    diagnosis = result.get("diagnosis") or {}
    escalated = bool(result.get("escalated"))
    case_id = result.get("case_id")
    context_blocked = bool(diagnosis.get("context_blocked"))
    soft_block = context_blocked and str(diagnosis.get("context_block_code") or "").startswith("soft_")

    # 3. Escalation handoff — only on real escalations for the bound asset.
    if escalated and not context_blocked and crm_context.get("customer_id") and crm_context.get("asset_id"):
        case = create_case_from_escalation(
            customer_id=crm_context["customer_id"],
            asset_id=crm_context["asset_id"],
            user_message=message,
            diagnosis=diagnosis,
        )
        if case.get("case_id"):
            case_id = case["case_id"]
    elif context_blocked:
        escalated = not soft_block
        case_id = None

    outcome = DiagnosisOutcome(
        response=result.get("response", ""),
        diagnosis=diagnosis,
        escalated=escalated,
        case_id=case_id,
        warranty=active_warranty if identified else {},
        crm_context=crm_context,
    )

    if cache_enabled and cache_key and not outcome.warranty_blocked and not context_blocked:
        cache_set_diagnosis(
            cache_key,
            {
                "response": outcome.response,
                "diagnosis": {k: v for k, v in (outcome.diagnosis or {}).items() if k != "_cache_hit"},
                "escalated": outcome.escalated,
                "case_id": outcome.case_id,
            },
        )
    return outcome
