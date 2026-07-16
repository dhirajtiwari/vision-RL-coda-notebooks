"""
Weighted "cheapest diagnostic route" over the knowledge graph.

Industry practice (see docs/25 + the Scaling & Populating KG guide): the
*fastest* path (fewest hops) and the *cheapest* path (least uncertainty /
technician time / part cost) are frequently different. This module answers the
weighted question — "what is the lowest-cost route from a Symptom to a
confirming DiagnosticStep (or Part)?" — using two tiers:

1. **APOC weighted Dijkstra** (``apoc.algo.dijkstra``) — the APOC plugin is
   already loaded in this project's Neo4j image, so no GDS install is required.
   Runs on a ``cost`` relationship property.
2. **Native Cypher ``shortestPath()``** — unweighted (fewest hops) fallback used
   automatically when APOC is unavailable, so the endpoint always answers.

Cost model (``ensure_route_costs``): each edge gets a ``cost`` derived from its
existing evidence so a *more certain* / *cheaper* route wins:

* ``INDICATES``     cost = 1 - confidence      (uncertainty of the link)
* ``CONFIRMS``      cost = 1 - confidence      (detection effort inverse)
* ``NEXT_STEP``     cost = 1.0                 (one unit of technician effort)
* ``REQUIRES_PART`` cost = 1 - probability     (likelihood the part is needed)

This is [AS-BUILT] runnable code. Cluster/GDS Delta-Stepping remain [REFERENCE]
(see ``docs/sdd/10-SCALING-POPULATING-KG.md``).
"""

from __future__ import annotations

from typing import Any, Literal

from graph.neo4j_client import get_driver

TargetKind = Literal["step", "part"]

# Relationship types that make up a diagnostic route, with the direction used by
# APOC's dijkstra spec string ("TYPE>" = outgoing, "TYPE<" = incoming).
_ROUTE_RELS_APOC = "INDICATES>|CONFIRMS<|NEXT_STEP>|REQUIRES_PART>"
# Native fallback uses an undirected, bounded var-length pattern.
_ROUTE_RELS_NATIVE = "INDICATES|CONFIRMS|NEXT_STEP|REQUIRES_PART"
_MAX_HOPS = 8


def ensure_route_costs(driver=None) -> dict[str, int]:
    """Set a ``cost`` property on route relationships where missing (idempotent).

    Derives cost from existing evidence so the *cheapest* route is the most
    certain / least-effort one. Safe to call on every request — it only writes
    to edges that do not yet have a ``cost`` (``WHERE r.cost IS NULL``).
    """
    driver = driver or get_driver()
    statements = {
        "INDICATES": (
            "MATCH ()-[r:INDICATES]->() WHERE r.cost IS NULL "
            "SET r.cost = round(1.0 - coalesce(r.confidence, 0.5), 4) "
            "RETURN count(r) AS n"
        ),
        "CONFIRMS": (
            "MATCH ()-[r:CONFIRMS]->() WHERE r.cost IS NULL "
            "SET r.cost = round(1.0 - coalesce(r.confidence, 0.5), 4) "
            "RETURN count(r) AS n"
        ),
        "NEXT_STEP": ("MATCH ()-[r:NEXT_STEP]->() WHERE r.cost IS NULL " "SET r.cost = 1.0 RETURN count(r) AS n"),
        "REQUIRES_PART": (
            "MATCH ()-[r:REQUIRES_PART]->() WHERE r.cost IS NULL "
            "SET r.cost = round(1.0 - coalesce(r.probability, 0.5), 4) "
            "RETURN count(r) AS n"
        ),
    }
    updated: dict[str, int] = {}
    with driver.session() as session:
        for rel, cypher in statements.items():
            rec = session.run(cypher).single()
            updated[rel] = int(rec["n"]) if rec else 0
    return updated


def _target_ids(session, product_id: str, symptom_id: str, target_kind: TargetKind) -> list[str]:
    """Candidate target node ids reachable from the symptom's failure modes.

    Scoped to ``product_id`` when the failure mode is linked to the product, so
    a route stays inside the product neighborhood (matches the diagnose path).
    """
    if target_kind == "part":
        cypher = (
            "MATCH (s:Symptom {symptom_id: $sid})-[:INDICATES]->(fm:FailureMode)"
            "-[:REQUIRES_PART]->(pt:Part) "
            "WHERE $pid IS NULL OR (:Product {product_id: $pid})-[:CAN_HAVE]->(fm) "
            "RETURN DISTINCT pt.part_id AS id"
        )
    else:  # step
        cypher = (
            "MATCH (s:Symptom {symptom_id: $sid})-[:INDICATES]->(fm:FailureMode)"
            "<-[:CONFIRMS]-(ds:DiagnosticStep) "
            "WHERE $pid IS NULL OR (:Product {product_id: $pid})-[:CAN_HAVE]->(fm) "
            "RETURN DISTINCT ds.step_id AS id"
        )
    return [r["id"] for r in session.run(cypher, {"sid": symptom_id, "pid": product_id or None}) if r["id"]]


def _apoc_dijkstra(session, symptom_id: str, target_kind: TargetKind, target_id: str) -> dict | None:
    """One weighted source→target Dijkstra via APOC. Returns route dict or None."""
    end_match = (
        "MATCH (e:Part {part_id: $tid})" if target_kind == "part" else "MATCH (e:DiagnosticStep {step_id: $tid})"
    )
    cypher = (
        "MATCH (s:Symptom {symptom_id: $sid}) "
        f"{end_match} "
        "CALL apoc.algo.dijkstra(s, e, $rels, 'cost') "
        "YIELD path, weight "
        "RETURN weight AS total_cost, "
        "[n IN nodes(path) | {id: coalesce(n.symptom_id, n.failure_mode_id, "
        "n.step_id, n.part_id), label: head(labels(n)), "
        "name: coalesce(n.description, n.name, n.part_number)}] AS route"
    )
    rec = session.run(cypher, {"sid": symptom_id, "tid": target_id, "rels": _ROUTE_RELS_APOC}).single()
    if not rec or rec["route"] is None:
        return None
    return {"total_cost": float(rec["total_cost"]), "route": rec["route"], "target_id": target_id}


def _native_shortest(session, symptom_id: str, target_kind: TargetKind, target_id: str) -> dict | None:
    """Unweighted native shortestPath() fallback (fewest hops)."""
    end_match = (
        "MATCH (e:Part {part_id: $tid})" if target_kind == "part" else "MATCH (e:DiagnosticStep {step_id: $tid})"
    )
    cypher = (
        "MATCH (s:Symptom {symptom_id: $sid}) "
        f"{end_match} "
        f"MATCH path = shortestPath((s)-[:{_ROUTE_RELS_NATIVE}*..{_MAX_HOPS}]-(e)) "
        "RETURN length(path) AS hops, "
        "[n IN nodes(path) | {id: coalesce(n.symptom_id, n.failure_mode_id, "
        "n.step_id, n.part_id), label: head(labels(n)), "
        "name: coalesce(n.description, n.name, n.part_number)}] AS route"
    )
    rec = session.run(cypher, {"sid": symptom_id, "tid": target_id}).single()
    if not rec or rec["route"] is None:
        return None
    return {"hops": int(rec["hops"]), "route": rec["route"], "target_id": target_id}


def _best_route(session, symptom_id, target_kind, targets, finder, key) -> dict | None:
    """Run ``finder`` for each candidate target; keep the minimum ``key``.

    Returns None if the finder raises (e.g. APOC missing) so the caller can
    fall back to the next tier.
    """
    best: dict | None = None
    try:
        for tid in targets:
            cand = finder(session, symptom_id, target_kind, tid)
            if cand and (best is None or cand[key] < best[key]):
                best = cand
    except Exception:
        return None
    return best


def cheapest_diagnostic_route(
    product_id: str,
    symptom_id: str,
    target_kind: TargetKind = "step",
    driver=None,
) -> dict[str, Any]:
    """Cheapest weighted route from a Symptom to a confirming step (or part).

    Tries APOC weighted Dijkstra across all candidate targets and returns the
    lowest total cost. Falls back to native ``shortestPath()`` (fewest hops)
    when APOC is unavailable. Returns a JSON-serializable dict describing the
    route, its cost/hops, and which method produced it.
    """
    driver = driver or get_driver()
    ensure_route_costs(driver)

    with driver.session() as session:
        targets = _target_ids(session, product_id, symptom_id, target_kind)
        if not targets:
            return {
                "found": False,
                "method": "none",
                "reason": f"no reachable {target_kind} target from symptom {symptom_id}",
                "product_id": product_id,
                "symptom_id": symptom_id,
                "target_kind": target_kind,
            }

        # Tier 1: APOC weighted Dijkstra — pick the cheapest across candidates.
        best = _best_route(session, symptom_id, target_kind, targets, _apoc_dijkstra, "total_cost")
        method = "apoc.algo.dijkstra"

        # Tier 2: native shortestPath() fallback (fewest hops).
        if best is None:
            method = "shortestPath"
            best = _best_route(session, symptom_id, target_kind, targets, _native_shortest, "hops")

        if best is None:
            return {
                "found": False,
                "method": method,
                "reason": "no path found",
                "product_id": product_id,
                "symptom_id": symptom_id,
                "target_kind": target_kind,
            }

        return {
            "found": True,
            "method": method,
            "weighted": method == "apoc.algo.dijkstra",
            "product_id": product_id,
            "symptom_id": symptom_id,
            "target_kind": target_kind,
            "target_id": best["target_id"],
            "total_cost": best.get("total_cost"),
            "hops": best.get("hops", len(best["route"]) - 1),
            "route": best["route"],
        }
