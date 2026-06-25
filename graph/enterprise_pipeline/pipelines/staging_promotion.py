"""Pipeline 3: Staging Promotion — promote catalog to production Neo4j after smoke pass."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from config.settings import settings
from graph.neo4j_client import close_driver, get_driver
from graph.populate_graph import populate_graph
from utils.lineage_store import log_batch


@dataclass
class PromotionReport:
    promoted: bool = False
    entity_counts: dict[str, int] = field(default_factory=dict)
    batch_id: str = ""
    errors: list[str] = field(default_factory=list)


def run_staging_promotion(*, require_smoke_pass: bool = True, smoke_passed: bool = True) -> PromotionReport:
    report = PromotionReport()
    if require_smoke_pass and not smoke_passed:
        report.errors.append("Smoke validation did not pass — promotion blocked")
        log_batch(pipeline="staging_promotion", status="blocked", errors=report.errors)
        return report

    catalog_path = settings.enterprise_catalog_file
    if not catalog_path.exists():
        report.errors.append(f"Catalog not found: {catalog_path}")
        log_batch(pipeline="staging_promotion", status="failed", errors=report.errors)
        return report

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    report.batch_id = catalog.get("etl_batch_id", "")

    driver = get_driver()
    try:
        report.entity_counts = populate_graph(driver, catalog, etl_batch_id=report.batch_id)
        report.promoted = True
    except Exception as exc:
        report.errors.append(str(exc))
    finally:
        close_driver()

    log_batch(
        pipeline="staging_promotion",
        status="success" if report.promoted else "failed",
        product_count=len(catalog.get("products", [])),
        errors=report.errors,
        neo4j_target="production",
    )
    return report