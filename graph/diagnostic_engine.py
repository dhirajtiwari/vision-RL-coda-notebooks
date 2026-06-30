"""
Dynamic diagnostic decision engine — traverses Neo4j troubleshooting trees
(NEXT_STEP, CONFIRMS, RULES_OUT) alongside symptom/error-code ranking.
"""

from __future__ import annotations

from typing import Any

from graph.neo4j_client import get_driver


def get_diagnostic_tree(product_id: str) -> dict[str, Any]:
    """Return ordered troubleshooting tree with branches for a product."""
    driver = get_driver()
    with driver.session() as session:
        steps = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
            RETURN ds.step_id AS step_id, ds.description AS description,
                   ds.order AS step_order, ds.expected_outcome AS expected_outcome
            ORDER BY ds.order
            """,
            product_id=product_id,
        )
        step_list = [dict(r) for r in steps]
        step_ids = [s["step_id"] for s in step_list]

        edges = []
        if step_ids:
            for row in session.run(
                """
                MATCH (a:DiagnosticStep)-[r:NEXT_STEP]->(b:DiagnosticStep)
                WHERE a.step_id IN $ids AND b.step_id IN $ids
                RETURN a.step_id AS from_step_id, b.step_id AS to_step_id, r.condition AS condition
                """,
                ids=step_ids,
            ):
                edges.append(dict(row))

        confirmations = []
        if step_ids:
            for row in session.run(
                """
                MATCH (ds:DiagnosticStep)-[r:CONFIRMS]->(fm:FailureMode)
                WHERE ds.step_id IN $ids
                RETURN ds.step_id AS step_id, fm.failure_mode_id AS failure_mode_id,
                       fm.name AS failure_mode_name, r.confidence AS confidence
                """,
                ids=step_ids,
            ):
                confirmations.append(dict(row))

    entry = step_list[0]["step_id"] if step_list else None
    return {
        "entry_step_id": entry,
        "steps": step_list,
        "branches": edges,
        "confirmations": confirmations,
        "is_dynamic": len(edges) > 0,
    }


def resolve_dynamic_steps(
    product_id: str,
    failure_mode_id: str | None,
    *,
    max_steps: int = 6,
) -> list[dict[str, Any]]:
    """
    Walk diagnostic tree preferring CONFIRMS path to target failure mode.
    Falls back to product-ordered steps when no tree exists.
    """
    tree = get_diagnostic_tree(product_id)
    if not tree["is_dynamic"] or not failure_mode_id:
        from graph.graph_rag import get_diagnostic_steps_for_failure_mode

        return get_diagnostic_steps_for_failure_mode(product_id, failure_mode_id or "")

    confirm_map: dict[str, list[str]] = {}
    for c in tree["confirmations"]:
        confirm_map.setdefault(c["step_id"], []).append(c["failure_mode_id"])

    branch_map = {e["from_step_id"]: e for e in tree["branches"]}
    steps_by_id = {s["step_id"]: s for s in tree["steps"]}

    ordered: list[dict[str, Any]] = []
    current = tree["entry_step_id"]
    visited: set[str] = set()

    while current and current not in visited and len(ordered) < max_steps:
        visited.add(current)
        step = steps_by_id.get(current)
        if step:
            confirms = confirm_map.get(current, [])
            step = {
                **step,
                "confirms_failure_modes": confirms,
                "targets_top_fm": failure_mode_id in confirms,
            }
            ordered.append(step)

        branch = branch_map.get(current)
        if not branch:
            break
        current = branch["to_step_id"]

    if not ordered:
        from graph.graph_rag import get_diagnostic_steps_for_failure_mode

        return get_diagnostic_steps_for_failure_mode(product_id, failure_mode_id)

    return ordered