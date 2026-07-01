"""
Pipeline Orchestrator
=====================
Runs enterprise pipelines in industry-standard order:

  1. knowledge_etl     — Extract/Transform/Load from enterprise systems
  2. smoke_validation  — Regression scenarios before promotion
  3. staging_promotion — Promote validated graph to Neo4j (demo: same instance)

Usage:
  python -m graph.enterprise_pipeline.orchestrator
  python -m graph.enterprise_pipeline.orchestrator --pipelines etl,smoke
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl
from graph.enterprise_pipeline.pipelines.smoke_validation import run_smoke_validation
from graph.enterprise_pipeline.pipelines.staging_promotion import run_staging_promotion


def run_all(*, load_neo4j: bool = True, promote: bool = True) -> int:
    print("=== Pipeline 1: Knowledge ETL ===")
    etl = run_knowledge_etl(load_neo4j=load_neo4j)
    for name, s in etl.sources.items():
        print(f"  [{('OK' if s['ok'] else 'FAIL')}] {name}: {s['record_count']} records ({s.get('mode')})")
    if etl.errors:
        for e in etl.errors:
            print(f"  ! {e}")
        return 1
    print(f"  Catalog: {etl.output_file or '(dry-run)'}")
    if etl.neo4j_loaded:
        print(f"  Neo4j loaded: {etl.entity_counts}")

    print("\n=== Pipeline 2: Smoke Validation ===")
    smoke = run_smoke_validation()
    for line in smoke.details[-15:]:
        print(f"  {line}")
    if not smoke.ok:
        print("  Smoke validation FAILED — promotion skipped")
        return 1

    if promote:
        print("\n=== Pipeline 3: Staging Promotion ===")
        promo = run_staging_promotion(smoke_passed=smoke.ok)
        if promo.promoted:
            print(f"  Promoted batch {promo.batch_id}: {promo.entity_counts}")
        else:
            for e in promo.errors:
                print(f"  ! {e}")
            return 1

    print("\nAll pipelines completed successfully.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Enterprise pipeline orchestrator")
    parser.add_argument("--no-load", action="store_true", help="Skip Neo4j load in ETL")
    parser.add_argument("--no-promote", action="store_true", help="Skip staging promotion")
    parser.add_argument("--dry-run", action="store_true", help="ETL extract/transform only")
    args = parser.parse_args()

    if args.dry_run:
        etl = run_knowledge_etl(dry_run=True)
        print(etl)
        return 0 if not etl.errors else 1

    return run_all(load_neo4j=not args.no_load, promote=not args.no_promote)


if __name__ == "__main__":
    raise SystemExit(main())
