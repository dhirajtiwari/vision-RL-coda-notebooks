"""
Unstructured text → provisional diagnostic triples.

Industry mapping: document/ticket extraction before human or LLM refinement.
This demo uses deterministic pattern extraction (no paid LLM required).
Optional future hook: gateway LLM NER.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Pattern banks for demo appliances (extend per domain)
ERROR_CODE_RE = re.compile(r"\b([EF]\d{1,3}|[A-Z]\d{2}[A-Z]?\d?)\b")
SYMPTOM_HINTS = [
    (r"won'?t\s+drain|will\s+not\s+drain|not\s+draining", "drain", "high"),
    (r"won'?t\s+spin|will\s+not\s+spin", "spin", "high"),
    (r"leaking|leak\b", "leak", "medium"),
    (r"not\s+heating|no\s+heat|cold", "heating", "medium"),
    (r"noise|noisy|grinding|squeal", "noise", "medium"),
    (r"error|fault|code", "error_reported", "medium"),
    (r"not\s+starting|won'?t\s+start", "start", "high"),
    (r"arcing|spark", "arcing", "critical"),
    (r"no\s+ice|not\s+making\s+ice|won'?t\s+make\s+ice|slow\s+ice", "no_ice", "high"),
    (r"ice\s+bin|bin\s+full|harvest", "ice_bin", "medium"),
    (r"water\s+inlet|no\s+water\s+fill|fill\s+tube", "water_fill", "high"),
]


def extract_from_text(text: str, *, doc_id: str = "", product_hint: str = "") -> dict[str, Any]:
    """Extract provisional symptoms / error codes / notes from free text."""
    lower = text.lower()
    error_codes = sorted(set(ERROR_CODE_RE.findall(text.upper())))
    symptoms: list[dict[str, Any]] = []
    for pattern, key, severity in SYMPTOM_HINTS:
        if re.search(pattern, lower):
            symptoms.append(
                {
                    "provisional_id": f"prov-{key}-{doc_id or 'doc'}",
                    "key": key,
                    "description": f"Extracted symptom pattern: {key}",
                    "severity": severity,
                    "source": "unstructured_extract",
                    "confidence": 0.55,
                }
            )
    product_id = product_hint
    if not product_id:
        if "washer" in lower or "washing" in lower:
            product_id = "wm-001"
        elif "dishwasher" in lower:
            product_id = "dw-001"
        elif "microwave" in lower:
            product_id = "mw-001"
        elif "ice maker" in lower or "icemaker" in lower or "ice machine" in lower:
            product_id = "ice-001"
        elif "dehumidifier" in lower or "dryzone" in lower or "hmd-001" in lower:
            product_id = "hmd-001"
        elif "espresso" in lower or "brewbar" in lower or "esp-001" in lower or "bb-esp15" in lower:
            product_id = "esp-001"
        else:
            product_id = ""

    return {
        "doc_id": doc_id,
        "product_id": product_id,
        "error_codes": error_codes,
        "provisional_symptoms": symptoms,
        "char_count": len(text),
        "source": "unstructured",
    }


def ingest_unstructured_dir(root: Path) -> dict[str, Any]:
    docs: list[dict[str, Any]] = []
    artifacts: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        product_hint = ""
        # filename convention: wm-001_drain_manual.txt
        stem = path.stem
        # Filename convention: {product_id}_service_manual.txt / ticket.md
        if (
            stem.startswith("wm-")
            or stem.startswith("dw-")
            or stem.startswith("mw-")
            or stem.startswith("ice-")
            or stem.startswith("oem-")
            or stem.startswith("hmd-")
            or stem.startswith("esp-")
            or stem.startswith("vac-")
            or stem.startswith("ac-")
            or stem.startswith("dry-")
            or stem.startswith("ref-")
            or stem.startswith("fan-")
            or stem.startswith("pur-")
            or stem.startswith("hob-")
            or stem.startswith("oven-")
            or stem.startswith("grill-")
        ):
            product_hint = stem.split("_")[0]
        extracted = extract_from_text(text, doc_id=path.name, product_hint=product_hint)
        extracted["path"] = str(path)
        docs.append(extracted)
        artifacts.append(str(path))
    return {
        "documents": docs,
        "artifacts": artifacts,
        "document_count": len(docs),
        "symptom_hints": sum(len(d.get("provisional_symptoms") or []) for d in docs),
        "error_codes_found": sum(len(d.get("error_codes") or []) for d in docs),
    }
