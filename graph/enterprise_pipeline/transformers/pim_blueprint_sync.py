"""
Sync enterprise OEM product blueprints into the PIM fixture for ETL ingestion.

Run: python -m graph.enterprise_pipeline.transformers.pim_blueprint_sync
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config.settings import settings
from graph.oem_product_catalog import build_oem_enterprise_catalog


def sync_pim_fixture(
    target: Path | None = None,
    *,
    write_enterprise_catalog: bool = True,
) -> dict:
    """
    Export full OEM enterprise catalog to PIM fixture (and optionally enterprise catalog).
    Returns summary stats.
    """
    catalog = build_oem_enterprise_catalog()
    target = target or settings.enterprise_sources_dir / "pim_catalog.json"

    pim_payload = {
        "source_system": "SAP PLM / PIM (OEM blueprint sync)",
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "catalog_metadata": catalog.get("catalog_metadata", {}),
        "products": catalog["products"],
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(pim_payload, indent=2), encoding="utf-8")

    if write_enterprise_catalog:
        ent_path = settings.enterprise_catalog_file
        ent_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    return {
        "pim_fixture": str(target),
        "product_count": len(catalog["products"]),
        "oem_product_count": catalog.get("catalog_metadata", {}).get("oem_product_count", 0),
        "assets": len(catalog.get("assets", [])),
        "claims": len(catalog.get("claims", [])),
    }


if __name__ == "__main__":
    stats = sync_pim_fixture()
    print(f"✅ PIM sync complete: {stats}")