#!/usr/bin/env python3
"""
Eval gate (kickoff prompt §D, handbook ch04).

Runs versioned golden + safety suites against the DETERMINISTIC diagnosis engine
and exits non-zero when aggregate metrics fall below the thresholds in
``evals/thresholds.yaml``. Wired into CI as a release gate.

Suites:
  smoke  — fast subset (golden/smoke.jsonl) for PR gating.
  full   — golden/*.jsonl + safety/*.jsonl for release gating.

Metrics:
  product_accuracy   — fraction of cases whose detected product == expected.
  confidence_pass    — fraction of cases meeting per-case min_confidence.
  escalation_correct — fraction where escalated flag matches expectation.
  safety_pass        — fraction of safety cases handled without a violation.

Neo4j: if the graph is unavailable the harness SKIPS (exit 0 with a warning) so
CI without a database does not produce false failures; a nightly job runs it
against a live graph. Use --require-graph to force a hard failure instead.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVALS_DIR = ROOT / "evals"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rows.append(json.loads(line))
    return rows


def _load_thresholds() -> dict:
    path = EVALS_DIR / "thresholds.yaml"
    try:
        import yaml

        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _collect(suite: str) -> tuple[list[dict], list[dict]]:
    """Return (golden_cases, safety_cases) for the given suite.

    Safety cases are DB-free and always run (even in smoke) so injection/jailbreak
    regressions are caught on every PR.
    """
    safety: list[dict] = []
    for f in sorted((EVALS_DIR / "safety").glob("*.jsonl")):
        safety.extend(_load_jsonl(f))
    if suite == "smoke":
        golden = _load_jsonl(EVALS_DIR / "golden" / "smoke.jsonl")
    else:
        golden = []
        for f in sorted((EVALS_DIR / "golden").glob("*.jsonl")):
            golden.extend(_load_jsonl(f))
    return golden, safety


def _eval_case(case: dict) -> tuple[bool, bool, bool, list[str]]:
    """Evaluate one golden case → (product_ok, conf_ok, esc_ok, failures)."""
    from graph.graph_rag import detect_product, diagnose

    msg = case["message"]
    product = detect_product(msg)
    result = diagnose(msg)
    detected = product["product_id"] if product else None
    failures: list[str] = []

    product_ok = detected == case.get("expected_product")
    if not product_ok:
        failures.append(f"product mismatch: '{msg[:40]}' expected={case.get('expected_product')} got={detected}")

    conf_ok = result.confidence >= case.get("min_confidence", 0.0)
    if not conf_ok:
        failures.append(f"low confidence: '{msg[:40]}' {result.confidence:.2f} < {case.get('min_confidence')}")

    if "expected_escalated" in case:
        escalated = result.confidence < case.get("escalation_threshold", 0.65)
        esc_ok = escalated == case["expected_escalated"]
    else:
        esc_ok = True
    return product_ok, conf_ok, esc_ok, failures


def _run_golden(cases: list[dict]) -> dict:
    n = len(cases)
    product_ok = conf_ok = esc_ok = 0
    failures: list[str] = []
    for case in cases:
        p_ok, c_ok, e_ok, fails = _eval_case(case)
        product_ok += int(p_ok)
        conf_ok += int(c_ok)
        esc_ok += int(e_ok)
        failures.extend(fails)
    return {
        "n": n,
        "product_accuracy": product_ok / n if n else 1.0,
        "confidence_pass": conf_ok / n if n else 1.0,
        "escalation_correct": esc_ok / n if n else 1.0,
        "failures": failures,
    }


def _run_safety(cases: list[dict]) -> dict:
    """Safety cases assert guardrails reject/normalise adversarial input."""
    from guardrails.input import GuardrailViolation, check_input

    n = len(cases)
    passed = 0
    failures: list[str] = []
    for case in cases:
        msg = case["message"]
        expect_block = case.get("expect_block", True)
        try:
            check_input(msg)
            blocked = False
        except GuardrailViolation:
            blocked = True
        if blocked == expect_block:
            passed += 1
        else:
            failures.append(f"safety: '{msg[:40]}' expect_block={expect_block} got_block={blocked}")
    return {"n": n, "safety_pass": passed / n if n else 1.0, "failures": failures}


def _check_metric(group: str, metric: str, value: float, floor) -> bool:
    """Print one metric line vs its threshold; return pass/fail (True if no floor)."""
    if floor is None:
        print(f"  {group}.{metric} = {value:.3f}")
        return True
    passed = value >= floor
    print(f"  {group}.{metric} = {value:.3f}  (min {floor}) {'PASS' if passed else 'FAIL'}")
    return passed


def _report_metrics(results: dict, thresholds: dict) -> bool:
    """Print metrics vs thresholds; return True if all gated metrics pass."""
    ok = True
    for group in ("golden", "safety"):
        metrics = results.get(group)
        if not metrics:
            continue
        for metric, value in metrics.items():
            if metric in ("n", "failures"):
                continue
            ok = _check_metric(group, metric, value, thresholds.get(metric)) and ok
        for f in metrics.get("failures", [])[:10]:
            print(f"    - {f}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="LLMOps eval gate")
    parser.add_argument("--suite", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--report", type=str, default="")
    parser.add_argument("--require-graph", action="store_true")
    args = parser.parse_args()

    thresholds = _load_thresholds().get(args.suite, {})
    golden, safety = _collect(args.suite)

    from graph.neo4j_client import verify_connection

    graph_up = verify_connection()
    if not graph_up:
        if args.require_graph:
            print("!! Neo4j unavailable and --require-graph set → FAIL")
            return 2
        print("SKIP: Neo4j unavailable; golden suite skipped (safety still runs)")

    results: dict = {"suite": args.suite}
    if graph_up and golden:
        results["golden"] = _run_golden(golden)
    if safety:
        results["safety"] = _run_safety(safety)

    print(f"\n=== Eval gate: suite={args.suite} ===")
    ok = _report_metrics(results, thresholds)

    if args.report:
        Path(args.report).write_text(json.dumps(results, indent=2))
        print(f"\nreport → {args.report}")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
