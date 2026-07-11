"""
Durable Admin audit trail — survives API restarts.

Complements:
  - data/lineage/etl_batches.jsonl (ETL extract/materialize batches)
  - data/lineage/pipeline_runs/* (control-plane run JSON)
  - in-memory ADMIN_REVIEW_STATE.journey (session only)

Writes append-only JSONL under data/lineage/admin_audit.jsonl.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.settings import settings


def _path() -> Path:
    settings.lineage_dir.mkdir(parents=True, exist_ok=True)
    return settings.lineage_dir / "admin_audit.jsonl"


def log_admin_event(
    *,
    step: str,
    action: str,
    summary: str,
    changes: dict[str, Any] | None = None,
    actor: str = "admin",
    status: str = "ok",
) -> dict[str, Any]:
    record = {
        "event_id": f"AUD-{datetime.now(UTC).strftime('%Y%m%d')}-{uuid.uuid4().hex[:10]}",
        "ts": datetime.now(UTC).isoformat(),
        "actor": actor,
        "step": step,
        "action": action,
        "status": status,
        "summary": summary,
        "changes": changes or {},
    }
    with _path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return record


def list_admin_events(limit: int = 100) -> list[dict[str, Any]]:
    path = _path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    rows = []
    for line in reversed(lines[-limit * 2 :]):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(rows) >= limit:
            break
    return rows


def build_audit_bundle(limit: int = 40) -> dict[str, Any]:
    """Unified audit view for Admin UI / API."""
    from graph.enterprise_pipeline.control_plane.run_store import list_runs
    from utils.lineage_store import list_batches

    events = list_admin_events(limit=limit)
    runs = list_runs(limit=limit)
    batches = list_batches(limit=limit)
    return {
        "admin_events": events,
        "pipeline_runs": runs,
        "etl_batches": batches,
        "paths": {
            "admin_audit": str(_path()),
            "pipeline_runs": str(settings.lineage_dir / "pipeline_runs"),
            "etl_batches": str(settings.lineage_dir / "etl_batches.jsonl"),
        },
        "counts": {
            "admin_events": len(events),
            "pipeline_runs": len(runs),
            "etl_batches": len(batches),
        },
    }
