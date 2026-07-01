"""Enterprise scenario regression suite."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.graph_rag import detect_product, diagnose
from graph.neo4j_client import verify_connection
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility

SCENARIOS_FILE = ROOT / "tests" / "scenarios" / "enterprise_test_scenarios.json"


def _load() -> list[dict]:
    return json.loads(SCENARIOS_FILE.read_text(encoding="utf-8"))["scenarios"]


def _run_case(case: dict, smoke: bool = False) -> tuple[bool, str]:
    if case.get("category") == "crm_enrichment":
        crm = enrich_session_from_crm(
            customer_id=case.get("customer_id"),
            asset_id=case.get("asset_id"),
        )
        if not crm.get("enriched"):
            return False, "CRM enrichment failed"
        if case.get("expected_product_id") and crm.get("product_id") != case["expected_product_id"]:
            return False, f"product={crm.get('product_id')}"
        if case.get("expect_warranty_eligible"):
            w = check_warranty_eligibility(crm)
            if not w.get("eligible"):
                return False, f"warranty={w.get('reason')}"
        return True, f"crm product={crm.get('product_id')}"

    msg = case["message"]
    product_id = case.get("product_id")
    detected = detect_product(msg)
    result = diagnose(msg, product_id=product_id)

    if case.get("expected_product_id") is None:
        if result.product_id:
            return False, f"expected no product, got {result.product_id}"
    elif case.get("expected_product_id"):
        pid = product_id or (detected or {}).get("product_id")
        if pid != case["expected_product_id"]:
            return False, f"product={pid}"

    if "min_confidence" in case and result.confidence < case["min_confidence"]:
        return False, f"confidence={result.confidence:.0%}"

    if case.get("expected_top_failure") and result.ranked_failure_modes:
        top = result.ranked_failure_modes[0]["name"]
        if top != case["expected_top_failure"]:
            return False, f"top={top}"

    if case.get("expect_escalate") is not None and result.should_escalate != case["expect_escalate"]:
        return False, f"escalate={result.should_escalate}"

    if case.get("require_diagnostic_steps") and not result.diagnostic_steps:
        return False, "no steps"

    if case.get("require_provenance_trail") and not result.provenance_trail:
        return False, "no provenance"

    if case.get("min_failure_modes") and len(result.ranked_failure_modes) < case["min_failure_modes"]:
        return False, "no failure modes"

    return True, f"product={result.product_id} conf={result.confidence:.0%} esc={result.should_escalate}"


def run_all(smoke: bool = False) -> int:
    if not verify_connection():
        print("SKIP: Neo4j not available")
        return 1

    cases = _load()
    if smoke:
        cases = [c for c in cases if c["category"] in ("product_detection", "safety_critical")]

    passed = failed = 0
    for case in cases:
        ok, detail = _run_case(case, smoke=smoke)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['id']}: {case.get('message', case.get('category', ''))[:50]}")
        print(f"        {detail}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{passed + failed} scenarios passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    smoke_mode = "--smoke" in sys.argv
    raise SystemExit(run_all(smoke=smoke_mode))
