"""Shared models for the KG ingestion control plane."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SourceKind(str, Enum):
    STRUCTURED = "structured"
    SEMI_STRUCTURED = "semi_structured"
    UNSTRUCTURED = "unstructured"
    MIXED = "mixed"
    INTERNAL = "internal"  # graph/catalog only


class RunMode(str, Enum):
    BOOTSTRAP = "bootstrap"  # full first-time / rebaseline
    INCREMENTAL = "incremental"  # delta / watermark
    ON_DEMAND = "on_demand"  # human / API triggered


class PipelineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class PipelineDefinition:
    id: str
    name: str
    description: str
    source_kind: SourceKind
    supported_modes: list[RunMode]
    stages: list[str]
    default_mode: RunMode = RunMode.ON_DEMAND
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["source_kind"] = self.source_kind.value
        d["supported_modes"] = [m.value for m in self.supported_modes]
        d["default_mode"] = self.default_mode.value
        return d


@dataclass
class StageResult:
    name: str
    status: PipelineStatus
    message: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
            "errors": self.errors,
        }


@dataclass
class PipelineRunReport:
    run_id: str
    pipeline_id: str
    mode: RunMode
    dry_run: bool
    target_env: str  # staging | production
    status: PipelineStatus = PipelineStatus.RUNNING
    stages: list[StageResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    errors: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pipeline_id": self.pipeline_id,
            "mode": self.mode.value,
            "dry_run": self.dry_run,
            "target_env": self.target_env,
            "status": self.status.value,
            "stages": [s.to_dict() for s in self.stages],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "errors": self.errors,
            "summary": self.summary,
        }
