"""Tests for the weighted diagnostic-route feature.

Pure-logic tests run without Neo4j. Live-graph tests skip when Neo4j is down.
"""

from __future__ import annotations

import pytest

from graph.diagnostic_path import cheapest_diagnostic_route, ensure_route_costs
from graph.neo4j_client import verify_connection

pytestmark = pytest.mark.filterwarnings("ignore")

_NEO4J_UP = verify_connection()
_needs_neo4j = pytest.mark.skipif(not _NEO4J_UP, reason="Neo4j not available")


def test_module_exports():
    assert callable(cheapest_diagnostic_route)
    assert callable(ensure_route_costs)


@_needs_neo4j
def test_ensure_route_costs_idempotent():
    first = ensure_route_costs()
    assert isinstance(first, dict)
    # second call should update 0 (costs already set)
    second = ensure_route_costs()
    assert all(v == 0 for v in second.values())


@_needs_neo4j
def test_cheapest_route_structure():
    # wm-001 is a seeded demo product; find a symptom then route.
    from graph.neo4j_client import get_driver

    with get_driver().session() as s:
        rec = s.run(
            "MATCH (p:Product {product_id:'wm-001'})-[:CAN_HAVE]->(fm:FailureMode)"
            "<-[:INDICATES]-(sym:Symptom) RETURN sym.symptom_id AS sid LIMIT 1"
        ).single()
    if not rec or not rec["sid"]:
        pytest.skip("no symptom→failure_mode path seeded for wm-001")
    result = cheapest_diagnostic_route("wm-001", rec["sid"], target_kind="step")
    assert "found" in result
    assert result["method"] in ("apoc.algo.dijkstra", "shortestPath", "none")
    if result["found"]:
        assert result["route"]
        assert result["route"][0]["label"] == "Symptom"
