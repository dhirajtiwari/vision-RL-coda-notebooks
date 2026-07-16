"""
Ontology-first validation for product knowledge bundles (W3C-aligned).

Recommended knowledge-base build order (W3C / DL practice)::

  1. **TBox (OWL / RDFS ontology)** — classes, properties, domain/range
     ("the rule book"). See W3C OWL 2 Primer.
  2. **Shapes / constraints (SHACL-style)** — closed-world checks that
     instance data is complete and type-safe enough for the application
     (W3C SHACL). We implement a lightweight SHACL-*inspired* validator
     without requiring an external reasoner.
  3. **ABox (RDF product instances)** — only facts that conform to TBox +
     shapes, so irrelevant or malformed entities never reach the runtime
     knowledge graph used by diagnosis.
  4. **Operational graph** — Neo4j property graph is the *runtime*
     projection of the approved ABox for GraphRAG (not a substitute for
     defining the ontology).

This module validates **incoming product packs** against the fixed
warranty-diagnosis TBox (classes/properties from ``rdf_ontology_export``)
before materialize/promote. It does **not** claim full OWL reasoning.
"""

from __future__ import annotations

from typing import Any

from graph.rdf_ontology_export import CLASSES, OBJECT_PROPERTIES

# Catalog JSON list keys that map to OWL classes in our TBox
ALLOWED_LIST_KEYS: dict[str, str] = {
    "symptoms": "Symptom",
    "failure_modes": "FailureMode",
    "diagnostic_steps": "DiagnosticStep",
    "parts": "Part",
    "components": "Component",
    "error_codes": "ErrorCode",
    "historical_resolutions": "HistoricalResolution",
    "skus": "SKU",
    "claims": "Claim",
}

# Link tables that must only reference ids that exist in the same bundle
LINK_SPECS: list[tuple[str, str, str, str, str]] = [
    # (list_key, from_field, from_pool, to_field, to_pool)
    ("symptom_failure_links", "symptom_id", "symptoms", "failure_mode_id", "failure_modes"),
    ("failure_mode_part_links", "failure_mode_id", "failure_modes", "part_id", "parts"),
    ("failure_mode_component_links", "failure_mode_id", "failure_modes", "component_id", "components"),
    ("component_part_links", "component_id", "components", "part_id", "parts"),
    ("error_code_failure_links", "error_code_id", "error_codes", "failure_mode_id", "failure_modes"),
    ("diagnostic_step_failure_links", "step_id", "diagnostic_steps", "failure_mode_id", "failure_modes"),
    ("sku_part_links", "sku_id", "skus", "part_id", "parts"),
]

ID_FIELDS: dict[str, str] = {
    "symptoms": "symptom_id",
    "failure_modes": "failure_mode_id",
    "diagnostic_steps": "step_id",
    "parts": "part_id",
    "components": "component_id",
    "error_codes": "error_code_id",
    "historical_resolutions": "resolution_id",
    "skus": "sku_id",
}

# Minimum evidence for diagnosis-safe ABox (prevents empty / junk products)
MIN_SYMPTOMS = 1
MIN_FAILURE_MODES = 1
MIN_INDICATES_LINKS = 1  # symptom→failure_mode with confidence


def tbox_summary() -> dict[str, Any]:
    """Export TBox inventory for Admin UI / API (ontology rule book)."""
    return {
        "standard_refs": {
            "rdf": "https://www.w3.org/TR/rdf11-concepts/",
            "rdfs": "https://www.w3.org/TR/rdf-schema/",
            "owl2": "https://www.w3.org/TR/owl2-overview/",
            "owl2_primer": "https://www.w3.org/TR/owl2-primer/",
            "shacl": "https://www.w3.org/TR/shacl/",
        },
        "build_order": [
            "1. Define / freeze domain TBox once (OWL classes + properties) — shared rule book",
            "2. Onboard NEW product = author ABox instances under existing classes (not a new ontology language)",
            "3. Only if domain needs NEW *types* of things → extend TBox (rare governance change)",
            "4. Validate ABox against TBox + shapes (this module / SHACL-style)",
            "5. Materialize conforming ABox → promote to operational Neo4j → export RDF for audit",
        ],
        "new_vs_existing": {
            "existing_product": "ABox already in live graph; updates re-validate changed facts against same TBox",
            "new_product": (
                "No product-specific ontology file required. Build instance pack "
                "(symptoms, FMs, INDICATES links, …) typed by the domain TBox, then validate."
            ),
            "tbox_extension": (
                "Required only when introducing a new class/property not in the domain ontology "
                "(e.g. a new entity kind). A new SKU/product_id is ABox, not TBox."
            ),
        },
        "classes": [{"name": c, "comment": note} for c, note in CLASSES],
        "object_properties": [
            {
                "name": name,
                "domain": domain,
                "range": rng,
                "comment": comment,
                "neo4j": neo,
            }
            for name, domain, rng, comment, neo in OBJECT_PROPERTIES
        ],
        "allowed_catalog_lists": ALLOWED_LIST_KEYS,
        "note": (
            "OWL defines meaning (open-world inference). SHACL-style shapes enforce "
            "closed-world data quality before load. Our runtime diagnosis uses Neo4j "
            "as the operational graph; RDF export is the formal W3C serialization."
        ),
    }


def _pool_ids(bundle: dict[str, Any], list_key: str) -> set[str]:
    field = ID_FIELDS.get(list_key)
    if not field:
        return set()
    out: set[str] = set()
    for row in bundle.get(list_key) or []:
        if isinstance(row, dict) and row.get(field):
            out.add(str(row[field]))
    return out


def _product_core(bundle: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        return {}
    inner = bundle.get("product")
    if isinstance(inner, dict):
        return inner
    return bundle


def _near_duplicate_warnings(bundle: dict[str, Any], warnings: list[str], pid: str) -> dict[str, Any]:
    """Detect near-duplicate symptoms / failure modes within a bundle.

    Appends human-readable warnings and returns a structured suggestion map for
    the Admin review queue. Uses the stdlib fuzzy resolver (no extra deps).
    """
    from graph.enterprise_pipeline.entity_resolution import find_near_duplicates

    out: dict[str, list[dict[str, Any]]] = {}
    checks = (
        ("symptoms", "symptom_id", "description"),
        ("failure_modes", "failure_mode_id", "name"),
    )
    for list_key, id_field, text_field in checks:
        rows = bundle.get(list_key)
        if not isinstance(rows, list) or len(rows) < 2:
            continue
        dups = find_near_duplicates(rows, id_field=id_field, text_field=text_field)
        if dups:
            out[list_key] = dups
            for d in dups:
                warnings.append(
                    f"{pid}: near-duplicate {list_key} {d['a_id']} ~ {d['b_id']} "
                    f"(score {d['score']}) — review for strong/weak merge"
                )
    return out


def validate_product_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """
    Validate one product ontology bundle (ABox candidate) against TBox rules.

    Returns a report with ``ok``, ``errors``, ``warnings``, ``product_id``.
    """
    errors: list[str] = []
    warnings: list[str] = []
    core = _product_core(bundle)
    pid = str(core.get("product_id") or "")

    if not pid:
        errors.append("product.product_id is required (TBox: Product identity)")
    if not (core.get("name") or "").strip():
        errors.append(f"{pid or '?'}: product.name is required")

    # Reject unknown top-level keys that are not in TBox mapping or known meta
    known_meta = {
        "product",
        "model",
        "symptom_failure_links",
        "failure_mode_part_links",
        "failure_mode_component_links",
        "component_part_links",
        "error_code_failure_links",
        "diagnostic_step_failure_links",
        "sku_part_links",
        "catalog_metadata",
        "_test_pack",
        "product_id",
        "name",
        "family",
        "oem",
        "brand",
        "category",
        "model_year",
    }
    for key in bundle:
        if key in known_meta or key in ALLOWED_LIST_KEYS:
            continue
        if key.startswith("_"):
            continue
        warnings.append(f"{pid}: unknown catalog key '{key}' not in TBox-mapped lists — ignored for diagnosis graph")

    # Required diagnosis evidence (shapes)
    symptoms = bundle.get("symptoms") or []
    fms = bundle.get("failure_modes") or []
    links = bundle.get("symptom_failure_links") or []
    if len(symptoms) < MIN_SYMPTOMS:
        errors.append(f"{pid}: need ≥{MIN_SYMPTOMS} Symptom (ABox) for diagnosis — empty product rejected")
    if len(fms) < MIN_FAILURE_MODES:
        errors.append(f"{pid}: need ≥{MIN_FAILURE_MODES} FailureMode (ABox) — cannot diagnose without FMs")
    if len(links) < MIN_INDICATES_LINKS:
        errors.append(
            f"{pid}: need ≥{MIN_INDICATES_LINKS} symptom→failure_mode link (INDICATES / confidence) "
            "— otherwise ranking has no graph evidence"
        )

    # Id uniqueness + required id fields
    for list_key, id_field in ID_FIELDS.items():
        rows = bundle.get(list_key) or []
        if not isinstance(rows, list):
            errors.append(f"{pid}: {list_key} must be a list")
            continue
        seen: set[str] = set()
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{pid}: {list_key}[{i}] must be an object")
                continue
            rid = row.get(id_field)
            if not rid:
                errors.append(f"{pid}: {list_key}[{i}] missing {id_field}")
                continue
            rid = str(rid)
            if rid in seen:
                errors.append(f"{pid}: duplicate {id_field}={rid} in {list_key}")
            seen.add(rid)

    # Referential integrity of links (closed-world shape check)
    pools = {k: _pool_ids(bundle, k) for k in ID_FIELDS}
    for list_key, from_f, from_pool, to_f, to_pool in LINK_SPECS:
        for i, row in enumerate(bundle.get(list_key) or []):
            if not isinstance(row, dict):
                errors.append(f"{pid}: {list_key}[{i}] must be an object")
                continue
            a, b = row.get(from_f), row.get(to_f)
            if a and str(a) not in pools.get(from_pool, set()):
                errors.append(
                    f"{pid}: {list_key}[{i}].{from_f}={a} not in bundle {from_pool} "
                    f"(orphan link — rejected to protect diagnosis accuracy)"
                )
            if b and str(b) not in pools.get(to_pool, set()):
                errors.append(
                    f"{pid}: {list_key}[{i}].{to_f}={b} not in bundle {to_pool} "
                    f"(orphan link — rejected to protect diagnosis accuracy)"
                )
            if list_key == "symptom_failure_links":
                conf = row.get("confidence")
                if conf is None:
                    warnings.append(f"{pid}: symptom_failure_links[{i}] missing confidence (default later)")
                else:
                    try:
                        c = float(conf)
                        if c < 0 or c > 1:
                            errors.append(f"{pid}: confidence {c} out of range [0,1]")
                    except (TypeError, ValueError):
                        errors.append(f"{pid}: confidence must be numeric")

    # Historical resolutions must point at known FMs when present
    for i, row in enumerate(bundle.get("historical_resolutions") or []):
        if not isinstance(row, dict):
            continue
        fm = row.get("confirmed_failure_mode_id") or row.get("failure_mode_id")
        if fm and str(fm) not in pools.get("failure_modes", set()):
            errors.append(f"{pid}: historical_resolutions[{i}] FM {fm} not in failure_modes")

    # Strong/weak entity resolution: flag near-duplicate ABox nodes (review, not
    # auto-merge) so an LLM/unstructured-extracted symptom does not silently
    # create a competing duplicate of a catalog one. See entity_resolution.py.
    duplicate_suggestions = _near_duplicate_warnings(bundle, warnings, pid)

    ok = len(errors) == 0
    return {
        "ok": ok,
        "product_id": pid or None,
        "name": core.get("name"),
        "errors": errors,
        "warnings": warnings,
        "duplicate_suggestions": duplicate_suggestions,
        "entity_counts": {
            k: len(bundle.get(k) or []) if isinstance(bundle.get(k), list) else 0 for k in ALLOWED_LIST_KEYS
        },
        "tbox_classes_used": sorted(
            {ALLOWED_LIST_KEYS[k] for k in ALLOWED_LIST_KEYS if isinstance(bundle.get(k), list) and bundle.get(k)}
            | ({"Product"} if pid else set())
        ),
    }


def validate_catalog_products(
    products: list[dict[str, Any]],
    *,
    product_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Validate many bundles; optionally filter to selected product_ids."""
    allow = {str(p) for p in product_ids} if product_ids else None
    reports: list[dict[str, Any]] = []
    for bundle in products or []:
        if not isinstance(bundle, dict):
            continue
        core = _product_core(bundle)
        pid = str(core.get("product_id") or "")
        if allow is not None and pid not in allow:
            continue
        reports.append(validate_product_bundle(bundle))

    passed = [r for r in reports if r["ok"]]
    failed = [r for r in reports if not r["ok"]]
    return {
        "ok": len(failed) == 0 and len(reports) > 0,
        "validated_count": len(reports),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "passed_product_ids": [r["product_id"] for r in passed if r.get("product_id")],
        "failed_product_ids": [r["product_id"] for r in failed if r.get("product_id")],
        "reports": reports,
        "tbox": tbox_summary(),
        "headline": (
            f"Ontology validation: {len(passed)} passed, {len(failed)} failed "
            f"(of {len(reports)} ABox product(s) checked against TBox shapes)."
            if reports
            else "No products to validate."
        ),
    }


def load_pim_bundles() -> list[dict[str, Any]]:
    """Load raw product bundles from PIM fixture (ABox candidates)."""
    import json

    from config.settings import settings

    path = settings.enterprise_sources_dir / "pim_catalog.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    products = data.get("products") if isinstance(data, dict) else data
    return [p for p in (products or []) if isinstance(p, dict)]
