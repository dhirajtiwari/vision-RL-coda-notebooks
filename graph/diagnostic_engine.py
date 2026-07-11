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


def get_diagnostic_steps(product_id: str) -> list[dict[str, Any]]:
    """All ordered diagnostic steps for a product (product-level fallback)."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
            RETURN ds.step_id AS step_id, ds.description AS description,
                   ds.order AS step_order, ds.expected_outcome AS expected_outcome,
                   ds.source_system AS source_system,
                   ds.source_document_uri AS source_document_uri
            ORDER BY ds.order
        """,
            product_id=product_id,
        )
        return [dict(r) for r in result]


def get_diagnostic_steps_for_failure_mode(
    product_id: str,
    failure_mode_id: str,
) -> list[dict[str, Any]]:
    """
    Steps targeted to a failure mode via CONFIRMS, plus true prerequisites only.

    Includes:
      - steps that CONFIRMS the target failure mode
      - earlier steps that CONFIRMS *no* failure mode (shared entry checks)

    Does **not** include steps that only CONFIRMS a *different* failure mode
    (e.g. ice-maker checks when top FM is defrost heater).

    Falls back to all product steps when no CONFIRMS edge exists for the FM.
    """
    driver = get_driver()
    with driver.session() as session:
        all_steps = [
            dict(r)
            for r in session.run(
                """
                MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                RETURN ds.step_id AS step_id, ds.description AS description,
                       ds.order AS step_order, ds.expected_outcome AS expected_outcome,
                       ds.source_system AS source_system,
                       ds.source_document_uri AS source_document_uri
                ORDER BY ds.order
            """,
                product_id=product_id,
            )
        ]
        # step_id -> set of FM ids it confirms
        confirms_by_step: dict[str, set[str]] = {}
        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
            MATCH (ds)-[:CONFIRMS]->(fm:FailureMode)
            RETURN ds.step_id AS step_id, fm.failure_mode_id AS failure_mode_id
            """,
            product_id=product_id,
        ):
            confirms_by_step.setdefault(row["step_id"], set()).add(row["failure_mode_id"])

        confirming_ids = {sid for sid, fms in confirms_by_step.items() if failure_mode_id in fms}

    if not confirming_ids:
        return all_steps

    confirming_orders = [
        s["step_order"] for s in all_steps if s["step_id"] in confirming_ids and s.get("step_order") is not None
    ]
    min_confirm_order = min(confirming_orders) if confirming_orders else None

    targeted: list[dict[str, Any]] = []
    for step in all_steps:
        sid = step["step_id"]
        fms = confirms_by_step.get(sid) or set()
        if failure_mode_id in fms:
            targeted.append({**step, "targets_top_fm": True, "confirms_failure_modes": list(fms)})
            continue
        # Shared prerequisites: no CONFIRMS to any FM, and not after the confirming step
        if not fms and min_confirm_order is not None:
            order = step.get("step_order")
            if order is None or order <= min_confirm_order:
                targeted.append(
                    {**step, "targets_top_fm": False, "confirms_failure_modes": [], "is_prerequisite": True}
                )
        # Explicitly skip steps that only confirm other FMs

    return targeted if targeted else all_steps


def resolve_dynamic_steps(
    product_id: str,
    failure_mode_id: str | None,
    *,
    max_steps: int = 6,
) -> list[dict[str, Any]]:
    """
    Resolve troubleshooting steps for a top failure mode.

    Prefer CONFIRMS-targeted steps (+ shared prerequisites). Linear NEXT_STEP
    chains that only encode a generic sequence are **not** used as a substitute
    for FM targeting (they incorrectly pull in checks for other FMs).

    Tree walk is used only when it actually lands on a step that CONFIRMS the
    target FM and no better CONFIRMS set exists.
    """
    if not failure_mode_id:
        return get_diagnostic_steps(product_id)[:max_steps]

    targeted = get_diagnostic_steps_for_failure_mode(product_id, failure_mode_id)
    if any(s.get("targets_top_fm") for s in targeted):
        return targeted[:max_steps]

    tree = get_diagnostic_tree(product_id)
    if not tree["is_dynamic"]:
        return targeted[:max_steps] if targeted else get_diagnostic_steps(product_id)[:max_steps]

    confirm_map: dict[str, list[str]] = {}
    for c in tree["confirmations"]:
        confirm_map.setdefault(c["step_id"], []).append(c["failure_mode_id"])

    # If the tree has no step confirming this FM, stay with product-order fallback
    if failure_mode_id not in {fm for fms in confirm_map.values() for fm in fms}:
        return targeted[:max_steps] if targeted else get_diagnostic_steps(product_id)[:max_steps]

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
            ordered.append(
                {
                    **step,
                    "confirms_failure_modes": confirms,
                    "targets_top_fm": failure_mode_id in confirms,
                }
            )
            # Stop once we reach a step that confirms the top FM
            if failure_mode_id in confirms:
                break

        branch = branch_map.get(current)
        if not branch:
            break
        current = branch["to_step_id"]

    # Drop steps that only confirm other FMs (keep prereqs + target)
    cleaned = [
        s
        for s in ordered
        if s.get("targets_top_fm")
        or not s.get("confirms_failure_modes")
        or failure_mode_id in (s.get("confirms_failure_modes") or [])
    ]
    if any(s.get("targets_top_fm") for s in cleaned):
        return cleaned[:max_steps]

    return targeted[:max_steps] if targeted else get_diagnostic_steps(product_id)[:max_steps]
