"""Basic evaluation tests for the diagnosis engine."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.graph_rag import detect_product, diagnose
from graph.neo4j_client import verify_connection

TEST_CASES = [
    {
        "message": "My washing machine won't spin and water stays in the drum",
        "expected_product": "wm-001",
        "min_confidence": 0.20,
    },
    {
        "message": "Dishwasher leaves dishes wet and cold after cycle",
        "expected_product": "dw-001",
        "min_confidence": 0.4,
    },
    {
        "message": "Microwave runs but food stays cold with arcing inside",
        "expected_product": "mw-001",
        "min_confidence": 0.4,
    },
]


def run_evaluation() -> int:
    if not verify_connection():
        print("SKIP: Neo4j not available")
        return 1

    passed = 0
    for i, case in enumerate(TEST_CASES, 1):
        product = detect_product(case["message"])
        result = diagnose(case["message"])

        product_ok = product and product["product_id"] == case["expected_product"]
        confidence_ok = result.confidence >= case["min_confidence"]
        has_failure = len(result.ranked_failure_modes) > 0

        ok = product_ok and confidence_ok and has_failure
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] Case {i}: {case['message'][:50]}...")
        print(f"       product={result.product_id} confidence={result.confidence:.0%}")
        if ok:
            passed += 1

    print(f"\n{passed}/{len(TEST_CASES)} tests passed")
    return 0 if passed == len(TEST_CASES) else 1


if __name__ == "__main__":
    raise SystemExit(run_evaluation())
