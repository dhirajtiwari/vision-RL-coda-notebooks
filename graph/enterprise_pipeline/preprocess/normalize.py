"""
Preprocess / quality stage for multi-source records before ontology materialization.

Industry mapping: clean → validate → dedupe → quality score (Great Expectations-like lite).
"""

from __future__ import annotations

from typing import Any

REQUIRED_WORK_ORDER = ("product_id", "confirmed_failure_mode_id")
REQUIRED_PART = ("product_id", "part_id")


def _nonempty(v: Any) -> bool:
    return v is not None and str(v).strip() != ""


def quality_score(record: dict[str, Any], required: tuple[str, ...]) -> float:
    if not required:
        return 1.0
    ok = sum(1 for k in required if _nonempty(record.get(k)))
    return round(ok / len(required), 3)


def dedupe_key(record: dict[str, Any]) -> str:
    rt = record.get("record_type", "unknown")
    if rt == "part_delta":
        return f"part:{record.get('product_id')}:{record.get('part_id')}"
    if rt == "work_order_delta":
        return (
            f"wo:{record.get('product_id')}:{record.get('symptom_id')}:"
            f"{record.get('confirmed_failure_mode_id')}:{record.get('closed_date')}"
        )
    return f"raw:{hash(frozenset(record.items()))}"


def preprocess_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """
    Accept a multi-source bundle and return cleaned records + quality report.

    Expected optional keys: work_orders, parts, documents (unstructured extracts),
    structured_summary (from enterprise connectors).
    """
    work_orders = list(bundle.get("work_orders") or [])
    parts = list(bundle.get("parts") or [])
    documents = list(bundle.get("documents") or [])

    cleaned_wo: list[dict[str, Any]] = []
    cleaned_parts: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in work_orders:
        qs = quality_score(row, REQUIRED_WORK_ORDER)
        row = {**row, "quality_score": qs}
        if qs < 0.5:
            rejected.append({"reason": "low_quality_work_order", "record": row})
            continue
        key = dedupe_key(row)
        if key in seen:
            rejected.append({"reason": "duplicate", "record": row})
            continue
        seen.add(key)
        cleaned_wo.append(row)

    for row in parts:
        qs = quality_score(row, REQUIRED_PART)
        row = {**row, "quality_score": qs}
        if qs < 0.5:
            rejected.append({"reason": "low_quality_part", "record": row})
            continue
        key = dedupe_key(row)
        if key in seen:
            rejected.append({"reason": "duplicate", "record": row})
            continue
        seen.add(key)
        cleaned_parts.append(row)

    # Unstructured: keep high-signal provisional symptoms only
    provisional_symptoms: list[dict[str, Any]] = []
    for doc in documents:
        for s in doc.get("provisional_symptoms") or []:
            if float(s.get("confidence") or 0) >= 0.5:
                provisional_symptoms.append({**s, "product_id": doc.get("product_id", "")})

    report = {
        "input_work_orders": len(work_orders),
        "input_parts": len(parts),
        "input_documents": len(documents),
        "accepted_work_orders": len(cleaned_wo),
        "accepted_parts": len(cleaned_parts),
        "provisional_symptoms": len(provisional_symptoms),
        "rejected": len(rejected),
        "rejection_reasons": _count_reasons(rejected),
        "pass_rate": _pass_rate(len(work_orders) + len(parts), len(cleaned_wo) + len(cleaned_parts)),
    }

    return {
        "work_orders": cleaned_wo,
        "parts": cleaned_parts,
        "provisional_symptoms": provisional_symptoms,
        "documents": documents,
        "rejected": rejected[:50],
        "quality": report,
        "structured_summary": bundle.get("structured_summary") or {},
    }


def _count_reasons(rejected: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rejected:
        k = str(r.get("reason") or "unknown")
        out[k] = out.get(k, 0) + 1
    return out


def _pass_rate(total_in: int, total_ok: int) -> float:
    if total_in <= 0:
        return 1.0
    return round(total_ok / total_in, 3)
