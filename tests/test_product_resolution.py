"""Product resolution — asset-first + soft mismatch (production-shaped)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.graph_rag import (  # noqa: E402
    _composite_confidence,
    _text_similarity,
    detect_product,
    diagnose,
    resolve_product_for_diagnosis,
)
from integrations.crm_enrichment import (  # noqa: E402
    _build_enrichment,
    list_crm_customers,
    list_customer_assets,
)


def test_detect_product_dishwasher_message() -> None:
    product = detect_product("Dishwasher leaves dishes wet and cold after the cycle")
    assert product is not None
    assert product["product_id"] == "dw-001"


def test_dishwasher_symptom_matches_dishwasher_message() -> None:
    score = _text_similarity(
        "Dishwasher leaves dishes wet and cold after the cycle",
        "Dishes come out wet and cold",
    )
    assert score >= 0.30


def test_composite_confidence_separates_posterior_and_language() -> None:
    ranked = [
        {
            "failure_mode_id": "dw-fm01",
            "posterior": 0.82,
            "indications": [{"symptom_id": "dw-s01", "confidence": 0.94}],
        }
    ]
    strong = [{"symptom_id": "dw-s01", "match_score": 0.85}]
    weak = [{"symptom_id": "dw-s01", "match_score": 0.44}]
    strong_overall, strong_graph, strong_lang, strong_strength, _ = _composite_confidence(ranked, strong)
    weak_overall, _, weak_lang, _, _ = _composite_confidence(ranked, weak)
    assert strong_overall == weak_overall
    assert strong_graph == 0.94
    assert strong_lang > weak_lang
    assert strong_strength in {"Strong", "Moderate", "Weak", "Insufficient data"}


def test_crm_list_customers_and_assets() -> None:
    customers = list_crm_customers()
    assert any(c["customer_id"] == "CUST-10042" for c in customers)
    data = list_customer_assets("CUST-10042")
    assert data["customer"]["name"] == "Jane Martinez"
    assert any(a["product_id"] == "wm-001" for a in data["registered_assets"])


def test_asset_first_product_from_crm_ignores_client_product_match() -> None:
    """When asset is bound, product is the asset product."""
    crm = {
        "enriched": True,
        "asset_id": "AST-WM-4421",
        "product_id": "wm-001",
        "sku_id": "SKU-WM8K-2023",
        "model_number": "AH-WM8K",
        "serial_number": "AH-WM8K-2023-99421",
        "customer_id": "CUST-10042",
    }
    product, asset_ctx, effective_asset_id, warnings, block_code, meta = resolve_product_for_diagnosis(
        "won't spin and water stays in the drum",
        product_id=None,
        asset_id="AST-WM-4421",
        crm_product_id="wm-001",
        crm_context=crm,
    )
    assert block_code == ""
    assert product is not None
    assert product["product_id"] == "wm-001"
    assert meta.get("session") == "identified"
    assert effective_asset_id == "AST-WM-4421"
    assert asset_ctx is not None


def test_soft_mismatch_washer_asset_dishwasher_text() -> None:
    crm = {
        "enriched": True,
        "asset_id": "AST-WM-4421",
        "product_id": "wm-001",
        "customer_id": "CUST-10042",
        "model_number": "AH-WM8K",
        "serial_number": "x",
    }
    product, asset_ctx, effective_asset_id, warnings, block_code, meta = resolve_product_for_diagnosis(
        "Dishwasher leaves dishes wet and cold after the cycle",
        product_id=None,
        asset_id="AST-WM-4421",
        crm_product_id="wm-001",
        crm_context=crm,
    )
    assert block_code == "soft_appliance_mismatch"
    assert meta.get("can_force_keep") is True
    assert meta.get("suggested_product_id") == "dw-001"
    assert product is not None and product["product_id"] == "wm-001"
    assert effective_asset_id == "AST-WM-4421"
    assert warnings


def test_force_keep_allows_diagnose_on_bound_asset() -> None:
    crm = {
        "enriched": True,
        "asset_id": "AST-WM-4421",
        "product_id": "wm-001",
        "customer_id": "CUST-10042",
        "model_number": "AH-WM8K",
        "serial_number": "x",
    }
    product, _, _, warnings, block_code, _ = resolve_product_for_diagnosis(
        "Dishwasher leaves dishes wet and cold after the cycle",
        product_id=None,
        asset_id="AST-WM-4421",
        crm_product_id="wm-001",
        force_keep_context=True,
        crm_context=crm,
    )
    assert block_code == ""
    assert product is not None and product["product_id"] == "wm-001"
    assert warnings  # operator confirmed warning


def test_api_invariant_client_product_vs_asset() -> None:
    crm = {
        "enriched": True,
        "asset_id": "AST-WM-4421",
        "product_id": "wm-001",
        "customer_id": "CUST-10042",
    }
    _, _, _, warnings, block_code, _ = resolve_product_for_diagnosis(
        "won't spin",
        product_id="dw-001",  # illegal override
        asset_id="AST-WM-4421",
        crm_product_id="wm-001",
        crm_context=crm,
    )
    assert block_code == "product_asset_conflict"
    assert warnings


def test_diagnose_asset_first_aligned() -> None:
    try:
        from graph.neo4j_client import verify_connection
    except Exception:
        return
    if not verify_connection():
        return
    crm = {
        "enriched": True,
        "asset_id": "AST-DW-1180",
        "product_id": "dw-001",
        "customer_id": "CUST-10087",
        "model_number": "CW-DW12",
        "serial_number": "CW-DW12-2022-33180",
        "sku_id": "SKU-DW12-2022",
    }
    result = diagnose(
        "Dishwasher leaves dishes wet and cold after the cycle",
        product_id=None,
        asset_id="AST-DW-1180",
        crm_product_id="dw-001",
        crm_context=crm,
    )
    assert result.context_blocked is False
    assert result.product_id == "dw-001"
    assert result.ranked_failure_modes
    assert all(int(fm.get("link_count") or 0) > 0 for fm in result.ranked_failure_modes)


def test_diagnose_soft_block_then_force() -> None:
    try:
        from graph.neo4j_client import verify_connection
    except Exception:
        return
    if not verify_connection():
        return
    crm = {
        "enriched": True,
        "asset_id": "AST-WM-4421",
        "product_id": "wm-001",
        "customer_id": "CUST-10042",
        "model_number": "AH-WM8K",
        "serial_number": "x",
    }
    msg = "Dishwasher leaves dishes wet and cold after the cycle"
    blocked = diagnose(msg, asset_id="AST-WM-4421", crm_product_id="wm-001", crm_context=crm)
    assert blocked.context_blocked is True
    assert blocked.context_block_code == "soft_appliance_mismatch"
    forced = diagnose(
        msg,
        asset_id="AST-WM-4421",
        crm_product_id="wm-001",
        force_keep_context=True,
        crm_context=crm,
    )
    assert forced.context_blocked is False
    assert forced.product_id == "wm-001"


def test_crm_customer_asset_mismatch_warning() -> None:
    payload = _build_enrichment(
        customer={"customer_id": "CUST-10042", "name": "Jane Martinez"},
        asset={
            "asset_id": "AST-MW-7702",
            "customer_id": "CUST-10042",
            "product_id": "mw-001",
        },
        requested_customer_id="CUST-10120",
        source_record_id="AST-MW-7702",
    )
    assert payload["customer_id"] == "CUST-10042"
    assert payload["customer_asset_mismatch"] is True
