"""
Warranty claim interaction workflow — submit, track, and resolve claims
from diagnosis outcomes using graph-backed evidence.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from graph.neo4j_client import get_driver
from graph.parts_predictor import predict_parts
from integrations.warranty_eligibility import check_warranty_eligibility
from utils.persistence import get_store


def submit_claim_from_diagnosis(
    *,
    diagnosis: dict[str, Any],
    asset_id: str,
    customer_id: str,
    user_message: str,
) -> dict[str, Any]:
    """Create a warranty claim submission from a completed diagnosis."""
    product_id = diagnosis.get("product_id", "")
    top_fm = (diagnosis.get("ranked_failure_modes") or [None])[0]
    failure_mode_id = top_fm.get("failure_mode_id") if top_fm else None
    sku_id = diagnosis.get("sku_id")
    predicted = diagnosis.get("predicted_parts") or diagnosis.get("parts") or []

    if not predicted and product_id and failure_mode_id:
        predicted = predict_parts(product_id, failure_mode_id, sku_id=sku_id or None)

    asset_ctx = {"asset_id": asset_id, "customer_id": customer_id, "warranty_status": "active"}
    warranty = check_warranty_eligibility(
        asset_ctx,
        predicted_parts=predicted,
        failure_mode_id=failure_mode_id,
    )

    claim_id = f"CLM-SUB-{uuid.uuid4().hex[:8].upper()}"
    primary_part = predicted[0] if predicted else {}
    total_cost = sum((p.get("estimated_cost_usd") or 0) * (p.get("quantity") or 1) for p in predicted)

    claim = {
        "claim_id": claim_id,
        "status": "submitted" if warranty.get("eligible") else "pending_review",
        "asset_id": asset_id,
        "customer_id": customer_id,
        "product_id": product_id,
        "sku_id": sku_id,
        "model_number": diagnosis.get("model_number"),
        "failure_mode_id": failure_mode_id,
        "failure_mode_name": top_fm.get("name") if top_fm else None,
        "symptom_ids": [s.get("symptom_id") for s in diagnosis.get("matched_symptoms", [])],
        "error_codes": [e.get("code") for e in diagnosis.get("matched_error_codes", [])],
        "predicted_parts": predicted,
        "estimated_parts_cost_usd": round(total_cost, 2),
        "primary_part_id": primary_part.get("part_id"),
        "warranty_check": warranty,
        "user_message": user_message,
        "diagnosis_confidence": diagnosis.get("confidence"),
        "submitted_at": datetime.now(UTC).isoformat(),
        "graph_evidence": diagnosis.get("evidence", []),
    }

    get_store().save_claim(claim)
    _persist_claim_to_neo4j(claim)
    return claim


def _persist_claim_to_neo4j(claim: dict[str, Any]) -> None:
    try:
        driver = get_driver()
    except Exception:
        return
    with driver.session() as session:
        session.run(
            """
            MERGE (cl:Claim {claim_id: $claim_id})
            SET cl.status = $status, cl.resolution_summary = $summary,
                cl.closed_date = $submitted_at, cl.symptom_id = $symptom_id
            """,
            {
                "claim_id": claim["claim_id"],
                "status": claim["status"],
                "summary": f"Submitted: {claim.get('failure_mode_name', 'diagnosis')}",
                "submitted_at": claim["submitted_at"][:10],
                "symptom_id": (claim.get("symptom_ids") or [""])[0],
            },
        )
        if claim.get("asset_id"):
            session.run(
                """
                MATCH (cl:Claim {claim_id: $claim_id})
                MERGE (a:Asset {asset_id: $asset_id})
                MERGE (cl)-[:FOR_ASSET]->(a)
                """,
                {"claim_id": claim["claim_id"], "asset_id": claim["asset_id"]},
            )
        if claim.get("failure_mode_id"):
            session.run(
                """
                MATCH (cl:Claim {claim_id: $claim_id})
                MATCH (fm:FailureMode {failure_mode_id: $fm_id})
                MERGE (cl)-[:CONFIRMED]->(fm)
                """,
                {"claim_id": claim["claim_id"], "fm_id": claim["failure_mode_id"]},
            )
        if claim.get("primary_part_id"):
            session.run(
                """
                MATCH (cl:Claim {claim_id: $claim_id})
                MATCH (pt:Part {part_id: $part_id})
                MERGE (cl)-[:USED_PART]->(pt)
                """,
                {"claim_id": claim["claim_id"], "part_id": claim["primary_part_id"]},
            )


def list_submitted_claims(limit: int = 50) -> list[dict]:
    return get_store().list_claims(limit=limit)


def get_claim(claim_id: str) -> dict | None:
    return get_store().get_claim(claim_id)


def update_claim_status(claim_id: str, status: str, *, agent_notes: str = "") -> dict | None:
    return get_store().update_claim(
        claim_id,
        {"status": status, "agent_notes": agent_notes},
    )
