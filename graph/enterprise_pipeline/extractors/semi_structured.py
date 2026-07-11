"""
Semi-structured ingestion: CSV / JSONL → normalized records for ontology merge.

Industry mapping: schema-on-read files (service notes, parts dumps) before semantic lift.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def normalize_work_order_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map semi-structured work-order fields to catalog-adjacent shape."""
    return {
        "record_type": "work_order_delta",
        "product_id": row.get("product_id") or row.get("productId") or "",
        "symptom_id": row.get("symptom_id") or "",
        "confirmed_failure_mode_id": row.get("failure_mode_id") or row.get("confirmed_failure_mode_id") or "",
        "resolution_summary": row.get("resolution") or row.get("resolution_summary") or "",
        "closed_date": row.get("closed_date") or row.get("date") or "",
        "source": "semi_structured",
        "raw": row,
    }


def normalize_parts_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "part_delta",
        "product_id": row.get("product_id") or "",
        "part_id": row.get("part_id") or "",
        "part_number": row.get("part_number") or "",
        "name": row.get("name") or row.get("part_name") or "",
        "estimated_cost_usd": float(row.get("cost") or row.get("estimated_cost_usd") or 0),
        "source": "semi_structured",
        "raw": row,
    }


def ingest_semi_structured_dir(root: Path) -> dict[str, Any]:
    """Load all known semi-structured artifacts under a directory."""
    work_orders: list[dict[str, Any]] = []
    parts: list[dict[str, Any]] = []
    artifacts: list[str] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".jsonl" and "work" in path.name.lower():
            rows = [normalize_work_order_row(r) for r in load_jsonl(path)]
            work_orders.extend(rows)
            artifacts.append(str(path))
        elif path.suffix.lower() == ".csv" and "part" in path.name.lower():
            rows = [normalize_parts_row(r) for r in load_csv(path)]
            parts.extend(rows)
            artifacts.append(str(path))
        elif path.suffix.lower() == ".jsonl" and "part" in path.name.lower():
            rows = [normalize_parts_row(r) for r in load_jsonl(path)]
            parts.extend(rows)
            artifacts.append(str(path))
        elif path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for r in data:
                    if "part_id" in r or "part_number" in r:
                        parts.append(normalize_parts_row(r))
                    else:
                        work_orders.append(normalize_work_order_row(r))
                artifacts.append(str(path))

    return {
        "work_orders": work_orders,
        "parts": parts,
        "artifacts": artifacts,
        "record_count": len(work_orders) + len(parts),
    }
