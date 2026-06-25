"""ETL batch lineage audit log for knowledge graph loads."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import settings


def _path() -> Path:
    settings.lineage_dir.mkdir(parents=True, exist_ok=True)
    return settings.lineage_dir / "etl_batches.jsonl"


def new_batch_id() -> str:
    return f"ETL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


def log_batch(
    *,
    pipeline: str,
    status: str,
    product_count: int = 0,
    sources: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    neo4j_target: str = "staging",
) -> dict[str, Any]:
    record = {
        "batch_id": new_batch_id(),
        "pipeline": pipeline,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "product_count": product_count,
        "neo4j_target": neo4j_target,
        "sources": sources or {},
        "errors": errors or [],
    }
    with _path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def list_batches(limit: int = 50) -> list[dict[str, Any]]:
    path = _path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return list(reversed(records[-limit:]))