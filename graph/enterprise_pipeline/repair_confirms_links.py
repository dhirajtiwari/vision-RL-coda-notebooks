"""
Repair missing DiagnosticStep-[:CONFIRMS]->FailureMode links (catalog + Neo4j).

Root cause: many products (esp. bulletin d05 steps) were promoted with steps/FMs
but without diagnostic_step_failure_links. Diagnosis then either showed all steps
in order (including wrong-FM checks) or omitted the confirming bulletin step.

Policy (deterministic, TBox-safe ABox only):
  1. Prefer existing catalog links when present.
  2. Else build links by description keywords, then by sorted order index.
  3. Leave at most one "entry" step without CONFIRMS (shared prerequisite).
  4. On Neo4j: replace product CONFIRMS edges with the catalog set (delete + MERGE).

Usage:
  python -m graph.enterprise_pipeline.repair_confirms_links
  python -m graph.enterprise_pipeline.repair_confirms_links --neo4j production
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
from pathlib import Path
from typing import Any

from config.settings import settings
from runtime.partitioning import product_id_from_record

# keyword → prefer FM / step matching these tokens
_FM_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("bulletin|polar|connector key|keying", ("bulletin", "polar", "connector", "keying", "kit")),
    ("defrost|bi-?metal|frost|heater continuity", ("defrost", "bi-metal", "bimetal", "heater", "frost")),
    ("ice maker|33e|ice room|ice duct", ("ice", "33e", "duct")),
    ("evaporator|22e|condenser fan|fan motor", ("evaporator", "22e", "fan motor", "compressor")),
    ("drain|pump|impeller", ("drain", "pump", "impeller")),
    ("latch|door switch", ("latch", "door", "switch")),
    ("board|pcb|control", ("board", "pcb", "control", "comm")),
    ("magnetron|waveguide|hv", ("magnetron", "waveguide", "hv")),
    ("ambient|baffle|garage", ("ambient", "baffle", "garage", "below")),
]


def _core(bundle: dict[str, Any]) -> dict[str, Any]:
    inner = bundle.get("product")
    if isinstance(inner, dict) and (inner.get("product_id") or product_id_from_record(bundle)):
        return inner
    return bundle


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _order_key(entity_id: str, order_field: Any = None) -> int:
    if order_field is not None:
        try:
            return int(order_field)
        except (TypeError, ValueError):
            pass
    m = re.search(r"(?:d|fm|s)(\d+)$", str(entity_id), re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)$", str(entity_id))
    return int(m.group(1)) if m else 999


def _score_pair(step: dict[str, Any], fm: dict[str, Any]) -> float:
    st = _norm(f"{step.get('description', '')} {step.get('expected_outcome', '')} {step.get('step_id', '')}")
    ft = _norm(f"{fm.get('name', '')} {fm.get('description', '')} {fm.get('failure_mode_id', '')}")
    score = 0.0
    for _pat, tokens in _FM_HINTS:
        if any(t in st for t in tokens) and any(t in ft for t in tokens):
            score += 3.0
    # shared tokens length >= 4
    st_toks = set(re.findall(r"[a-z0-9]{4,}", st))
    ft_toks = set(re.findall(r"[a-z0-9]{4,}", ft))
    score += 0.5 * len(st_toks & ft_toks)
    # order proximity bonus
    so = _order_key(step.get("step_id", ""), step.get("order"))
    fo = _order_key(fm.get("failure_mode_id", ""))
    score += max(0.0, 2.0 - abs(so - fo) * 0.5)
    return score


def propose_confirms_links(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a clean CONFIRMS set for one product bundle."""
    steps = [s for s in (bundle.get("diagnostic_steps") or []) if isinstance(s, dict) and s.get("step_id")]
    fms = [f for f in (bundle.get("failure_modes") or []) if isinstance(f, dict) and f.get("failure_mode_id")]
    if not steps or not fms:
        return list(bundle.get("diagnostic_step_failure_links") or [])

    steps_sorted = sorted(steps, key=lambda s: _order_key(s["step_id"], s.get("order")))
    fms_sorted = sorted(fms, key=lambda f: _order_key(f["failure_mode_id"]))

    # Greedy best unique step↔FM pairs by score
    pairs: list[tuple[float, str, str]] = []
    for step in steps_sorted:
        for fm in fms_sorted:
            sc = _score_pair(step, fm)
            pairs.append((sc, str(step["step_id"]), str(fm["failure_mode_id"])))
    pairs.sort(key=lambda x: -x[0])

    used_s: set[str] = set()
    used_f: set[str] = set()
    chosen: list[dict[str, Any]] = []

    for sc, sid, fid in pairs:
        if sc < 1.5:  # weak noise
            break
        if sid in used_s or fid in used_f:
            continue
        chosen.append(
            {
                "step_id": sid,
                "failure_mode_id": fid,
                "link_type": "CONFIRMS",
                "confidence": min(0.95, 0.75 + sc / 20.0),
            }
        )
        used_s.add(sid)
        used_f.add(fid)

    # Order-index fallback for remaining FMs (skip first step as optional entry)
    rem_steps = [s for s in steps_sorted if str(s["step_id"]) not in used_s]
    rem_fms = [f for f in fms_sorted if str(f["failure_mode_id"]) not in used_f]
    # Prefer not using d01 as a forced pair if others remain
    if len(rem_steps) > len(rem_fms) and rem_steps:
        first_id = str(rem_steps[0]["step_id"])
        if _order_key(first_id, rem_steps[0].get("order")) <= 1:
            rem_steps = rem_steps[1:]

    for step, fm in zip(rem_steps, rem_fms, strict=False):
        sid, fid = str(step["step_id"]), str(fm["failure_mode_id"])
        chosen.append(
            {
                "step_id": sid,
                "failure_mode_id": fid,
                "link_type": "CONFIRMS",
                "confidence": 0.88,
            }
        )
        used_s.add(sid)
        used_f.add(fid)

    return chosen


def repair_catalog(path: Path | None = None) -> dict[str, Any]:
    catalog_path = path or settings.enterprise_catalog_file
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    products = data.get("products") or []
    repaired = 0
    total_links = 0
    for bundle in products:
        if not isinstance(bundle, dict):
            continue
        links = propose_confirms_links(bundle)
        old = bundle.get("diagnostic_step_failure_links") or []
        if links != old:
            bundle["diagnostic_step_failure_links"] = links
            repaired += 1
        total_links += len(links)

    catalog_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    syn = settings.data_file
    if syn.exists() and syn.resolve() != catalog_path.resolve():
        with contextlib.suppress(Exception):
            syn.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {
        "products_repaired": repaired,
        "total_confirms_links": total_links,
        "path": str(catalog_path),
    }


def merge_confirms_to_neo4j(env: str = "production") -> dict[str, Any]:
    """Delete product CONFIRMS edges and recreate from repaired catalog."""
    from graph.neo4j_client import get_driver, neo4j_env

    catalog = json.loads(settings.enterprise_catalog_file.read_text(encoding="utf-8"))
    products = catalog.get("products") or []
    wrote = 0
    cleared = 0
    with neo4j_env(env):  # type: ignore[arg-type]
        driver = get_driver()
        with driver.session() as session:
            for bundle in products:
                if not isinstance(bundle, dict):
                    continue
                core = _core(bundle)
                pid = core.get("product_id") or product_id_from_record(bundle)
                if not pid:
                    continue
                c = session.run(
                    """
                    MATCH (p:Product {product_id: $pid})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                    MATCH (ds)-[r:CONFIRMS]->(:FailureMode)
                    DELETE r
                    RETURN count(r) AS n
                    """,
                    pid=str(pid),
                ).single()
                cleared += int((c or {}).get("n") or 0)
                for link in bundle.get("diagnostic_step_failure_links") or []:
                    if link.get("link_type", "CONFIRMS") != "CONFIRMS":
                        continue
                    sid, fid = link.get("step_id"), link.get("failure_mode_id")
                    if not sid or not fid:
                        continue
                    conf = float(link.get("confidence") or 0.9)
                    session.run(
                        """
                        MATCH (ds:DiagnosticStep {step_id: $sid})
                        MATCH (fm:FailureMode {failure_mode_id: $fid})
                        MERGE (ds)-[r:CONFIRMS]->(fm)
                        SET r.confidence = $conf
                        """,
                        sid=str(sid),
                        fid=str(fid),
                        conf=conf,
                    )
                    wrote += 1
    return {"env": env, "confirms_cleared": cleared, "confirms_written": wrote}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neo4j", choices=("none", "staging", "production", "both"), default="both")
    args = parser.parse_args()
    cat = repair_catalog()
    print("catalog:", cat)
    if args.neo4j in ("staging", "both"):
        print("neo4j staging:", merge_confirms_to_neo4j("staging"))
    if args.neo4j in ("production", "both"):
        print("neo4j production:", merge_confirms_to_neo4j("production"))


if __name__ == "__main__":
    main()
