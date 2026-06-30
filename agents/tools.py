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


def tool_list_products() -> list[dict]:
    return list_products()


def tool_detect_product(message: str) -> dict | None:
    return detect_product(message)


def tool_diagnose(
    message: str,
    product_id: str | None = None,
    asset_id: str | None = None,
) -> dict:
    result = diagnose(message, product_id=product_id, asset_id=asset_id)
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
        "should_escalate": result.should_escalate,
        "escalation_reason": result.escalation_reason,
        "evidence": result.evidence,
        "provenance_trail": result.provenance_trail,
        "formatted_response": format_diagnosis_response(result),
    }
    if result.product_id:
        payload["graph_subgraph"] = diagnosis_subgraph_from_result(payload)
    return payload


def tool_get_steps(product_id: str) -> list[dict]:
    return get_diagnostic_steps(product_id)


def tool_rank_failures(product_id: str, symptom_ids: list[str]) -> list[dict]:
    return rank_failure_modes(product_id, symptom_ids)