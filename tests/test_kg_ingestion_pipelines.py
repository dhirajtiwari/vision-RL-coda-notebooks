"""Tests for multi-source KG ingestion control plane."""

from __future__ import annotations

from pathlib import Path

from graph.enterprise_pipeline.control_plane.registry import get_pipeline, list_pipelines
from graph.enterprise_pipeline.control_plane.runner import run_pipeline, sources_root
from graph.enterprise_pipeline.extractors.semi_structured import ingest_semi_structured_dir
from graph.enterprise_pipeline.extractors.unstructured_text import extract_from_text, ingest_unstructured_dir
from graph.enterprise_pipeline.preprocess.normalize import preprocess_bundle


def test_registry_has_core_pipelines():
    ids = {p.id for p in list_pipelines()}
    for required in (
        "structured_extract",
        "semi_structured_ingest",
        "unstructured_extract",
        "preprocess_normalize",
        "bootstrap_all",
        "incremental_sync",
        "promote_graph",
        "smoke_validate",
    ):
        assert required in ids
    assert get_pipeline("bootstrap_all") is not None


def test_semi_structured_fixtures_load():
    root = sources_root() / "semi_structured" / "bootstrap"
    assert root.exists(), "fixture pack missing — run fixture setup"
    result = ingest_semi_structured_dir(root)
    assert result["record_count"] >= 4
    assert len(result["work_orders"]) >= 1
    assert len(result["parts"]) >= 1


def test_unstructured_extract_patterns():
    text = "Washer will not drain and shows E21. Customer reports water in drum."
    out = extract_from_text(text, doc_id="t1", product_hint="wm-001")
    assert out["product_id"] == "wm-001"
    assert "E21" in out["error_codes"] or any(s["key"] == "drain" for s in out["provisional_symptoms"])
    assert out["provisional_symptoms"]


def test_unstructured_dir_bootstrap():
    root = sources_root() / "unstructured" / "bootstrap"
    result = ingest_unstructured_dir(root)
    assert result["document_count"] >= 2
    assert result["symptom_hints"] >= 1


def test_preprocess_quality_rejects_incomplete():
    bundle = {
        "work_orders": [
            {
                "record_type": "work_order_delta",
                "product_id": "wm-001",
                "confirmed_failure_mode_id": "wm-fm02",
                "symptom_id": "wm-s03",
            },
            {"record_type": "work_order_delta", "product_id": "", "confirmed_failure_mode_id": ""},
        ],
        "parts": [{"record_type": "part_delta", "product_id": "wm-001", "part_id": "wm-p02"}],
        "documents": [],
    }
    cleaned = preprocess_bundle(bundle)
    assert cleaned["quality"]["accepted_work_orders"] == 1
    assert cleaned["quality"]["rejected"] >= 1
    assert cleaned["quality"]["pass_rate"] < 1.0


def test_run_semi_structured_dry():
    report = run_pipeline("semi_structured_ingest", mode="bootstrap", dry_run=True)
    assert report.status.value in ("success", "partial")
    assert report.stages


def test_run_unstructured_and_preprocess():
    r1 = run_pipeline("unstructured_extract", mode="bootstrap", dry_run=False)
    assert r1.status.value == "success"
    r2 = run_pipeline("semi_structured_ingest", mode="bootstrap", dry_run=False)
    assert r2.status.value == "success"
    r3 = run_pipeline("preprocess_normalize", mode="on_demand", dry_run=False)
    assert r3.status.value in ("success", "partial")
    assert any(s.name == "preprocess_quality" for s in r3.stages)


def test_run_bootstrap_all_dry():
    report = run_pipeline("bootstrap_all", mode="bootstrap", dry_run=True)
    # Chain should execute multiple sub-stages; dry-run must not fail on smoke (Neo4j optional)
    assert len(report.stages) >= 3
    assert report.pipeline_id == "bootstrap_all"
    assert report.status.value in ("success", "partial")
    assert not any(s.status.value == "failed" and "smoke" in s.name for s in report.stages)


def test_api_list_kg_pipelines():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    r = client.get("/admin/kg-pipelines")
    assert r.status_code == 200
    body = r.json()
    assert "pipelines" in body
    assert len(body["pipelines"]) >= 8


def test_api_run_semi_pipeline_dry():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    r = client.post("/admin/kg-pipelines/semi_structured_ingest/run?mode=bootstrap&dry_run=true")
    assert r.status_code == 200
    body = r.json()
    assert body["pipeline_id"] == "semi_structured_ingest"
    assert "run_id" in body
    assert body["stages"]
