"""Agent tools wrapping the GraphRAG layer."""

from graph.graph_rag import (
    detect_product,
    diagnose,
    format_diagnosis_response,
    get_diagnostic_steps,
    list_products,
    rank_failure_modes,
)
from graph.graph_visualization import diagnosis_subgraph_from_result
from graph.knowledge_lineage import get_product_knowledge_profile


def tool_list_products() -> list[dict]:
    return list_products()


def tool_detect_product(message: str) -> dict | None:
    return detect_product(message)


def tool_diagnose(
    message: str,
    product_id: str | None = None,
    asset_id: str | None = None,
    crm_product_id: str | None = None,
    force_keep_context: bool = False,
    crm_context: dict | None = None,
) -> dict:
    result = diagnose(
        message,
        product_id=product_id,
        asset_id=asset_id,
        crm_product_id=crm_product_id,
        force_keep_context=force_keep_context,
        crm_context=crm_context,
    )
    payload = {
        "product_id": result.product_id,
        "product_name": result.product_name,
        "asset_id": result.asset_id,
        "model_number": result.model_number,
        "sku_id": result.sku_id,
        "serial_number": result.serial_number,
        "matched_symptoms": result.matched_symptoms,
        "matched_error_codes": result.matched_error_codes,
        "ranked_failure_modes": result.ranked_failure_modes,
        "diagnostic_steps": result.diagnostic_steps,
        "impacted_components": result.impacted_components,
        "parts": result.parts,
        "predicted_parts": result.predicted_parts,
        "claim_precedents": result.claim_precedents,
        "diagnostic_tree": result.diagnostic_tree,
        "historical_resolutions": result.historical_resolutions,
        "confidence": result.confidence,
        "graph_confidence": result.graph_confidence,
        "language_confidence": result.language_confidence,
        # Separated scoring transparency fields (for UI display)
        "recommendation_strength": result.recommendation_strength,
        "posterior_dominance_ratio": result.posterior_dominance_ratio,
        # Exact traversal path (for precise graph highlighting)
        "traversed_symptom_ids": result.traversed_symptom_ids,
        "traversed_fm_id": result.traversed_fm_id,
        "should_escalate": result.should_escalate,
        "escalation_reason": result.escalation_reason,
        "evidence": result.evidence,
        "provenance_trail": result.provenance_trail,
        "warnings": result.warnings,
        "context_blocked": result.context_blocked,
        "context_block_code": result.context_block_code,
        "resolution_meta": result.resolution_meta,
        "formatted_response": format_diagnosis_response(result),
    }
    # Never attach a misleading subgraph when diagnosis was blocked for context.
    if result.product_id and not result.context_blocked:
        payload["graph_subgraph"] = diagnosis_subgraph_from_result(payload)
        payload["knowledge_profile"] = get_product_knowledge_profile(result.product_id)
    return payload


def tool_get_steps(product_id: str) -> list[dict]:
    return get_diagnostic_steps(product_id)


def tool_rank_failures(product_id: str, symptom_ids: list[str]) -> list[dict]:
    return rank_failure_modes(product_id, symptom_ids)
