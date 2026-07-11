"""
Execute multi-source KG pipelines with bootstrap / incremental / on_demand modes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.control_plane.models import (
    PipelineRunReport,
    PipelineStatus,
    RunMode,
    StageResult,
)
from graph.enterprise_pipeline.control_plane.registry import get_pipeline
from graph.enterprise_pipeline.control_plane.run_store import new_run_id, save_run
from graph.enterprise_pipeline.extractors.semi_structured import ingest_semi_structured_dir
from graph.enterprise_pipeline.extractors.unstructured_text import ingest_unstructured_dir
from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl
from graph.enterprise_pipeline.pipelines.smoke_validation import run_smoke_validation
from graph.enterprise_pipeline.preprocess.normalize import preprocess_bundle
from graph.neo4j_client import get_driver
from graph.populate_graph import populate_graph
from runtime.cache import invalidate_all_named_caches


def _now() -> str:
    return datetime.now(UTC).isoformat()


def sources_root() -> Path:
    return settings.project_root / "data" / "pipeline_sources"


def staging_root() -> Path:
    d = settings.project_root / "data" / "pipeline_staging"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_pipeline(
    pipeline_id: str,
    *,
    mode: str | RunMode = RunMode.ON_DEMAND,
    dry_run: bool = False,
    target_env: str = "staging",
    product_ids: list[str] | None = None,
) -> PipelineRunReport:
    definition = get_pipeline(pipeline_id)
    if definition is None:
        report = PipelineRunReport(
            run_id=new_run_id(),
            pipeline_id=pipeline_id,
            mode=RunMode.ON_DEMAND,
            dry_run=dry_run,
            target_env=target_env,
            status=PipelineStatus.FAILED,
            started_at=_now(),
            finished_at=_now(),
            errors=[f"Unknown pipeline: {pipeline_id}"],
        )
        save_run(report)
        return report

    mode_e = RunMode(mode) if isinstance(mode, str) else mode
    if mode_e not in definition.supported_modes:
        mode_e = definition.default_mode

    report = PipelineRunReport(
        run_id=new_run_id(),
        pipeline_id=pipeline_id,
        mode=mode_e,
        dry_run=dry_run,
        target_env=target_env if target_env in ("staging", "production") else "staging",
        status=PipelineStatus.RUNNING,
        started_at=_now(),
    )

    sel = [str(x) for x in (product_ids or []) if x]
    ctx: dict[str, Any] = {
        "mode": mode_e.value,
        "dry_run": dry_run,
        "target_env": report.target_env,
        "product_ids": sel or None,
    }

    try:
        if pipeline_id == "structured_extract":
            _run_structured(report, ctx)
        elif pipeline_id == "semi_structured_ingest":
            _run_semi(report, ctx)
        elif pipeline_id == "unstructured_extract":
            _run_unstructured(report, ctx)
        elif pipeline_id == "preprocess_normalize":
            _run_preprocess(report, ctx)
        elif pipeline_id == "knowledge_materialize":
            _run_materialize(report, ctx)
        elif pipeline_id == "smoke_validate":
            _run_smoke(report, ctx)
        elif pipeline_id == "promote_graph":
            _run_promote(report, ctx)
        elif pipeline_id == "bootstrap_all":
            _run_chain(
                report,
                ctx,
                [
                    "structured_extract",
                    "semi_structured_ingest",
                    "unstructured_extract",
                    "preprocess_normalize",
                    "knowledge_materialize",
                    "smoke_validate",
                ],
            )
        elif pipeline_id == "incremental_sync":
            _run_chain(
                report,
                ctx,
                [
                    "structured_extract",
                    "semi_structured_ingest",
                    "preprocess_normalize",
                    "knowledge_materialize",
                ],
            )
        else:
            report.errors.append(f"No runner for {pipeline_id}")
            report.status = PipelineStatus.FAILED
    except Exception as exc:  # noqa: BLE001
        report.errors.append(str(exc))
        report.status = PipelineStatus.FAILED
        report.stages.append(
            StageResult(name="exception", status=PipelineStatus.FAILED, message=str(exc), errors=[str(exc)])
        )

    if report.status == PipelineStatus.RUNNING:
        failed = any(s.status == PipelineStatus.FAILED for s in report.stages)
        report.status = PipelineStatus.FAILED if failed or report.errors else PipelineStatus.SUCCESS

    report.finished_at = _now()
    report.summary = {
        "stage_count": len(report.stages),
        "mode": report.mode.value,
        "dry_run": report.dry_run,
        "target_env": report.target_env,
    }
    save_run(report)
    return report


def _run_chain(report: PipelineRunReport, ctx: dict[str, Any], pipeline_ids: list[str]) -> None:
    for pid in pipeline_ids:
        sub = run_pipeline(
            pid,
            mode=report.mode,
            dry_run=report.dry_run,
            target_env=report.target_env,
            product_ids=ctx.get("product_ids"),
        )
        report.stages.append(
            StageResult(
                name=f"chain:{pid}",
                status=sub.status,
                message=f"sub-run {sub.run_id}",
                metrics={"sub_run_id": sub.run_id, "sub_status": sub.status.value},
                artifacts=[a for s in sub.stages for a in s.artifacts],
                errors=sub.errors,
            )
        )
        if sub.status == PipelineStatus.FAILED:
            report.errors.extend(sub.errors or [f"{pid} failed"])
            break
        # merge context artifacts
        for s in sub.stages:
            for k, v in (s.metrics or {}).items():
                if k.startswith("staging_"):
                    ctx[k] = v


def _run_structured(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    # Reuse existing knowledge ETL extract+transform without Neo4j unless bootstrap materialize later
    etl = run_knowledge_etl(load_neo4j=False, dry_run=report.dry_run)
    stage = StageResult(
        name="extract_connectors",
        status=PipelineStatus.FAILED if etl.errors and not etl.product_count else PipelineStatus.SUCCESS,
        message="PIM/FSM/Claims/CRM extract via existing connectors",
        metrics={
            "product_count": etl.product_count,
            "batch_id": etl.batch_id,
            "sources": etl.sources,
            "mode": report.mode.value,
            "workers": getattr(etl, "connector_workers", 1),
        },
        errors=list(etl.errors),
        artifacts=[etl.output_file] if etl.output_file else [],
    )
    if report.dry_run:
        stage.message += " (dry-run: no catalog write beyond existing ETL dry_run semantics)"
    report.stages.append(stage)
    # stash for preprocess
    staging = staging_root() / f"{report.run_id}-structured.json"
    payload = {"product_count": etl.product_count, "sources": etl.sources, "batch_id": etl.batch_id}
    if not report.dry_run:
        staging.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        stage.artifacts.append(str(staging))
    ctx["structured_summary"] = payload
    ctx["staging_structured"] = str(staging)


def _run_semi(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    root = sources_root() / "semi_structured"
    if report.mode == RunMode.INCREMENTAL:
        root = root / "incremental"
    else:
        root = root / "bootstrap"
    result = ingest_semi_structured_dir(root)
    stage = StageResult(
        name="load_semi_structured",
        status=PipelineStatus.SUCCESS if result["record_count"] >= 0 else PipelineStatus.FAILED,
        message=f"Loaded semi-structured artifacts from {root}",
        metrics={
            "work_orders": len(result["work_orders"]),
            "parts": len(result["parts"]),
            "record_count": result["record_count"],
        },
        artifacts=result["artifacts"],
    )
    report.stages.append(stage)
    path = staging_root() / f"{report.run_id}-semi.json"
    if not report.dry_run:
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        stage.artifacts.append(str(path))
    ctx["semi"] = result
    ctx["staging_semi"] = str(path)


def _run_unstructured(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    root = sources_root() / "unstructured" / ("bootstrap" if report.mode != RunMode.INCREMENTAL else "incremental")
    if not root.exists():
        root = sources_root() / "unstructured" / "bootstrap"
    result = ingest_unstructured_dir(root)
    stage = StageResult(
        name="extract_unstructured",
        status=PipelineStatus.SUCCESS,
        message=f"Pattern-extracted {result['document_count']} documents",
        metrics={
            "document_count": result["document_count"],
            "symptom_hints": result["symptom_hints"],
            "error_codes_found": result["error_codes_found"],
        },
        artifacts=result["artifacts"],
    )
    report.stages.append(stage)
    path = staging_root() / f"{report.run_id}-unstructured.json"
    if not report.dry_run:
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        stage.artifacts.append(str(path))
    ctx["unstructured"] = result
    ctx["staging_unstructured"] = str(path)


def _load_latest_staging(prefix: str) -> dict[str, Any]:
    files = sorted(staging_root().glob(f"*-{prefix}.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {}
    return json.loads(files[0].read_text(encoding="utf-8"))


def _run_preprocess(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    semi = ctx.get("semi") or _load_latest_staging("semi")
    unstr = ctx.get("unstructured") or _load_latest_staging("unstructured")
    structured = ctx.get("structured_summary") or _load_latest_staging("structured")
    bundle = {
        "work_orders": (semi or {}).get("work_orders") or [],
        "parts": (semi or {}).get("parts") or [],
        "documents": (unstr or {}).get("documents") or [],
        "structured_summary": structured or {},
    }
    # incremental mode: only last N work orders
    if report.mode == RunMode.INCREMENTAL and bundle["work_orders"]:
        bundle["work_orders"] = bundle["work_orders"][-20:]
    cleaned = preprocess_bundle(bundle)
    stage = StageResult(
        name="preprocess_quality",
        status=PipelineStatus.SUCCESS if cleaned["quality"]["pass_rate"] >= 0.5 else PipelineStatus.PARTIAL,
        message="Preprocess normalize + quality report",
        metrics=cleaned["quality"],
    )
    report.stages.append(stage)
    path = staging_root() / f"{report.run_id}-preprocessed.json"
    if not report.dry_run:
        path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
        stage.artifacts.append(str(path))
    ctx["preprocessed"] = cleaned
    ctx["staging_preprocessed"] = str(path)


def _run_materialize(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    """Materialize using existing knowledge ETL catalog path (non-dry unless requested)."""
    product_ids = ctx.get("product_ids")
    if report.dry_run:
        report.stages.append(
            StageResult(
                name="build_catalog",
                status=PipelineStatus.SUCCESS,
                message=(
                    "Dry-run: skipped catalog write; would run OntologyBuilder"
                    + (f" for selected {product_ids}" if product_ids else " (full catalog)")
                ),
                metrics={"dry_run": True, "product_ids": product_ids},
            )
        )
        return
    etl = run_knowledge_etl(load_neo4j=False, dry_run=False, product_ids=product_ids)
    # Optionally annotate catalog with preprocessed provisional notes
    pre = ctx.get("preprocessed") or _load_latest_staging("preprocessed")
    if pre and settings.enterprise_catalog_file.exists():
        catalog = json.loads(settings.enterprise_catalog_file.read_text(encoding="utf-8"))
        catalog["pipeline_ingest"] = {
            "quality": pre.get("quality"),
            "provisional_symptom_count": len(pre.get("provisional_symptoms") or []),
            "semi_work_orders": len(pre.get("work_orders") or []),
            "mode": report.mode.value,
            "run_id": report.run_id,
            "product_ids_filter": product_ids,
        }
        settings.enterprise_catalog_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    sel_note = f" selected={product_ids}" if product_ids else " (full catalog)"
    stage = StageResult(
        name="knowledge_materialize",
        status=PipelineStatus.FAILED if etl.errors and not etl.product_count else PipelineStatus.SUCCESS,
        message=f"Catalog written via OntologyBuilder knowledge ETL{sel_note}",
        metrics={
            "product_count": etl.product_count,
            "batch_id": etl.batch_id,
            "output": etl.output_file,
            "product_ids_filter": product_ids,
            "summaries": len(getattr(etl, "product_summaries", None) or []),
        },
        errors=list(etl.errors),
        artifacts=[etl.output_file] if etl.output_file else [],
    )
    report.stages.append(stage)


def _run_smoke(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    if report.dry_run:
        report.stages.append(
            StageResult(
                name="smoke_validate",
                status=PipelineStatus.SUCCESS,
                message="Dry-run: skipped live smoke (would run enterprise scenarios against Neo4j)",
                metrics={"dry_run": True, "would_run": "run_smoke_validation"},
            )
        )
        return
    smoke = run_smoke_validation()
    report.stages.append(
        StageResult(
            name="smoke_validate",
            status=PipelineStatus.SUCCESS if smoke.ok else PipelineStatus.FAILED,
            message="Enterprise scenario smoke",
            metrics={"passed": smoke.passed, "failed": smoke.failed, "ok": smoke.ok},
            errors=[] if smoke.ok else ["smoke failed — see details"],
        )
    )
    if not smoke.ok:
        report.errors.append("Smoke validation failed")


def _run_promote(report: PipelineRunReport, ctx: dict[str, Any]) -> None:
    from graph.neo4j_client import neo4j_env

    if report.dry_run:
        report.stages.append(
            StageResult(
                name="promote_graph",
                status=PipelineStatus.SUCCESS,
                message="Dry-run: would MERGE catalog into target Neo4j and invalidate caches",
                metrics={"target_env": report.target_env, "dry_run": True},
            )
        )
        return
    catalog_path = settings.enterprise_catalog_file
    if not catalog_path.exists():
        report.stages.append(
            StageResult(
                name="promote_graph",
                status=PipelineStatus.FAILED,
                message="No enterprise catalog to promote",
                errors=["catalog missing"],
            )
        )
        report.errors.append("catalog missing")
        return
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    product_ids = ctx.get("product_ids")
    promoted_ids: list[str] = []
    if product_ids:
        from runtime.partitioning import product_id_from_record

        allow = {str(x) for x in product_ids}
        filtered = []
        for row in catalog.get("products") or []:
            if not isinstance(row, dict):
                continue
            pid = product_id_from_record(row)
            if pid and str(pid) in allow:
                filtered.append(row)
                promoted_ids.append(str(pid))
        if not filtered:
            report.stages.append(
                StageResult(
                    name="promote_graph",
                    status=PipelineStatus.FAILED,
                    message=f"None of selected product_ids found in catalog: {sorted(allow)}",
                    errors=["selection empty after filter"],
                )
            )
            report.errors.append("selection empty after filter")
            return
        catalog = {**catalog, "products": filtered}
    target: str = "production" if report.target_env == "production" else "staging"
    try:
        with neo4j_env(target):  # type: ignore[arg-type]
            driver = get_driver()
            counts = populate_graph(
                driver,
                catalog,
                etl_batch_id=catalog.get("etl_batch_id", report.run_id),
            )
        # Bust ontology/subgraph/diagnose caches after either env promote
        invalidate_all_named_caches()
        report.stages.append(
            StageResult(
                name="promote_graph",
                status=PipelineStatus.SUCCESS,
                message=(
                    f"MERGE complete into Neo4j env={target}"
                    + (f" products={promoted_ids}" if promoted_ids else " (full catalog)")
                ),
                metrics={
                    "entity_counts": counts,
                    "target_env": target,
                    "product_ids_promoted": promoted_ids or None,
                    "neo4j_uri": (settings.neo4j_uri if target == "production" else settings.neo4j_staging_uri),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        report.stages.append(
            StageResult(name="promote_graph", status=PipelineStatus.FAILED, message=str(exc), errors=[str(exc)])
        )
        report.errors.append(str(exc))
