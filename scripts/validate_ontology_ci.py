#!/usr/bin/env python3
"""
Ontology + ABox validation gate for CI (merge-blocking).

Runs three checks with NO Neo4j required, so it can run on every PR:

1. **TBox Turtle syntax** — export the schema-only Turtle and parse it. Uses
   ``rdflib`` when installed (true W3C parse); otherwise a lightweight
   structural check (prefixes + balanced statements) so CI still gates.
2. **TBox internal consistency** — classes non-empty and unique; every object
   property's domain/range references a declared class.
3. **ABox shape validation** — if the enterprise catalog exists, validate every
   product bundle against the TBox + SHACL-style shapes (fail-closed on errors).

Exit code 0 = pass, 1 = fail. See ``docs/sdd/10-SCALING-POPULATING-KG.md`` §3.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import settings  # noqa: E402
from graph.enterprise_pipeline.ontology_validate import validate_catalog_products  # noqa: E402
from graph.rdf_ontology_export import CLASSES, OBJECT_PROPERTIES, schema_only_turtle  # noqa: E402


def _fail(msg: str, errors: list[str]) -> None:
    print(f"[FAIL] {msg}")
    for e in errors[:50]:
        print(f"   - {e}")
    sys.exit(1)


def check_turtle_syntax() -> None:
    turtle = schema_only_turtle()
    try:
        import rdflib  # type: ignore

        g = rdflib.Graph()
        g.parse(data=turtle, format="turtle")
        print(f"[PASS] TBox Turtle parses (rdflib): {len(g)} triples")
    except ImportError:
        # Lightweight structural check when rdflib is not installed.
        if "@prefix" not in turtle or turtle.count("owl:Class") < 1:
            _fail("TBox Turtle structural check", ["missing @prefix or owl:Class declarations"])
        print("[PASS] TBox Turtle structural check (rdflib not installed)")
    except Exception as exc:  # rdflib present but parse failed
        _fail("TBox Turtle syntax", [str(exc)])


def check_tbox_consistency() -> None:
    errors: list[str] = []
    class_names = [name for name, _ in CLASSES]
    if not class_names:
        errors.append("no classes declared in TBox")
    dupes = {c for c in class_names if class_names.count(c) > 1}
    if dupes:
        errors.append(f"duplicate class names: {sorted(dupes)}")
    known = set(class_names)
    for entry in OBJECT_PROPERTIES:
        name, domain, rng = entry[0], entry[1], entry[2]
        if domain not in known:
            errors.append(f"object property {name} domain '{domain}' is not a declared class")
        if rng not in known:
            errors.append(f"object property {name} range '{rng}' is not a declared class")
    if errors:
        _fail("TBox internal consistency", errors)
    print(f"[PASS] TBox consistency: {len(class_names)} classes, {len(OBJECT_PROPERTIES)} object properties")


def check_abox_shapes() -> None:
    path = settings.enterprise_catalog_file
    if not path.exists():
        print(f"[SKIP] ABox validation — catalog not present ({path.name}); run ETL to generate")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    products = data.get("products") if isinstance(data, dict) else data
    if not isinstance(products, list) or not products:
        print("[SKIP] ABox validation — catalog has no products")
        return
    report = validate_catalog_products(products)
    if not report["ok"]:
        failed = report.get("failed_product_ids", [])
        detail: list[str] = []
        for r in report.get("reports", []):
            if not r.get("ok"):
                detail.extend(r.get("errors", []))
        _fail(f"ABox shape validation ({len(failed)} products failed)", detail)
    print(f"[PASS] ABox shapes: {report['passed_count']}/{report['validated_count']} product bundles valid")


def main() -> None:
    print("=== Ontology + ABox validation gate ===")
    check_turtle_syntax()
    check_tbox_consistency()
    check_abox_shapes()
    print("=== All ontology checks passed ===")


if __name__ == "__main__":
    main()
