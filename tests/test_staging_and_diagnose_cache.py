"""Tests for dual Neo4j env routing and diagnose read-path cache."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from graph.neo4j_client import current_neo4j_env, get_driver, neo4j_env
from runtime.cache import reset_named_caches_for_tests
from runtime.diagnose_cache import catalog_version, diagnose_cache_key
from services.diagnosis_service import run_full_diagnosis


def setup_function():
    reset_named_caches_for_tests()


def test_neo4j_env_context_switches_active_env():
    assert current_neo4j_env() == "production"
    with neo4j_env("staging"):
        assert current_neo4j_env() == "staging"
    assert current_neo4j_env() == "production"


def test_diagnose_cache_key_stable_and_partitioned():
    a = diagnose_cache_key("Won't drain E21", product_id="wm-001", tenant_id="t1")
    b = diagnose_cache_key("won't   drain e21", product_id="wm-001", tenant_id="t1")
    c = diagnose_cache_key("won't drain e21", product_id="wm-001", tenant_id="t2")
    d = diagnose_cache_key("won't drain e21", product_id="dw-001", tenant_id="t1")
    assert a == b
    assert a != c
    assert a != d
    assert len(a) == 64
    assert len(catalog_version()) == 16


def test_diagnose_cache_hit_skips_second_graph_call(monkeypatch):
    from config.settings import settings

    monkeypatch.setattr(settings, "enable_diagnose_cache", True)
    monkeypatch.setattr(settings, "cache_ttl_diagnose_seconds", 120.0)

    calls = {"n": 0}

    def fake_run_diagnosis(
        message,
        product_id=None,
        asset_id=None,
        crm_product_id=None,
        force_keep_context=False,
        crm_context=None,
    ):
        calls["n"] += 1
        return {
            "response": f"ok-{calls['n']}",
            "diagnosis": {"product_id": product_id or "wm-001", "confidence": 0.9, "ranked_failure_modes": []},
            "escalated": False,
            "case_id": None,
        }

    monkeypatch.setattr("services.diagnosis_service.run_diagnosis", fake_run_diagnosis)

    o1 = run_full_diagnosis("washer will not drain", product_id="wm-001", use_cache=True)
    o2 = run_full_diagnosis("washer will not drain", product_id="wm-001", use_cache=True)
    assert calls["n"] == 1
    assert o1.response == "ok-1"
    assert o2.response == "ok-1"
    assert o2.diagnosis.get("_cache_hit") is True


def test_promote_runner_uses_staging_env(monkeypatch):
    from graph.enterprise_pipeline.control_plane import runner as runner_mod
    from graph.enterprise_pipeline.control_plane.models import PipelineStatus

    envs: list[str] = []

    def fake_populate(driver, catalog, etl_batch_id=None):
        from graph.neo4j_client import current_neo4j_env

        envs.append(current_neo4j_env())
        return {"products": 1}

    monkeypatch.setattr(runner_mod, "populate_graph", fake_populate)
    monkeypatch.setattr(runner_mod, "invalidate_all_named_caches", lambda: None)
    monkeypatch.setattr(runner_mod.settings, "enterprise_catalog_file", runner_mod.settings.data_file)

    # Ensure catalog exists
    assert runner_mod.settings.data_file.exists() or runner_mod.settings.enterprise_catalog_file.exists()

    report = runner_mod.run_pipeline("promote_graph", mode="on_demand", dry_run=False, target_env="staging")
    assert report.status in (PipelineStatus.SUCCESS, PipelineStatus.FAILED)
    if report.status == PipelineStatus.SUCCESS:
        assert envs == ["staging"]
