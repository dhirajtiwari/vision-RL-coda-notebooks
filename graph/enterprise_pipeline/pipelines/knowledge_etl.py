"""Pipeline 1: Knowledge ETL — Extract from enterprise systems, transform, load to Neo4j."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.connectors import ClaimsConnector, CRMConnector, FSMConnector, PIMConnector
from graph.enterprise_pipeline.connectors.base import ConnectorResult
from graph.enterprise_pipeline.transformers import OntologyBuilder
from graph.neo4j_client import get_driver
from graph.populate_graph import populate_graph
from utils.lineage_store import log_batch, new_batch_id


@dataclass
class ETLReport:
    batch_id: str = ""
    sources: dict[str, dict] = field(default_factory=dict)
    product_count: int = 0
    output_file: str = ""
    neo4j_loaded: bool = False
    entity_counts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _summarize(result: ConnectorResult) -> dict:
    return {
        "ok": result.ok,
        "record_count": len(result.records),
        "mode": result.metadata.get("mode", "unknown"),
        "errors": result.errors,
    }


def run_knowledge_etl(*, load_neo4j: bool = False, dry_run: bool = False) -> ETLReport:
    report = ETLReport(batch_id=new_batch_id())
    connectors = {
        "PIM": PIMConnector(),
        "FSM": FSMConnector(),
        "Claims": ClaimsConnector(),
        "CRM": CRMConnector(),
    }
    fetched: dict[str, ConnectorResult] = {}
    for name, conn in connectors.items():
        result = conn.fetch()
        fetched[name] = result
        report.sources[name] = _summarize(result)
        if not result.ok:
            report.errors.extend([f"{name}: {e}" for e in result.errors])

    if any(not fetched[k].ok for k in ("PIM", "FSM", "Claims")):
        log_batch(pipeline="knowledge_etl", status="failed", sources=report.sources, errors=report.errors)
        return report

    builder = OntologyBuilder(etl_batch_id=report.batch_id)
    catalog = builder.build_catalog_payload(
        pim=fetched["PIM"], fsm=fetched["FSM"], claims=fetched["Claims"], crm=fetched.get("CRM")
    )
    report.product_count = len(catalog.get("products", []))

    if dry_run:
        log_batch(pipeline="knowledge_etl", status="dry_run", product_count=report.product_count, sources=report.sources)
        return report

    settings.enterprise_catalog_file.parent.mkdir(parents=True, exist_ok=True)
    settings.enterprise_catalog_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    settings.data_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    report.output_file = str(settings.enterprise_catalog_file)

    if load_neo4j:
        driver = get_driver()
        try:
            report.entity_counts = populate_graph(driver, catalog, etl_batch_id=report.batch_id)
            report.neo4j_loaded = True
        except Exception as exc:
            report.errors.append(f"Neo4j load failed: {exc}")
        finally:
            driver.close()

    status = "success" if not report.errors else "partial"
    log_batch(
        pipeline="knowledge_etl",
        status=status,
        product_count=report.product_count,
        sources=report.sources,
        errors=report.errors,
        neo4j_target="staging" if load_neo4j else "catalog_only",
    )
    return report