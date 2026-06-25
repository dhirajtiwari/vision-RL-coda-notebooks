"""Integration tests for enterprise ETL pipeline (fixture mode)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl


def test_knowledge_etl_fixture_mode():
    report = run_knowledge_etl(load_neo4j=False, dry_run=True)
    assert not report.errors, report.errors
    assert report.product_count == 3
    assert report.sources["PIM"]["ok"]
    assert report.sources["FSM"]["ok"]
    assert report.sources["Claims"]["ok"]


if __name__ == "__main__":
    test_knowledge_etl_fixture_mode()
    print("PASS: pipeline integration (fixture dry-run)")