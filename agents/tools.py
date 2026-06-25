"""Agent tools wrapping the GraphRAG layer."""

from graph.graph_rag import (
    detect_product,
    diagnose,
    format_diagnosis_response,
    get_diagnostic_steps,
    list_products,
    rank_failure_modes,
)


def tool_list_products() -> list[dict]:
    return list_products()


def tool_detect_product(message: str) -> dict | None:
    return detect_product(message)


def tool_diagnose(message: str, product_id: str | None = None) -> dict:
    result = diagnose(message, product_id=product_id)
    return {
        "product_id": result.product_id,
        "product_name": result.product_name,
        "matched_symptoms": result.matched_symptoms,
        "ranked_failure_modes": result.ranked_failure_modes,
        "diagnostic_steps": result.diagnostic_steps,
        "parts": result.parts,
        "historical_resolutions": result.historical_resolutions,
        "confidence": result.confidence,
        "should_escalate": result.should_escalate,
        "escalation_reason": result.escalation_reason,
        "evidence": result.evidence,
        "provenance_trail": result.provenance_trail,
        "formatted_response": format_diagnosis_response(result),
    }


def tool_get_steps(product_id: str) -> list[dict]:
    return get_diagnostic_steps(product_id)


def tool_rank_failures(product_id: str, symptom_ids: list[str]) -> list[dict]:
    return rank_failure_modes(product_id, symptom_ids)