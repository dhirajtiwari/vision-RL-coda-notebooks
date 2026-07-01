"""Unit tests for SQLite operational store."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.persistence import OperationalStore  # noqa: E402


def _temp_store() -> OperationalStore:
    tmp = tempfile.mkdtemp()
    return OperationalStore(db_path=Path(tmp) / "test.db")


def test_save_and_list_escalation() -> None:
    store = _temp_store()
    saved = store.save_escalation(
        "washer won't spin",
        {"product_id": "wm-001", "confidence": 0.7},
    )
    rows = store.list_escalations()
    assert len(rows) == 1
    assert rows[0]["case_id"] == saved["case_id"]
    assert rows[0]["diagnosis"]["product_id"] == "wm-001"


def test_save_and_list_case() -> None:
    store = _temp_store()
    case = store.save_case({
        "customer_id": "CUST-10042",
        "asset_id": "AST-WM-4421",
        "user_message": "washer won't spin",
        "diagnosis": {"product_id": "wm-001"},
        "escalation_reason": "low confidence",
    })
    cases = store.list_cases()
    assert len(cases) == 1
    assert cases[0]["case_id"] == case["case_id"]
    assert cases[0]["customer_id"] == "CUST-10042"


def test_save_and_update_claim() -> None:
    store = _temp_store()
    claim = store.save_claim({
        "claim_id": "CLM-TEST-001",
        "status": "submitted",
        "asset_id": "AST-DW-1102",
    })
    updated = store.update_claim("CLM-TEST-001", {"status": "approved", "agent_notes": "ok"})
    assert updated is not None
    assert updated["status"] == "approved"
    assert updated["agent_notes"] == "ok"
    assert store.get_claim("CLM-TEST-001")["status"] == "approved"
    assert claim["claim_id"] == "CLM-TEST-001"


if __name__ == "__main__":
    tests = [
        test_save_and_list_escalation,
        test_save_and_list_case,
        test_save_and_update_claim,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {test.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)