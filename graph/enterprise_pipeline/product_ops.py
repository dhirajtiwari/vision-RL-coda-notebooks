"""
Product & warranty registration operations for the knowledge platform.

These bridge realistic business events into catalog + Neo4j:

  - bulk_upsert_products: add/update product ontology bundles (PIM-shaped)
  - register_warranty_asset: customer purchased / registered a warranty unit

They compose existing OntologyBuilder / populate_graph paths rather than a
separate OWL reasoner. RDF/OWL remains an *export* (graph.rdf_ontology_export).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.settings import settings
from graph.neo4j_client import get_driver, neo4j_env
from graph.populate_graph import populate_graph
from runtime.cache import invalidate_all_named_caches
from utils.logger import get_logger

logger = get_logger(__name__)


def _catalog_path() -> Path:
    return Path(settings.enterprise_catalog_file)


def _load_catalog() -> dict[str, Any]:
    path = _catalog_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    # fall back to synthetic seed
    seed = Path(settings.data_file)
    if seed.exists():
        return json.loads(seed.read_text(encoding="utf-8"))
    return {"products": []}


def _save_catalog(catalog: dict[str, Any]) -> None:
    path = _catalog_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    catalog["catalog_metadata"] = {
        **(catalog.get("catalog_metadata") or {}),
        "updated_at": datetime.now(UTC).isoformat(),
        "source": "product_ops",
    }
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def _product_index(catalog: dict[str, Any]) -> dict[str, int]:
    idx: dict[str, int] = {}
    for i, entry in enumerate(catalog.get("products") or []):
        prod = entry.get("product") or entry
        pid = prod.get("product_id")
        if pid:
            idx[pid] = i
    return idx


def bulk_upsert_products(
    product_entries: list[dict[str, Any]],
    *,
    promote_neo4j: bool = True,
    target_env: str = "staging",
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Bulk add or update products in the enterprise catalog.

    Each entry should be either a full catalog bundle::

        {"product": {...}, "symptoms": [...], "failure_modes": [...], ...}

    or a minimal product dict with ``product_id`` + ``name`` (merged onto existing
    or created as a thin product shell).
    """
    if not product_entries:
        return {"ok": False, "error": "no products provided", "created": [], "updated": []}

    catalog = _load_catalog()
    products = list(catalog.get("products") or [])
    index = _product_index(catalog)
    created: list[str] = []
    updated: list[str] = []
    errors: list[str] = []

    for raw in product_entries:
        if not isinstance(raw, dict):
            errors.append("skip non-object entry")
            continue
        if "product" in raw:
            entry = raw
            prod = entry.get("product") or {}
        else:
            prod = raw
            entry = {
                "product": prod,
                "symptoms": raw.get("symptoms") or [],
                "failure_modes": raw.get("failure_modes") or [],
                "diagnostic_steps": raw.get("diagnostic_steps") or [],
                "parts": raw.get("parts") or [],
                "symptom_failure_links": raw.get("symptom_failure_links") or [],
                "failure_mode_part_links": raw.get("failure_mode_part_links") or [],
            }
        pid = prod.get("product_id")
        if not pid or not prod.get("name"):
            errors.append(f"missing product_id/name: {pid!r}")
            continue
        if pid in index:
            # Deep-ish merge: replace entry but preserve empty sections from previous
            prev = products[index[pid]]
            merged = {**prev, **entry, "product": {**(prev.get("product") or {}), **prod}}
            for key in (
                "symptoms",
                "failure_modes",
                "diagnostic_steps",
                "parts",
                "symptom_failure_links",
                "failure_mode_part_links",
                "components",
                "error_codes",
            ):
                if not merged.get(key) and prev.get(key):
                    merged[key] = prev[key]
            products[index[pid]] = merged
            updated.append(pid)
        else:
            products.append(entry)
            index[pid] = len(products) - 1
            created.append(pid)

    catalog["products"] = products
    result: dict[str, Any] = {
        "ok": not errors or bool(created or updated),
        "created": created,
        "updated": updated,
        "errors": errors,
        "product_count": len(products),
        "dry_run": dry_run,
        "promote_neo4j": promote_neo4j,
        "target_env": target_env,
    }

    if dry_run:
        result["message"] = "Dry-run: catalog not written; Neo4j not updated"
        return result

    _save_catalog(catalog)
    result["catalog_path"] = str(_catalog_path())

    if promote_neo4j and (created or updated):
        # Promote only the touched product bundles for speed
        touch_ids = set(created) | set(updated)
        partial = {
            "products": [e for e in products if (e.get("product") or {}).get("product_id") in touch_ids],
            "etl_batch_id": f"bulk-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        }
        env = "production" if target_env == "production" else "staging"
        try:
            with neo4j_env(env):  # type: ignore[arg-type]
                counts = populate_graph(
                    get_driver(),
                    partial if partial["products"] else catalog,
                    etl_batch_id=partial["etl_batch_id"],
                )
            invalidate_all_named_caches()
            result["neo4j"] = {"env": env, "entity_counts": counts}
        except Exception as exc:  # noqa: BLE001
            logger.exception("bulk promote failed")
            result["neo4j_error"] = str(exc)
            result["ok"] = False

    return result


def register_warranty_asset(
    payload: dict[str, Any],
    *,
    promote_neo4j: bool = True,
    target_env: str = "production",
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Register a customer warranty purchase / installed asset.

    Expected payload fields:
      customer_id, customer_name?, asset_id, product_id, serial_number?,
      model_number?, sku_id?, purchase_date?, warranty_status?, warranty_expiry?
    """
    required = ("customer_id", "asset_id", "product_id")
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return {"ok": False, "error": f"missing fields: {', '.join(missing)}"}

    fixture = settings.enterprise_sources_dir / "crm_assets.json"
    data = (
        json.loads(fixture.read_text(encoding="utf-8"))
        if fixture.exists()
        else {
            "source_system": "CRM",
            "customers": [],
            "registered_assets": [],
        }
    )

    customers = list(data.get("customers") or [])
    assets = list(data.get("registered_assets") or [])

    if not any(c.get("customer_id") == payload["customer_id"] for c in customers):
        customers.append(
            {
                "customer_id": payload["customer_id"],
                "name": payload.get("customer_name") or payload["customer_id"],
                "email": payload.get("email") or "",
                "phone": payload.get("phone") or "",
            }
        )

    asset_row = {
        "asset_id": payload["asset_id"],
        "customer_id": payload["customer_id"],
        "product_id": payload["product_id"],
        "sku_id": payload.get("sku_id") or "",
        "model_number": payload.get("model_number") or "",
        "serial_number": payload.get("serial_number") or "",
        "purchase_date": payload.get("purchase_date") or datetime.now(UTC).date().isoformat(),
        "warranty_status": payload.get("warranty_status") or "active",
        "warranty_expiry": payload.get("warranty_expiry") or "",
    }

    existing_i = next((i for i, a in enumerate(assets) if a.get("asset_id") == asset_row["asset_id"]), None)
    if existing_i is not None:
        assets[existing_i] = {**assets[existing_i], **asset_row}
        action = "updated"
    else:
        assets.append(asset_row)
        action = "created"

    data["customers"] = customers
    data["registered_assets"] = assets

    result: dict[str, Any] = {
        "ok": True,
        "action": action,
        "asset": asset_row,
        "dry_run": dry_run,
    }

    if dry_run:
        result["message"] = "Dry-run: CRM fixture and Neo4j not written"
        return result

    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text(json.dumps(data, indent=2), encoding="utf-8")
    result["crm_fixture"] = str(fixture)

    if promote_neo4j:
        env = "production" if target_env == "production" else "staging"
        try:
            with neo4j_env(env):  # type: ignore[arg-type]
                driver = get_driver()
                with driver.session() as session:
                    session.run(
                        """
                        MERGE (a:Asset {asset_id: $asset_id})
                        SET a.serial_number = $serial_number,
                            a.model_number = $model_number,
                            a.customer_id = $customer_id,
                            a.warranty_status = $warranty_status,
                            a.warranty_expiry = $warranty_expiry,
                            a.purchase_date = $purchase_date
                        WITH a
                        MATCH (p:Product {product_id: $product_id})
                        MERGE (a)-[:INSTANCE_OF]->(p)
                        """,
                        **{
                            "asset_id": asset_row["asset_id"],
                            "serial_number": asset_row["serial_number"],
                            "model_number": asset_row["model_number"],
                            "customer_id": asset_row["customer_id"],
                            "warranty_status": asset_row["warranty_status"],
                            "warranty_expiry": asset_row["warranty_expiry"],
                            "purchase_date": asset_row["purchase_date"],
                            "product_id": asset_row["product_id"],
                        },
                    )
                    if asset_row.get("sku_id"):
                        session.run(
                            """
                            MATCH (a:Asset {asset_id: $asset_id})
                            MERGE (s:SKU {sku_id: $sku_id})
                            MERGE (a)-[:BOUND_TO_SKU]->(s)
                            """,
                            asset_id=asset_row["asset_id"],
                            sku_id=asset_row["sku_id"],
                        )
            invalidate_all_named_caches()
            result["neo4j"] = {"env": env, "merged": True}
        except Exception as exc:  # noqa: BLE001
            logger.exception("warranty asset promote failed")
            result["neo4j_error"] = str(exc)
            result["ok"] = False

    return result
