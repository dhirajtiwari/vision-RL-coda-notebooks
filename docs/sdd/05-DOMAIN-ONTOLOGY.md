# 05 — Domain ontology (TBox / ABox)

**Load when:** P1 TBox, new packs, shape validation, multi-source ABox.

## Platform rule (non-negotiable)

| Term | Definition | Action |
|------|------------|--------|
| **TBox** | Shared types: classes + allowed relationships | Define **once** in code |
| **ABox** | Instances for one product/device/site | Built by pipeline from sources |
| **NEW pack** | New ABox under existing classes | **Not** a new schema language |
| **TBox extension** | Unknown kind of entity/key | Detect + human review; never auto-merge |

**Sources on disk ≠ ontology schema.** Sources feed instances.

## This project entities (WarrantyGraph)

Product, Model, SKU, Asset, Symptom, ErrorCode, FailureMode, DiagnosticStep, Component, Part, Claim, HistoricalResolution, WarrantyPolicy.

**Chain:** Asset → Product → Symptom/ErrorCode → FailureMode → DiagnosticStep → Part (+ history/claims).

## Pack build pattern

1. Structured connectors + semi/unstructured extractors
2. OntologyBuilder attaches rich keys (model/SKU/components/error_codes/CONFIRMS, etc.)
3. Merge CRM assets + claims when available
4. Catalog JSON upsert (selection-scoped)
5. Shape validate vs TBox
6. Promote staging → production

## Pack contract pitfalls (do not repeat)

- Drop required shape fields → Fetch/ETL crash
- Naive index pairing of steps ↔ failure modes → wrong CONFIRMS
- Lab-only evidence language (“filter LED”) when users say “won’t start”
- Silent ignore of unknown list keys forever → surface `tbox_extension` candidates

## New vertical blanks

```text
Domain name: ________________
Entities + identity keys: ________________
Evidence → hypothesis → action chain: ________________
Sources (SoR names): ________________
5 golden phrases + expected top hypothesis: ________________
```

## As-built map

- Builder: `graph/enterprise_pipeline/transformers/ontology_builder.py`
- Validate: `graph/enterprise_pipeline/ontology_validate.py`
- Ontology export: `docs/ontology/`, graph export helpers
- Packs: `data/pipeline_sources/`
- Tests: `tests/test_multi_source_tbox_abox.py`
- Patterns (DL origin, sparse, scale): `docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`
- Operator mechanism: `docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`
- Interview narrative: `docs/interview/Master-This-Codebase.md`

## Exit (P1 / pack work)

Validate pack under shared TBox with **no** per-entity OWL file.
