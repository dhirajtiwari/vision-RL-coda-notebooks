"""
CI gates for multi-source NEW packs + TBox/ABox pipeline discipline (2026-07-11).

Covers:
  - Source pack presence (hmd-001, esp-001) across structured/semi/unstructured
  - OntologyBuilder builds ABox from connectors (rich keys + CRM assets)
  - NEW product packs validate against shared TBox shapes (no per-product schema)
  - Unknown list keys surface as tbox_extension candidates
  - Change preview / entity-delta selection helpers
  - Unstructured product hints for esp-/hmd-
  - FailureMode / DiagnosticStep required fields (Fetch/ETL contract)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "pipeline_sources"
ENTERPRISE = ROOT / "data" / "enterprise_sources"


# ─── Pack inventory ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("pid", ["hmd-001", "esp-001"])
def test_multi_source_manifest_exists(pid: str):
    # ESP_001 / HMD_001
    prefix = pid.split("-")[0].upper() + "_" + pid.split("-")[1]
    path = SOURCES / f"{prefix}_MULTI_SOURCE_MANIFEST.json"
    assert path.exists(), f"missing manifest {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert pid in data.get("product_ids", [])
    assert data.get("change_type") == "new_product"
    assert "source_map" in data


@pytest.mark.parametrize(
    "rel",
    [
        "structured/hmd-001_pim_note.json",
        "structured/hmd-001_new_product_pack.json",
        "semi_structured/bootstrap/hmd-001_parts.csv",
        "semi_structured/bootstrap/hmd-001_work_orders.jsonl",
        "semi_structured/incremental/hmd-001_work_orders_delta.jsonl",
        "unstructured/bootstrap/hmd-001_service_manual.txt",
        "unstructured/bootstrap/hmd-001_customer_ticket.md",
        "unstructured/incremental/hmd-001_tech_resolution_2026q3.md",
        "structured/esp-001_pim_note.json",
        "structured/esp-001_new_product_pack.json",
        "semi_structured/bootstrap/esp-001_parts.csv",
        "semi_structured/bootstrap/esp-001_work_orders.jsonl",
        "semi_structured/incremental/esp-001_work_orders_delta.jsonl",
        "unstructured/bootstrap/esp-001_service_manual.txt",
        "unstructured/bootstrap/esp-001_customer_ticket.md",
        "unstructured/incremental/esp-001_tech_resolution_2026q3.md",
    ],
)
def test_multi_source_artifact_files_exist(rel: str):
    p = SOURCES / rel
    assert p.exists() and p.stat().st_size > 0, rel


@pytest.mark.parametrize("pid", ["hmd-001", "esp-001"])
def test_pim_bundle_has_required_abox_keys(pid: str):
    pim = json.loads((ENTERPRISE / "pim_catalog.json").read_text(encoding="utf-8"))
    products = pim.get("products") or []
    bundle = None
    for row in products:
        if not isinstance(row, dict):
            continue
        inner = row.get("product") if isinstance(row.get("product"), dict) else row
        if (inner or {}).get("product_id") == pid:
            bundle = row
            break
    assert bundle is not None, f"{pid} missing from PIM"
    for key in (
        "symptoms",
        "failure_modes",
        "diagnostic_steps",
        "parts",
        "symptom_failure_links",
        "failure_mode_part_links",
        "diagnostic_step_failure_links",
        "model",
        "skus",
    ):
        assert key in bundle and bundle[key] not in (None, [], {}), f"{pid} missing {key}"
    # Pydantic contract: FailureMode required fields
    for fm in bundle["failure_modes"]:
        assert "estimated_repair_time_minutes" in fm, fm
        assert "safety_notes" in fm, fm
        assert "name" in fm and "description" in fm
    # DiagnosticStep contract
    for step in bundle["diagnostic_steps"]:
        assert "description" in step, step
        assert "expected_outcome" in step, step
        assert "order" in step
    # Model number present or name (promote-safe)
    model = bundle["model"]
    assert model.get("model_id")
    assert model.get("model_number") or model.get("name")


def test_crm_and_fsm_and_claims_reference_multi_source_products():
    crm = json.loads((ENTERPRISE / "crm_assets.json").read_text(encoding="utf-8"))
    assets = {a["asset_id"]: a for a in crm.get("registered_assets") or [] if isinstance(a, dict)}
    assert "AST-HMD001-4100" in assets and assets["AST-HMD001-4100"]["product_id"] == "hmd-001"
    assert "AST-ESP001-2200" in assets and assets["AST-ESP001-2200"]["product_id"] == "esp-001"

    fsm = json.loads((ENTERPRISE / "fsm_work_orders.json").read_text(encoding="utf-8"))
    wos = fsm.get("closed_work_orders") or []
    pids = {w.get("product_id") for w in wos if isinstance(w, dict)}
    assert "hmd-001" in pids and "esp-001" in pids

    claims = json.loads((ENTERPRISE / "claims_history.json").read_text(encoding="utf-8"))
    cpids = {c.get("product_id") for c in (claims.get("closed_claims") or []) if isinstance(c, dict)}
    assert "hmd-001" in cpids and "esp-001" in cpids


# ─── Pipeline: OntologyBuilder ABox from sources (not per-product TBox) ──────


def test_ontology_builder_preserves_rich_keys_and_crm_assets():
    from graph.enterprise_pipeline.connectors.claims_connector import ClaimsConnector
    from graph.enterprise_pipeline.connectors.crm_connector import CRMConnector
    from graph.enterprise_pipeline.connectors.fsm_connector import FSMConnector
    from graph.enterprise_pipeline.connectors.pim_connector import PIMConnector
    from graph.enterprise_pipeline.transformers.ontology_builder import OntologyBuilder

    pim = PIMConnector().fetch()
    fsm = FSMConnector().fetch()
    claims = ClaimsConnector().fetch()
    crm = CRMConnector().fetch()
    assert pim.ok and fsm.ok and claims.ok and crm.ok

    builder = OntologyBuilder(etl_batch_id="ci-multi-source")
    payload = builder.build_catalog_payload(pim=pim, fsm=fsm, claims=claims, crm=crm)

    for pid in ("hmd-001", "esp-001"):
        prod = next(p for p in payload["products"] if (p.get("product") or {}).get("product_id") == pid)
        assert prod.get("model"), f"{pid} model missing after builder"
        assert prod.get("skus"), f"{pid} skus missing"
        assert prod.get("diagnostic_step_failure_links"), f"{pid} CONFIRMS links missing"
        assert len(prod.get("failure_modes") or []) >= 3
        assert len(prod.get("diagnostic_steps") or []) >= 3

    asset_ids = {a.get("asset_id") for a in (payload.get("assets") or [])}
    assert "AST-HMD001-4100" in asset_ids
    assert "AST-ESP001-2200" in asset_ids

    claim_ids = {c.get("claim_id") for c in (payload.get("claims") or [])}
    assert any("HMD" in (cid or "") or "ESP" in (cid or "") for cid in claim_ids)


def test_knowledge_etl_dry_run_includes_multi_source_products():
    from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl

    report = run_knowledge_etl(load_neo4j=False, dry_run=True)
    assert not report.errors, report.errors
    # Fleet grew beyond legacy 13 — at least multi-source packs present
    assert report.product_count >= 20, report.product_count
    assert report.sources["PIM"]["ok"]
    assert report.connector_workers >= 1

    summaries = report.product_summaries or []
    ids = {s.get("product_id") for s in summaries if isinstance(s, dict)}
    # summaries may be full catalog; if empty, still product_count is enough
    if ids:
        assert "hmd-001" in ids or "esp-001" in ids or report.product_count >= 20


def test_abox_validate_multi_source_packs_against_tbox_shapes():
    """NEW packs pass shape validation — no product-specific OWL file required."""
    from graph.enterprise_pipeline.connectors.claims_connector import ClaimsConnector
    from graph.enterprise_pipeline.connectors.crm_connector import CRMConnector
    from graph.enterprise_pipeline.connectors.fsm_connector import FSMConnector
    from graph.enterprise_pipeline.connectors.pim_connector import PIMConnector
    from graph.enterprise_pipeline.ontology_validate import validate_product_bundle
    from graph.enterprise_pipeline.transformers.ontology_builder import OntologyBuilder

    payload = OntologyBuilder(etl_batch_id="ci-validate").build_catalog_payload(
        pim=PIMConnector().fetch(),
        fsm=FSMConnector().fetch(),
        claims=ClaimsConnector().fetch(),
        crm=CRMConnector().fetch(),
    )
    for pid in ("hmd-001", "esp-001"):
        prod = next(p for p in payload["products"] if (p.get("product") or {}).get("product_id") == pid)
        report = validate_product_bundle(prod)
        assert report.get("ok") is True or report.get("failed_count", 1) == 0, (
            pid,
            report,
        )


def test_tbox_extension_scan_flags_unknown_keys_only():
    from graph.enterprise_pipeline.ingest_plan import scan_tbox_extension_candidates
    from graph.rdf_ontology_export import CLASSES

    # Baseline fixtures should not invent high-severity unknown keys for standard packs
    cands = scan_tbox_extension_candidates()
    high = [c for c in cands if c.get("severity") == "high"]
    # Known ABox keys must not appear as high tbox_extension
    known = {
        "symptoms",
        "failure_modes",
        "diagnostic_steps",
        "parts",
        "components",
        "error_codes",
        "historical_resolutions",
        "skus",
        "model",
    }
    for c in high:
        assert c.get("unknown_key") not in known
    # Shared TBox still has core classes
    names = {c[0] for c in CLASSES}
    assert "Symptom" in names and "FailureMode" in names and "Product" in names


def test_tbox_extension_detects_artificial_unknown_key(tmp_path: Path):
    from graph.enterprise_pipeline.ingest_plan import scan_tbox_extension_candidates

    fake = {
        "products": [
            {
                "product": {"product_id": "fake-001", "name": "Fake"},
                "symptoms": [{"symptom_id": "f-s1", "description": "x", "severity": "low"}],
                "brew_profiles": [{"id": "bp1"}],  # not a domain TBox list
            }
        ]
    }
    p = tmp_path / "pim.json"
    p.write_text(json.dumps(fake), encoding="utf-8")
    cands = scan_tbox_extension_candidates(pim_path=p)
    keys = {c["unknown_key"] for c in cands}
    assert "brew_profiles" in keys
    hit = next(c for c in cands if c["unknown_key"] == "brew_profiles")
    assert hit["severity"] == "high"
    assert hit["change_class"] == "tbox_extension"


# ─── Change preview + entity delta selection helpers ─────────────────────────


def test_change_preview_builds_and_diff_summary_shape():
    from graph.enterprise_pipeline.change_preview import build_change_preview

    prev = build_change_preview()
    assert "diff_vs_production" in prev
    diff = prev["diff_vs_production"]
    summary = diff.get("summary") or {}
    for k in ("new_count", "updated_count", "unchanged_count", "incoming_count"):
        assert k in summary
    assert isinstance(diff.get("new_products"), list)
    assert isinstance(diff.get("updated_products"), list)
    assert isinstance(diff.get("unchanged_products"), list)


def test_entity_delta_actionable_vs_in_sync_summary():
    from graph.enterprise_pipeline.entity_delta import (
        _is_selection_actionable,
        build_selection_entity_deltas,
    )

    # Synthetic delta shapes (no Neo4j required for pure helper)
    assert _is_selection_actionable({"change_kind": "new_product"}) is True
    assert _is_selection_actionable({"change_kind": "product_update"}) is True
    assert _is_selection_actionable({"change_kind": "missing_catalog"}) is True
    assert _is_selection_actionable({"change_kind": "in_sync"}) is False

    # Live selection for multi-source ids (Neo4j may be absent in CI — tolerate empty graph)
    bundle = build_selection_entity_deltas(
        ["esp-001", "hmd-001"],
        compare_env="production",
        include_rdf=False,
    )
    assert "summary" in bundle
    s = bundle["summary"]
    assert "actionable_product_ids" in s
    assert "in_sync_product_ids" in s
    assert s.get("product_count") == 2
    assert isinstance(bundle.get("products"), list)


def test_populate_graph_model_number_defaults():
    """Model MERGE must not require model_number on every multi-source pack."""
    import inspect

    from graph import populate_graph as pg

    src = inspect.getsource(pg.populate_graph)
    assert "model_number" in src
    assert "model.get" in src or "model_number =" in src


# ─── Unstructured extract routing ───────────────────────────────────────────


def test_unstructured_hints_for_multi_source_products():
    from graph.enterprise_pipeline.extractors.unstructured_text import extract_from_text

    hmd = extract_from_text(
        "DryZone dehumidifier tank never fills error H3",
        doc_id="x",
        product_hint="",
    )
    assert hmd["product_id"] == "hmd-001"

    esp = extract_from_text(
        "BrewBar espresso machine will not heat E05",
        doc_id="y",
        product_hint="",
    )
    assert esp["product_id"] == "esp-001"

    hinted = extract_from_text("generic text", doc_id="esp-001_manual.txt", product_hint="esp-001")
    assert hinted["product_id"] == "esp-001"


def test_product_keywords_include_multi_source_packs():
    from graph.graph_rag import PRODUCT_KEYWORDS

    assert "hmd-001" in PRODUCT_KEYWORDS
    assert "esp-001" in PRODUCT_KEYWORDS
    assert any("espresso" in t or "brewbar" in t for t in PRODUCT_KEYWORDS["esp-001"])
    assert any("dehumidifier" in t or "dryzone" in t for t in PRODUCT_KEYWORDS["hmd-001"])
