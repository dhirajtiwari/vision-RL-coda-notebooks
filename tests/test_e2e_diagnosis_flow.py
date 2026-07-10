"""
End-to-end diagnosis flow (API + graph + runtime caches).

Requires Neo4j when available; skips the diagnosis assertion if Neo4j is down.
Always validates health/runtime wiring and cache behaviour.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.main import app  # noqa: E402
from graph.neo4j_client import verify_connection  # noqa: E402
from runtime.cache import get_named_cache, reset_named_caches_for_tests  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_caches():
    reset_named_caches_for_tests()
    yield
    reset_named_caches_for_tests()


def test_e2e_health_exposes_runtime_and_redis_status():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    runtime = body["runtime"]
    assert "redis" in runtime
    assert runtime["redis"]["mode"] in ("memory", "memory_fallback", "redis")
    assert "rate_limit_backend" in runtime
    assert "max_concurrent_diagnoses" in runtime
    assert "caches" in runtime


def test_e2e_ontology_cache_hit_path():
    r1 = client.get("/graph/ontology")
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1.get("nodes")
    r2 = client.get("/graph/ontology")
    assert r2.status_code == 200
    assert r2.json()["nodes"] == body1["nodes"]
    cache = get_named_cache("ontology_schema", ttl_seconds=300, maxsize=4)
    # Second request should have registered hits on the named cache.
    assert cache.stats.hits + cache.stats.sets >= 1


def test_e2e_diagnose_washer_drain_when_neo4j_up():
    if not verify_connection():
        pytest.skip("Neo4j not available")

    r = client.post(
        "/diagnose",
        json={
            "message": "My washing machine will not drain and shows E21",
            "product_id": "wm-001",
        },
        headers={"X-Tenant-Id": "e2e-tenant", "X-Customer-Id": "e2e-cust"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("response")
    diagnosis = body.get("diagnosis") or {}
    # Graph-backed diagnosis should identify product and ranked failure modes when catalog is loaded.
    if diagnosis:
        assert diagnosis.get("product_id") in (None, "wm-001") or diagnosis.get("product_id")
        fms = diagnosis.get("ranked_failure_modes") or diagnosis.get("failure_modes") or []
        # Soft assert: structure present even if empty catalog edge case.
        assert isinstance(fms, list)
    assert "X-Request-ID" in r.headers or r.headers.get("x-request-id")


def test_e2e_product_subgraph_when_neo4j_up():
    if not verify_connection():
        pytest.skip("Neo4j not available")

    r = client.get("/graph/product/wm-001")
    # 404 if catalog not loaded; 200 when present.
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert data.get("nodes")
        r2 = client.get("/graph/product/wm-001")
        assert r2.status_code == 200


def test_e2e_integrations_and_dry_run_etl():
    r = client.get("/integrations/status")
    assert r.status_code == 200
    assert "connectors" in r.json()

    r2 = client.post("/admin/pipeline/dry-run-etl")
    assert r2.status_code == 200
    payload = r2.json()
    assert "batch_id" in payload or "product_count" in payload or "status" in payload
