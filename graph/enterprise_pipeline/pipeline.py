"""Backward-compatible entry point — delegates to knowledge ETL pipeline."""

from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl as run_pipeline

__all__ = ["run_pipeline"]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--load-neo4j", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report = run_pipeline(load_neo4j=args.load_neo4j, dry_run=args.dry_run)
    if report.errors:
        for e in report.errors:
            print(f"ERROR: {e}")
        raise SystemExit(1)
    print(f"OK — products={report.product_count} output={report.output_file}")
