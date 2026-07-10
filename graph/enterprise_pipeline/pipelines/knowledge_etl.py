"""Pipeline 1: Knowledge ETL — Extract from enterprise systems, transform, load to Neo4j."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from config.settings import settings
from graph.enterprise_pipeline.connectors import ClaimsConnector, CRMConnector, FSMConnector, PIMConnector
from graph.enterprise_pipeline.connectors.base import ConnectorResult
from graph.enterprise_pipeline.transformers import OntologyBuilder
from graph.neo4j_client import close_driver, get_driver
from graph.populate_graph import populate_graph
from runtime.cache import invalidate_all_named_caches
from runtime.concurrency import parallel_map
from runtime.partitioning import batch_items, partition_for_etl, product_id_from_record
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
    partition_keys: list[str] = field(default_factory=list)
    product_partitions: int = 1
    connector_workers: int = 1


def _summarize(result: ConnectorResult) -> dict:
    return {
        "ok": result.ok,
        "record_count": len(result.records),
        "mode": result.metadata.get("mode", "unknown"),
        "errors": result.errors,
    }


def _fetch_connector(item: tuple[str, object]) -> tuple[str, ConnectorResult]:
    name, conn = item
    return name, conn.fetch()  # type: ignore[attr-defined]


def run_knowledge_etl(*, load_neo4j: bool = False, dry_run: bool = False) -> ETLReport:
    report = ETLReport(batch_id=new_batch_id())
    connectors = {
        "PIM": PIMConnector(),
        "FSM": FSMConnector(),
        "Claims": ClaimsConnector(),
        "CRM": CRMConnector(),
    }
    # I/O-bound connector fan-out with a bounded thread pool (enterprise practice:
    # parallel extract, serial transform for deterministic merge).
    workers = max(1, int(settings.etl_connector_max_workers))
    report.connector_workers = workers
    pairs = parallel_map(
        list(connectors.items()),
        _fetch_connector,
        max_workers=workers,
        preserve_order=True,
    )
    fetched: dict[str, ConnectorResult] = {}
    for name, result in pairs:
        fetched[name] = result
        report.sources[name] = _summarize(result)
        report.partition_keys.append(partition_for_etl(batch_id=report.batch_id, source_system=name))
        if not result.ok:
            report.errors.extend([f"{name}: {e}" for e in result.errors])

    if any(not fetched[k].ok for k in ("PIM", "FSM", "Claims")):
        log_batch(pipeline="knowledge_etl", status="failed", sources=report.sources, errors=report.errors)
        return report

    builder = OntologyBuilder(etl_batch_id=report.batch_id)
    # Single deterministic transform (correctness). Product batching is recorded as
    # logical partitions for lineage/scale planning; see settings.etl_product_batch_size.
    catalog = builder.build_catalog_payload(
        pim=fetched["PIM"], fsm=fetched["FSM"], claims=fetched["Claims"], crm=fetched.get("CRM")
    )
    report.product_count = len(catalog.get("products", []))
    product_ids = [pid for p in catalog.get("products", []) if (pid := product_id_from_record(p)) is not None]
    chunk_size = int(settings.etl_product_batch_size)
    product_chunks = batch_items(product_ids, chunk_size) if chunk_size > 0 else [product_ids]
    report.product_partitions = max(1, len(product_chunks))
    for idx, chunk in enumerate(product_chunks):
        label = chunk[0] if len(chunk) == 1 else f"chunk-{idx}-n{len(chunk)}"
        report.partition_keys.append(
            partition_for_etl(batch_id=report.batch_id, source_system="TRANSFORM", product_id=label)
        )

    if dry_run:
        log_batch(
            pipeline="knowledge_etl", status="dry_run", product_count=report.product_count, sources=report.sources
        )
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
            # Knowledge graph changed — drop read caches so API serves fresh subgraphs.
            invalidate_all_named_caches()
        except Exception as exc:
            report.errors.append(f"Neo4j load failed: {exc}")
        finally:
            close_driver()

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
