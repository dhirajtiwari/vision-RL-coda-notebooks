"""Unit tests for product conflict resolution and symptom matching."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.graph_rag import (  # noqa: E402
    _composite_confidence,
    _text_similarity,
    detect_product,
    resolve_product_for_diagnosis,
)
from integrations.crm_enrichment import _build_enrichment  # noqa: E402


def test_detect_product_dishwasher_message() -> None:
    product = detect_product("Dishwasher leaves dishes wet and cold after the cycle")
    assert product is not None
    assert product["product_id"] == "dw-001"


def test_microwave_symptom_does_not_match_dishwasher_message() -> None:
    score = _text_similarity(
        "Dishwasher leaves dishes wet and cold after the cycle",
        "Microwave runs but food stays cold",
    )
    assert score < 0.30


def test_dishwasher_symptom_matches_dishwasher_message() -> None:
    score = _text_similarity(
        "Dishwasher leaves dishes wet and cold after the cycle",
        "Dishes come out wet and cold",
    )
    assert score >= 0.30


def test_composite_confidence_separates_posterior_and_language() -> None:
    # Overall confidence is the Bayesian posterior of the leading failure mode
    # (engineering probability) and must NOT be diluted by language match.
    # Language match is reported as a separate, third signal.
    ranked = [{
        "failure_mode_id": "dw-fm01",
        "posterior": 0.82,
        "indications": [{"symptom_id": "dw-s01", "confidence": 0.94}],
    }]
    strong = [{"symptom_id": "dw-s01", "match_score": 0.85}]
    weak = [{"symptom_id": "dw-s01", "match_score": 0.44}]

    strong_overall, strong_graph, strong_lang = _composite_confidence(ranked, strong)
    weak_overall, _, weak_lang = _composite_confidence(ranked, weak)

    # Overall = posterior, independent of language match quality.
    assert strong_overall == weak_overall == 0.82
    # Strongest engineering indication for the top failure mode is surfaced.
    assert strong_graph == 0.94
    # Language signal alone tracks the retrieval match score.
    assert strong_lang > weak_lang


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
    assert payload["warnings"]


def test_resolve_product_prefers_message_over_asset_product() -> None:
    try:
        from graph.neo4j_client import verify_connection
    except Exception:
        return
    if not verify_connection():
        return

    product, asset_ctx, effective_asset_id, warnings = resolve_product_for_diagnosis(
        "Dishwasher leaves dishes wet and cold after the cycle",
        product_id="mw-001",
        asset_id="AST-MW-7702",
    )
    assert product is not None
    assert product["product_id"] == "dw-001"
    assert effective_asset_id is None
    assert asset_ctx is None
    assert warnings


if __name__ == "__main__":
    tests = [
        test_detect_product_dishwasher_message,
        test_microwave_symptom_does_not_match_dishwasher_message,
        test_dishwasher_symptom_matches_dishwasher_message,
        test_composite_confidence_scales_with_match_score,
        test_crm_customer_asset_mismatch_warning,
        test_resolve_product_prefers_message_over_asset_product,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {test.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)