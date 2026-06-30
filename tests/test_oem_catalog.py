"""OEM enterprise catalog validation."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.oem_product_catalog import OEM_BLUEPRINT_BUILDERS, build_oem_enterprise_catalog


def test_oem_builder_count():
    assert len(OEM_BLUEPRINT_BUILDERS) >= 10


def test_catalog_has_oem_products_with_sources():
    catalog = build_oem_enterprise_catalog()
    oem_products = [p for p in catalog["products"] if p.get("oem_sources")]
    assert len(oem_products) >= 10
    for p in oem_products:
        assert p.get("model")
        assert p.get("components")
        assert p.get("error_codes") or p.get("symptoms")
        assert p.get("diagnostic_tree_links") or p.get("diagnostic_step_failure_links")
        assert len(p["oem_sources"]) >= 1


def test_generated_json_on_disk():
    data = json.loads((ROOT / "data" / "synthetic_diagnosis_data.json").read_text())
    assert data["catalog_metadata"]["product_count"] >= 13
    assert data["catalog_metadata"]["oem_product_count"] >= 10


def test_pim_fixture_sync():
    from graph.enterprise_pipeline.transformers.pim_blueprint_sync import sync_pim_fixture

    stats = sync_pim_fixture()
    assert stats["product_count"] >= 13
    pim = json.loads((ROOT / "data" / "enterprise_sources" / "pim_catalog.json").read_text())
    assert len(pim["products"]) >= 13


if __name__ == "__main__":
    test_oem_builder_count()
    test_catalog_has_oem_products_with_sources()
    test_generated_json_on_disk()
    test_pim_fixture_sync()
    print("PASS: OEM catalog")