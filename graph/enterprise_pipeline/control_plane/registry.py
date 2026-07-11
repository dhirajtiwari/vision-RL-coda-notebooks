"""Pipeline registry — catalog of multi-source KG ingestion pipelines."""

from __future__ import annotations

from graph.enterprise_pipeline.control_plane.models import PipelineDefinition, RunMode, SourceKind

_PIPELINES: list[PipelineDefinition] = [
    PipelineDefinition(
        id="structured_extract",
        name="Structured enterprise extract",
        description="Extract from PIM/CRM/FSM/Claims (API or fixtures) — classic enterprise structured sources.",
        source_kind=SourceKind.STRUCTURED,
        supported_modes=[RunMode.BOOTSTRAP, RunMode.INCREMENTAL, RunMode.ON_DEMAND],
        stages=["extract_connectors", "summarize"],
        tags=["pim", "crm", "fsm", "claims"],
    ),
    PipelineDefinition(
        id="semi_structured_ingest",
        name="Semi-structured file ingest",
        description="Ingest CSV/JSONL work orders and parts lists (schema-on-read).",
        source_kind=SourceKind.SEMI_STRUCTURED,
        supported_modes=[RunMode.BOOTSTRAP, RunMode.INCREMENTAL, RunMode.ON_DEMAND],
        stages=["load_files", "normalize_rows"],
        tags=["csv", "jsonl"],
    ),
    PipelineDefinition(
        id="unstructured_extract",
        name="Unstructured text extract",
        description="Extract provisional symptoms/error codes from manuals and ticket text dumps.",
        source_kind=SourceKind.UNSTRUCTURED,
        supported_modes=[RunMode.BOOTSTRAP, RunMode.ON_DEMAND],
        stages=["read_documents", "pattern_extract"],
        tags=["txt", "manuals", "tickets"],
    ),
    PipelineDefinition(
        id="preprocess_normalize",
        name="Preprocess & quality gate",
        description="Clean, dedupe, score quality across multi-source staging bundles.",
        source_kind=SourceKind.MIXED,
        supported_modes=[RunMode.BOOTSTRAP, RunMode.INCREMENTAL, RunMode.ON_DEMAND],
        stages=["validate", "dedupe", "quality_report"],
        tags=["quality"],
    ),
    PipelineDefinition(
        id="knowledge_materialize",
        name="Ontology materialize (catalog)",
        description="Run OntologyBuilder / merge into enterprise catalog JSON (staging).",
        source_kind=SourceKind.MIXED,
        supported_modes=[RunMode.BOOTSTRAP, RunMode.INCREMENTAL, RunMode.ON_DEMAND],
        stages=["build_catalog", "write_staging"],
        tags=["ontology", "catalog"],
    ),
    PipelineDefinition(
        id="smoke_validate",
        name="Smoke validation",
        description="Run enterprise diagnosis scenarios before promotion.",
        source_kind=SourceKind.INTERNAL,
        supported_modes=[RunMode.ON_DEMAND],
        stages=["run_scenarios"],
        tags=["gate"],
    ),
    PipelineDefinition(
        id="promote_graph",
        name="Promote to Neo4j",
        description="MERGE approved catalog into Neo4j (staging or production target label).",
        source_kind=SourceKind.INTERNAL,
        supported_modes=[RunMode.ON_DEMAND],
        stages=["constraints", "merge", "invalidate_caches"],
        tags=["neo4j", "promote"],
    ),
    PipelineDefinition(
        id="bootstrap_all",
        name="Bootstrap (full first-time chain)",
        description="Project build phase: structured+semi+unstructured → preprocess → materialize → smoke.",
        source_kind=SourceKind.MIXED,
        supported_modes=[RunMode.BOOTSTRAP],
        default_mode=RunMode.BOOTSTRAP,
        stages=[
            "structured_extract",
            "semi_structured_ingest",
            "unstructured_extract",
            "preprocess_normalize",
            "knowledge_materialize",
            "smoke_validate",
        ],
        tags=["bootstrap", "full"],
    ),
    PipelineDefinition(
        id="incremental_sync",
        name="Incremental live sync",
        description="Live mode: structured + semi deltas → preprocess → materialize (no auto-promote).",
        source_kind=SourceKind.MIXED,
        supported_modes=[RunMode.INCREMENTAL],
        default_mode=RunMode.INCREMENTAL,
        stages=[
            "structured_extract",
            "semi_structured_ingest",
            "preprocess_normalize",
            "knowledge_materialize",
        ],
        tags=["incremental", "live"],
    ),
]


def list_pipelines() -> list[PipelineDefinition]:
    return list(_PIPELINES)


def get_pipeline(pipeline_id: str) -> PipelineDefinition | None:
    for p in _PIPELINES:
        if p.id == pipeline_id:
            return p
    return None
