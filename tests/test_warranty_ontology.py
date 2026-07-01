"""Tests for enterprise warranty ontology extensions."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.warranty_catalog_extensions import (
    PRODUCT_EXTENSIONS,
    build_enterprise_catalog_payload,
    resolve_sku_from_serial,
)


def test_all_products_have_bom_chain():
    for pid, ext in PRODUCT_EXTENSIONS.items():
        assert ext.get("model"), f"{pid} missing model"
        assert ext.get("components"), f"{pid} missing components"
        assert ext.get("failure_mode_component_links"), f"{pid} missing FM→component"
        assert ext.get("diagnostic_step_failure_links"), f"{pid} missing step→FM"
        assert ext.get("failure_mode_part_links"), f"{pid} missing parts predictor links"


def test_serial_resolves_to_sku():
    assert resolve_sku_from_serial("AH-WM8K-2023-99421") == "SKU-WM8K-2023"
    assert resolve_sku_from_serial("CW-DW12-2022-33180") == "SKU-DW12-2022"


def test_enterprise_catalog_includes_assets_and_claims():
    payload = build_enterprise_catalog_payload([{"product": {"product_id": "wm-001"}}])
    assert payload.get("assets")
    assert payload.get("claims")
    assert payload.get("warranty_policies")
    wm = next(p for p in payload["products"] if p["product"]["product_id"] == "wm-001")
    assert wm.get("error_codes")


if __name__ == "__main__":
    test_all_products_have_bom_chain()
    test_serial_resolves_to_sku()
    test_enterprise_catalog_includes_assets_and_claims()
    print("PASS: warranty ontology")
