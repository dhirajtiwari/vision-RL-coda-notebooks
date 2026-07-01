"""Pipeline 2: Smoke Validation — run scenario tests before graph promotion."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field

from config.settings import settings
from utils.lineage_store import log_batch

ROOT = settings.project_root
SCENARIOS = ROOT / "tests" / "scenarios" / "enterprise_test_scenarios.json"


@dataclass
class SmokeReport:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    ok: bool = False
    details: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def run_smoke_validation() -> SmokeReport:
    report = SmokeReport()
    if not SCENARIOS.exists():
        report.errors.append(f"Scenario file missing: {SCENARIOS}")
        log_batch(pipeline="smoke_validation", status="failed", errors=report.errors)
        return report

    proc = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "test_enterprise_scenarios.py"), "--smoke"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    report.details = (proc.stdout + proc.stderr).strip().splitlines()
    report.ok = proc.returncode == 0
    for line in report.details:
        if "[PASS]" in line:
            report.passed += 1
        elif "[FAIL]" in line:
            report.failed += 1
        elif "SKIP" in line:
            report.skipped += 1

    log_batch(
        pipeline="smoke_validation",
        status="success" if report.ok else "failed",
        sources={"passed": report.passed, "failed": report.failed},
        errors=report.errors if report.ok else [f"failed={report.failed}"],
    )
    return report
