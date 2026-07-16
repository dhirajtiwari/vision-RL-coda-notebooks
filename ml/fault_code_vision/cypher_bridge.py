"""Cypher templates matching graph/graph_rag.py ErrorCode paths."""

from __future__ import annotations

from typing import Any


def cypher_for_extracted_code(code: str, product_id: str = "wm-001") -> dict[str, Any]:
    """Parameterized Cypher aligned with production GraphRAG contracts."""
    q_match = """
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
WHERE toUpper(ec.code) = toUpper($code)
RETURN ec.error_code_id AS error_code_id,
       ec.code AS code,
       ec.description AS description
""".strip()
    q_fm = """
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
WHERE toUpper(ec.code) = toUpper($code)
MATCH (ec)-[r:INDICATES]->(fm:FailureMode)
RETURN fm.failure_mode_id AS failure_mode_id,
       fm.name AS name,
       r.confidence AS confidence
ORDER BY r.confidence DESC
""".strip()
    q_boost = """
MATCH (ec:ErrorCode)-[r:INDICATES]->(fm:FailureMode)
WHERE ec.error_code_id IN $error_code_ids
RETURN fm.failure_mode_id AS failure_mode_id, sum(r.confidence) AS error_boost
""".strip()
    q_resolution = """
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
WHERE toUpper(ec.code) = toUpper($code)
MATCH (ec)-[:INDICATES]->(fm:FailureMode)
OPTIONAL MATCH (ds:DiagnosticStep)-[:CONFIRMS]->(fm)
OPTIONAL MATCH (fm)-[:REQUIRES_PART]->(part:Part)
OPTIONAL MATCH (hr:HistoricalResolution)-[:RESOLVED]->(fm)
RETURN ec, fm,
       collect(DISTINCT ds) AS confirm_steps,
       collect(DISTINCT part) AS parts,
       collect(DISTINCT hr) AS historical
""".strip()
    return {
        "match_code_on_product": q_match,
        "failure_modes_for_code": q_fm,
        "error_code_boost": q_boost,
        "resolution_path": q_resolution,
        "params": {"product_id": product_id, "code": code},
    }


def diagnose_payload_from_ocr(
    ocr_result: dict[str, Any],
    product_id: str = "wm-001",
) -> dict[str, Any]:
    """Build API-shaped payload from FaultCodeReader.predict()."""
    code = ocr_result.get("code")
    if not code:
        return {
            "product_id": product_id,
            "extracted_code": None,
            "should_escalate": True,
            "escalation_reason": "fault_code_ocr_low_confidence_or_unknown",
            "ocr": ocr_result,
        }
    from ml.fault_code_vision.infer import user_message_for_graph_rag

    return {
        "product_id": product_id,
        "extracted_code": code,
        "confidence": ocr_result.get("confidence"),
        "user_message": user_message_for_graph_rag(code),
        "cypher": cypher_for_extracted_code(code, product_id=product_id),
        "should_escalate": bool(ocr_result.get("escalate")),
        "ocr": ocr_result,
        "model_version": ocr_result.get("model_checkpoint"),
    }
