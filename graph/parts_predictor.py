"""
Parts predictor: ranks replacement parts from failure mode, BOM components,
SKU compatibility, and historical claim usage.

Scoring is deterministic and probability-based rather than hand-tuned:

    prediction_score = P(failure_mode | symptoms)          # diagnostic posterior
                     * source_reliability                  # trust in the evidence path
                     * P(part | failure_mode)              # BOM edge probability

P(failure_mode | symptoms) is the naive-Bayes posterior from the diagnosis
engine (graph/reliability.py). Each evidence path (direct BOM link, inferred
component realisation, SKU compatibility, historical claim usage) carries a
reliability weight reflecting how directly it implies the part is required.
"""

from __future__ import annotations

from typing import Any

from graph.neo4j_client import get_driver

# Reliability of each evidence path = how strongly it implies the part is the
# one actually required for the repair. Direct engineering BOM links are
# authoritative; component-inferred and historical paths are corroborating.
SOURCE_RELIABILITY: dict[str, float] = {
    "REQUIRES_PART": 1.00,  # direct FailureMode -> Part BOM link
    "CLAIM_PRECEDENT": 0.85,  # part used to resolve confirmed field claims
    "BOM_COMPONENT": 0.70,  # part realises an impacted component
    "SKU_FIT": 0.90,  # confirmed compatible with the asset's SKU
}


def predict_parts(
    product_id: str,
    failure_mode_id: str,
    *,
    sku_id: str | None = None,
    fm_posterior: float = 1.0,
) -> list[dict[str, Any]]:
    """
    Enterprise parts prediction chain:
    FailureMode -[:REQUIRES_PART]-> Part
    FailureMode -[:IMPACTS_COMPONENT]-> Component -[:REALIZED_BY]-> Part
    SKU -[:COMPATIBLE_WITH]-> Part (when asset-bound)
    Claim -[:USED_PART]-> Part (historical precedent boost)

    `fm_posterior` is the diagnosis posterior P(failure_mode | symptoms); it
    scales every prediction so a part can never be reported as more likely than
    the failure mode it treats.
    """
    weight = max(float(fm_posterior), 0.0) or 1.0
    driver = get_driver()
    predictions: dict[str, dict[str, Any]] = {}

    with driver.session() as session:
        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode {failure_mode_id: $fm_id})
                  -[rp:REQUIRES_PART]->(pt:Part)
            RETURN pt.part_id AS part_id, pt.name AS name, pt.part_number AS part_number,
                   pt.estimated_cost_usd AS estimated_cost_usd,
                   rp.quantity AS quantity, rp.probability AS probability,
                   rp.is_primary AS is_primary, 'REQUIRES_PART' AS source
            """,
            product_id=product_id,
            fm_id=failure_mode_id,
        ):
            _upsert_prediction(
                predictions,
                dict(row),
                base_score=weight * SOURCE_RELIABILITY["REQUIRES_PART"] * (row["probability"] or 0.9),
            )

        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode {failure_mode_id: $fm_id})
                  -[:IMPACTS_COMPONENT]->(c:Component)-[:REALIZED_BY]->(pt:Part)
            RETURN pt.part_id AS part_id, pt.name AS name, pt.part_number AS part_number,
                   pt.estimated_cost_usd AS estimated_cost_usd,
                   c.name AS component_name, c.component_id AS component_id,
                   'BOM_COMPONENT' AS source
            """,
            product_id=product_id,
            fm_id=failure_mode_id,
        ):
            rec = dict(row)
            _upsert_prediction(
                predictions,
                rec,
                base_score=weight * SOURCE_RELIABILITY["BOM_COMPONENT"],
                component=rec.get("component_name"),
            )

        if sku_id:
            for row in session.run(
                """
                MATCH (sku:SKU {sku_id: $sku_id})-[:COMPATIBLE_WITH]->(pt:Part)
                MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode {failure_mode_id: $fm_id})
                      -[:REQUIRES_PART]->(pt)
                RETURN pt.part_id AS part_id, pt.name AS name, pt.part_number AS part_number,
                       pt.estimated_cost_usd AS estimated_cost_usd, 'SKU_FIT' AS source
                """,
                sku_id=sku_id,
                product_id=product_id,
                fm_id=failure_mode_id,
            ):
                _upsert_prediction(
                    predictions,
                    dict(row),
                    base_score=weight * SOURCE_RELIABILITY["SKU_FIT"],
                    sku_fit=True,
                )

        for row in session.run(
            """
            MATCH (cl:Claim)-[:CONFIRMED]->(fm:FailureMode {failure_mode_id: $fm_id})
            MATCH (cl)-[:USED_PART]->(pt:Part)
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm)
            RETURN pt.part_id AS part_id, pt.name AS name, pt.part_number AS part_number,
                   pt.estimated_cost_usd AS estimated_cost_usd,
                   cl.claim_id AS claim_id, 'CLAIM_PRECEDENT' AS source
            ORDER BY cl.closed_date DESC LIMIT 3
            """,
            product_id=product_id,
            fm_id=failure_mode_id,
        ):
            rec = dict(row)
            _upsert_prediction(
                predictions,
                rec,
                base_score=weight * SOURCE_RELIABILITY["CLAIM_PRECEDENT"],
                claim_precedent=rec.get("claim_id"),
            )

    ranked = sorted(
        predictions.values(),
        key=lambda x: (x.get("is_primary", False), x.get("prediction_score", 0)),
        reverse=True,
    )
    for i, part in enumerate(ranked, start=1):
        part["rank"] = i
    return ranked


def _upsert_prediction(
    store: dict[str, dict[str, Any]],
    row: dict[str, Any],
    *,
    base_score: float,
    **extras: Any,
) -> None:
    part_id = row["part_id"]
    if part_id not in store:
        store[part_id] = {
            "part_id": part_id,
            "name": row["name"],
            "part_number": row["part_number"],
            "estimated_cost_usd": row.get("estimated_cost_usd"),
            "quantity": row.get("quantity", 1),
            "is_primary": row.get("is_primary", False),
            "prediction_score": round(float(base_score), 4),
            "evidence_sources": [row.get("source", "graph")],
            "impacted_components": [],
            "claim_precedents": [],
            "sku_compatible": extras.get("sku_fit", False),
        }
    else:
        store[part_id]["prediction_score"] = max(store[part_id]["prediction_score"], base_score)
        src = row.get("source", "graph")
        if src not in store[part_id]["evidence_sources"]:
            store[part_id]["evidence_sources"].append(src)

    if extras.get("component"):
        comps = store[part_id]["impacted_components"]
        if extras["component"] not in comps:
            comps.append(extras["component"])
    if extras.get("claim_precedent"):
        preds = store[part_id]["claim_precedents"]
        if extras["claim_precedent"] not in preds:
            preds.append(extras["claim_precedent"])
    if extras.get("sku_fit"):
        store[part_id]["sku_compatible"] = True
