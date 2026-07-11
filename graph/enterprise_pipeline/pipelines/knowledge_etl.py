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
    product_summaries: list[dict] = field(default_factory=list)


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


def _merge_selected_products(
    built_catalog: dict,
    *,
    product_ids: list[str] | None,
) -> tuple[dict, list[str]]:
    """
    When product_ids is set, upsert *only* those bundles into the existing
    enterprise catalog (do not wipe unselected products). Returns (catalog, applied_ids).
    """
    from runtime.partitioning import product_id_from_record

    if not product_ids:
        return built_catalog, [
            str(pid)
            for p in (built_catalog.get("products") or [])
            if isinstance(p, dict) and (pid := product_id_from_record(p))
        ]

    allow = {str(x) for x in product_ids}
    selected_rows = []
    for p in built_catalog.get("products") or []:
        if not isinstance(p, dict):
            continue
        pid = product_id_from_record(p)
        if pid and str(pid) in allow:
            selected_rows.append(p)

    existing: dict = {"products": []}
    if settings.enterprise_catalog_file.exists():
        try:
            existing = json.loads(settings.enterprise_catalog_file.read_text(encoding="utf-8"))
        except Exception:
            existing = {"products": []}

    by_id: dict[str, dict] = {}
    for p in existing.get("products") or []:
        if isinstance(p, dict) and (pid := product_id_from_record(p)):
            by_id[str(pid)] = p
    applied: list[str] = []
    for p in selected_rows:
        pid = product_id_from_record(p)
        if pid:
            by_id[str(pid)] = p
            applied.append(str(pid))

    out = dict(existing)
    out["products"] = list(by_id.values())
    out["etl_batch_id"] = built_catalog.get("etl_batch_id") or existing.get("etl_batch_id")
    # Also upsert multi-source Asset / Claim ABox rows for the selected products
    # (CRM registered assets, closed claims). Without this, selection-scoped
    # materialize keeps stale seed assets only and never promotes new product assets.
    out["assets"] = _upsert_by_key(
        existing.get("assets") or [],
        built_catalog.get("assets") or [],
        id_key="asset_id",
        product_allow=allow,
    )
    out["claims"] = _upsert_by_key(
        existing.get("claims") or [],
        built_catalog.get("claims") or [],
        id_key="claim_id",
        product_allow=allow,
    )
    if built_catalog.get("warranty_policies"):
        # Prefer built policies when present (union by policy_id)
        out["warranty_policies"] = _upsert_by_key(
            existing.get("warranty_policies") or [],
            built_catalog.get("warranty_policies") or [],
            id_key="policy_id",
            product_allow=None,
        )
    out["selection_filter"] = {
        "requested": sorted(allow),
        "applied": applied,
        "note": "Only selected product ABox bundles were upserted into the catalog",
    }
    return out, applied


def _upsert_by_key(
    existing_rows: list,
    built_rows: list,
    *,
    id_key: str,
    product_allow: set[str] | None,
) -> list[dict]:
    """Union existing + built rows by id_key; when product_allow is set, only
    replace/add built rows whose product_id is in the selection (or has no product_id)."""
    by_id: dict[str, dict] = {}
    for row in existing_rows:
        if isinstance(row, dict) and row.get(id_key):
            by_id[str(row[id_key])] = dict(row)
    for row in built_rows:
        if not isinstance(row, dict) or not row.get(id_key):
            continue
        pid = row.get("product_id")
        if product_allow is not None and pid and str(pid) not in product_allow:
            continue
        by_id[str(row[id_key])] = dict(row)
    return list(by_id.values())


def run_knowledge_etl(
    *,
    load_neo4j: bool = False,
    dry_run: bool = False,
    product_ids: list[str] | None = None,
) -> ETLReport:
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
    # Optional Admin selection: merge only selected products into existing catalog
    catalog, applied_ids = _merge_selected_products(catalog, product_ids=product_ids)
    report.product_count = len(catalog.get("products", []))
    all_ids = [pid for p in catalog.get("products", []) if (pid := product_id_from_record(p)) is not None]
    chunk_size = int(settings.etl_product_batch_size)
    # Partition work by selection when present (enterprise batching)
    partition_ids = applied_ids if product_ids else all_ids
    product_chunks = batch_items(partition_ids, chunk_size) if chunk_size > 0 else [partition_ids]
    report.product_partitions = max(1, len(product_chunks))
    for idx, chunk in enumerate(product_chunks):
        label = chunk[0] if len(chunk) == 1 else f"chunk-{idx}-n{len(chunk)}"
        report.partition_keys.append(
            partition_for_etl(batch_id=report.batch_id, source_system="TRANSFORM", product_id=label)
        )

    # Product summaries for Admin change-preview (always useful; cheap vs Neo4j load)
    try:
        from graph.enterprise_pipeline.change_preview import catalog_products_from_etl_payload

        # Summaries of *built* selection or full catalog
        report.product_summaries = catalog_products_from_etl_payload(catalog)
        if product_ids and applied_ids:
            report.product_summaries = [s for s in report.product_summaries if s.get("product_id") in set(applied_ids)]
    except Exception:
        report.product_summaries = []

    if dry_run:
        log_batch(
            pipeline="knowledge_etl",
            status="dry_run",
            product_count=len(applied_ids) if product_ids else report.product_count,
            sources=report.sources,
        )
        return report

    if product_ids and not applied_ids:
        report.errors.append(f"None of the selected product_ids were found in PIM/catalog build: {sorted(product_ids)}")
        log_batch(pipeline="knowledge_etl", status="failed", errors=report.errors, sources=report.sources)
        return report

    settings.enterprise_catalog_file.parent.mkdir(parents=True, exist_ok=True)
    settings.enterprise_catalog_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    settings.data_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    report.output_file = str(settings.enterprise_catalog_file)

    if load_neo4j:
        driver = get_driver()
        try:
            # Promote only selected slices when filter set
            load_catalog = catalog
            if product_ids and applied_ids:
                allow = set(applied_ids)
                load_catalog = {
                    **catalog,
                    "products": [
                        p
                        for p in catalog.get("products") or []
                        if (pid := product_id_from_record(p)) and str(pid) in allow
                    ],
                }
            report.entity_counts = populate_graph(driver, load_catalog, etl_batch_id=report.batch_id)
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
