"""Persist pipeline run history for the Control Room UI."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from config.settings import settings
from graph.enterprise_pipeline.control_plane.models import PipelineRunReport


def _runs_dir() -> Path:
    d = settings.lineage_dir / "pipeline_runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def new_run_id() -> str:
    return f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"


def save_run(report: PipelineRunReport) -> Path:
    path = _runs_dir() / f"{report.run_id}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    # append index line
    index = _runs_dir() / "index.jsonl"
    with index.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "run_id": report.run_id,
                    "pipeline_id": report.pipeline_id,
                    "mode": report.mode.value if hasattr(report.mode, "value") else report.mode,
                    "status": report.status.value if hasattr(report.status, "value") else report.status,
                    "finished_at": report.finished_at,
                    "dry_run": report.dry_run,
                    "target_env": report.target_env,
                }
            )
            + "\n"
        )
    return path


def list_runs(limit: int = 30) -> list[dict[str, Any]]:
    index = _runs_dir() / "index.jsonl"
    if not index.exists():
        return []
    lines = index.read_text(encoding="utf-8").strip().splitlines()
    rows = []
    for line in reversed(lines[-limit * 2 :]):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(rows) >= limit:
            break
    return rows


def get_run(run_id: str) -> dict[str, Any] | None:
    path = _runs_dir() / f"{run_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
