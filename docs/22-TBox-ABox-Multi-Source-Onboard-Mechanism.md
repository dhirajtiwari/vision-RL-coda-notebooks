# TBox / ABox multi-source onboard mechanism

**Status:** Current platform design (WarrantyGraph / remote diagnostics)
**Audience:** Operators, engineers, reviewers
**Related:** `15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md`, `20-Enterprise-KG-Ingestion-Pipeline-Architecture.md`, `21-KG-Ingestion-Step-by-Step-Runbook.md`, `graph/enterprise_pipeline/ontology_validate.py`, `graph/rdf_ontology_export.py`

---

## 1. Purpose

This document records **how ontology and multi-source product onboarding work in this application**, so we do not confuse:

| Concept | Meaning |
|--------|---------|
| **TBox (schema)** | Shared domain vocabulary: *kinds* of things (classes, properties) |
| **ABox (instances)** | Facts about a specific product (symptoms, failure modes, assets, …) |
| **Source artifacts** | Files / connector payloads that feed extract → transform → validate → promote |
| **Demo shortcuts** | Hand-authored fixtures and keyword maps that stand in for real enterprise systems |

**Rule of thumb:** A **new product** is almost always **new ABox under an existing TBox**. A **new ontology class** is a rare **TBox extension** and is governance-owned, not auto-generated per SKU.

---

## 2. Build order (W3C-aligned)

Recommended knowledge-base build order (also exported by `ontology_validate.tbox_summary()`):

```text
1. Define / freeze domain TBox once (OWL classes + properties) — shared rule book
2. Onboard NEW product = author ABox instances under existing classes
3. Only if domain needs NEW *types* of things → extend TBox (rare)
4. Validate ABox against TBox + shapes (fail-closed)
5. Materialize conforming ABox → promote to operational Neo4j
6. Export RDF/OWL for audit / interchange (optional)
```

| Step | Runtime projection |
|------|-------------------|
| TBox | `graph/rdf_ontology_export.py` (`CLASSES`, `OBJECT_PROPERTIES`), `docs/ontology/*.ttl` |
| Shapes / validate | `graph/enterprise_pipeline/ontology_validate.py` |
| ABox build | `transformers/ontology_builder.py` + enterprise connectors |
| Promote | `populate_graph.py` → Neo4j staging (`:7688`) / production (`:7687`) |
| Diagnose | GraphRAG over **production** Neo4j only |

Neo4j is the **operational graph**, not a substitute for defining the ontology.

---

## 3. What is TBox vs ABox in this product

### 3.1 TBox (shared)

Examples of domain classes (not product-specific files):

- Product, Model, SKU, Asset
- Symptom, FailureMode, DiagnosticStep
- Part, Component, ErrorCode
- HistoricalResolution, Claim, WarrantyPolicy

Relationships (examples): `HAS_SYMPTOM`, `CAN_HAVE`, `INDICATES`, `CONFIRMS`, `REQUIRES_PART`, `INSTANCE_OF`, …

**Owners:** platform / ontology governance.
**Change frequency:** low.
**Not created** when adding `esp-001`, `hmd-001`, etc.

### 3.2 ABox (product instances)

Examples for product `esp-001`:

- Symptom `esp-001-s02` “Error code E05…”
- FailureMode `esp-001-fm01` “Boiler NTC Sensor…”
- Link `esp-001-d02 CONFIRMS esp-001-fm01`
- Asset `AST-ESP001-2200` `INSTANCE_OF` Product `esp-001`

**Owners:** product / service / warranty data pipelines.
**Change frequency:** high (new products, bulletins, resolutions).

### 3.3 When TBox *would* change

Only if sources introduce a **new kind of entity** not in the domain model, e.g. a top-level list key with no class mapping.

Detection (does **not** auto-extend TBox):

- `graph/enterprise_pipeline/ingest_plan.py` → `scan_tbox_extension_candidates()`
- Admin ingest plan → **TBox candidates** + acknowledge gate

Severity **high** if the suggested class name is not already in `CLASSES`.

---

## 4. Multi-source feed → graph (mechanism)

### 4.1 Source types

| Type | Demo location | Intended enterprise system |
|------|---------------|----------------------------|
| Structured enterprise | `data/enterprise_sources/pim_catalog.json` | PIM / PLM |
| FSM | `fsm_work_orders.json` | Field service management |
| Claims | `claims_history.json` | Warranty / claims |
| CRM | `crm_assets.json` | Installed base / assets |
| Structured pipeline notes | `data/pipeline_sources/structured/` | Change tickets / bulletins JSON |
| Semi-structured | `semi_structured/**` | Parts CSV, WO JSONL |
| Unstructured | `unstructured/**` | Manuals, tickets, tech notes |

**Manifest example:** `data/pipeline_sources/ESP_001_MULTI_SOURCE_MANIFEST.json`, `HMD_001_MULTI_SOURCE_MANIFEST.json`.

### 4.2 Control-plane pipelines

| Pipeline id | Role |
|-------------|------|
| `structured_extract` | PIM/FSM/Claims/CRM connectors |
| `semi_structured_ingest` | CSV / JSONL load |
| `unstructured_extract` | Pattern extract + product hints |
| `preprocess_normalize` | Quality / provisional notes |
| `knowledge_materialize` | OntologyBuilder → enterprise catalog (selection-scoped) |
| `smoke_validate` | Diagnosis scenarios |
| `promote_graph` | MERGE into Neo4j (`staging` \| `production`) |
| `bootstrap_all` / `incremental_sync` | Chains of the above |

Admin wizard maps to: **Sources → Fetch → Select → Validate ABox → Materialize → Smoke → Approve → Promote**.

### 4.3 Core transform

```text
Connectors (PIM, FSM, Claims, CRM)
        │
        ▼
OntologyBuilder.build_catalog_payload()
  • Core ProductKnowledge (Pydantic ABox)
  • Re-attach rich keys from PIM (model, SKU, components, error_codes, CONFIRMS, …)
  • Merge CRM assets + Claims closed claims into catalog ABox
        │
        ▼
enterprise_knowledge_catalog.json  (selection upsert when product_ids set)
        │
        ▼
ontology_validate (ABox vs TBox shapes)
        │
        ▼
populate_graph → Neo4j (staging then production)
```

Important implementation notes:

- **Selection-scoped materialize** upserts only selected product bundles into the catalog (plus related assets/claims for those products).
- **Promote** is fail-closed on empty selection when actionable delta exists.
- **Chat** reads **production** Neo4j only.

### 4.4 What “Fetch” computes

Fetch (dry-run ETL) rebuilds a **fleet change preview**:

- **NEW** — product id not in production Neo4j
- **Pending UPDATE** — catalog/sources ABox richer than live graph (core edges), not bulletin-only noise
- **Already in sync** — core ABox counts match production

Entity-delta panel re-checks **catalog ↔ Neo4j** for the **selection** (can show IN SYNC vs NEEDS MATERIALIZE even when fleet labels differ). Use **Drop IN SYNC from selection** to keep the batch honest.

### 4.5 Session lifecycle after promote

When production promote succeeds and fleet has **0 NEW / 0 UPDATE**:

- Session can **reset for next cycle** (`POST /admin/pipeline/session/reset-for-next-cycle`)
- Clears selection, step gates, smoke/approve/materialize flags
- **Does not** delete Neo4j or catalog ABox

UI: **Reset wizard for next plan** / auto-reset after idle Refresh plan.

---

## 5. Adding a fresh NEW product (correct procedure)

### 5.1 Do **not** create a product-specific ontology file

Incorrect mental model:

```text
esp-001 → invent new OWL schema for espresso → load schema → load instances
```

Correct mental model:

```text
Shared TBox (already loaded)
    → multi-source ABox pack for esp-001
    → validate under existing classes
    → materialize / promote instances
```

### 5.2 What to add as **source artifacts** (ABox + connectors)

For a multi-source NEW product (example `esp-001`):

1. **PIM** — full product bundle under known list keys (`symptoms`, `failure_modes`, `diagnostic_steps`, `parts`, `components`, `error_codes`, links, `model`, `skus`, …) with fields required by Pydantic models (e.g. FailureMode needs `estimated_repair_time_minutes`, `safety_notes`; steps use `description` / `expected_outcome`).
2. **FSM** — closed work orders → historical resolutions.
3. **Claims** — closed claims tied to asset / FM / part.
4. **CRM** — registered asset for customer test path.
5. **Pipeline structured / semi / unstructured** — inventory + narrative extract inputs.
6. **Manifest** — source map + test phrases + admin path.

### 5.3 What the pipeline builds (not hand-edited per product)

| Built by pipeline | Not “new schema” |
|-------------------|------------------|
| Catalog ABox from connectors | Domain TBox |
| Provenance stamps | New OWL classes |
| Neo4j nodes/edges | Per-product ontology language |
| Entity delta vs production | Artificial schema files in `docs/ontology/` per SKU |

### 5.4 Demo-only wiring (honest limitation)

These are **application shortcuts**, not ontology:

| Shortcut | Role |
|----------|------|
| `PRODUCT_KEYWORDS` in `graph_rag.py` | Chat product resolution when graph/CRM not bound |
| Unstructured filename stems / keyword hints | Route docs to `product_id` before graph is loaded |
| Fixture JSON under `data/enterprise_sources` | Stand-in for live PIM/FSM/Claims/CRM APIs |

Enterprise target: connectors + product master + asset binding; keywords become optional boosts, not the source of truth.

---

## 6. Validate vs TBox extension (operator view)

| Admin signal | Meaning | Action |
|--------------|---------|--------|
| **NEW product** | Id absent from production | Select → validate ABox → materialize → promote |
| **Pending UPDATE** | Existing product, richer ABox pending | Same path for selected ids only |
| **Already in sync** | Core ABox matches production | No re-work; data remains in graph |
| **TBox candidates** | Unknown source keys | Review; acknowledge or map into TBox — **do not** treat as normal product onboard |
| **IN SYNC** (entity delta) | Catalog ids present on Neo4j for selection | Drop from batch if mixed with real work |
| **NEEDS MATERIALIZE** | Not in enterprise catalog yet | Validate → Materialize before entity matrix fills |

---

## 7. Code map (quick reference)

| Concern | Module / path |
|---------|----------------|
| OWL classes / properties / Turtle export | `graph/rdf_ontology_export.py` |
| ABox shape validation | `graph/enterprise_pipeline/ontology_validate.py` |
| Connector → catalog | `graph/enterprise_pipeline/transformers/ontology_builder.py` |
| Knowledge ETL / selection merge | `graph/enterprise_pipeline/pipelines/knowledge_etl.py` |
| Change preview NEW/UPDATE/in-sync | `graph/enterprise_pipeline/change_preview.py` |
| Ingest plan + TBox scan | `graph/enterprise_pipeline/ingest_plan.py` |
| Entity delta catalog vs Neo4j | `graph/enterprise_pipeline/entity_delta.py` |
| Neo4j MERGE | `graph/populate_graph.py` |
| Admin APIs | `api/main.py` (`/admin/pipeline/*`, session reset) |
| Static schema TTL | `docs/ontology/warranty-diagnosis*.ttl` |

---

## 8. Demo packs using this mechanism

| Product | Intent | Manifest |
|---------|--------|----------|
| `hmd-001` DryZone dehumidifier | Multi-source NEW (climate) | `HMD_001_MULTI_SOURCE_MANIFEST.json` |
| `esp-001` BrewBar espresso | Multi-source NEW (kitchen) — **sources only** until operator Fetch | `ESP_001_MULTI_SOURCE_MANIFEST.json` |

Neither pack adds TBox. Both are ABox under the shared warranty-diagnosis ontology.

---

## 9. Next steps (recommended)

Ordered toward a more enterprise-faithful path while keeping the TBox/ABox split.

### Phase A — Prove the mechanism end-to-end (operator)

1. **Reset wizard for next plan** (fleet idle).
2. **Fetch** with `esp-001` sources on disk → expect **NEW `esp-001`**.
3. Select **only** `esp-001` → Validate ABox → Materialize → Smoke → Approve → Promote staging → production.
4. Customer chat: **CUST-10120 / AST-ESP001-2200** with manifest phrases.
5. Confirm Explore path shows **CONFIRMS** for espresso steps.

### Phase B — Reduce artificial product wiring

6. Prefer **CRM asset + product name/graph** for diagnose binding; shrink reliance on `PRODUCT_KEYWORDS` for new packs.
7. Unstructured: product_id from **filename convention + optional structured pointer**, not growing hardcoded brand lists.
8. Document “source pack contract” (required keys, Pydantic fields) as the only authoring surface for NEW products.

### Phase C — Connector realism

9. Point connectors at **mock enterprise apps** / HTTP fixtures (`simulation/`, `integrations/`) rather than only static JSON edits.
10. Incremental path: semi/unstructured deltas → preprocess → materialize selection (no full catalog rewrite).
11. Lineage: every materialize/promote batch already writes under `data/lineage/` — surface pack id + source fingerprint in Admin audit consistently.

### Phase D — TBox governance (only when needed)

12. Keep `scan_tbox_extension_candidates` as the gate for unknown keys.
13. If a real new class appears: ADR + update `rdf_ontology_export.CLASSES` / Turtle + shapes — **never** auto-merge from a product pack.
14. Optional: SHACL file export alongside Turtle for external reviewers.

### Phase E — Hardening

15. Automated test: “NEW product pack validates against TBox without schema file.”
16. Automated test: “unknown list key → tbox_extension high severity.”
17. CI smoke: dry-run ETL + validate selection for `esp-001` / `hmd-001` fixtures.

---

## 10. Decision record (summary)

| Decision | Choice |
|----------|--------|
| Per-product ontology schema? | **No** |
| Shared domain TBox? | **Yes** (code + `docs/ontology/`) |
| Multi-source NEW product? | **ABox packs + connectors** |
| Auto-extend TBox from sources? | **No** — detect and review only |
| Pipeline builds schema per onboard? | **No** — pipeline builds/validates/promotes **instances** |
| Demo fixtures? | Allowed as stand-ins; document as non-production |

---

## 11. One-page flow

```text
                    ┌─────────────────────────┐
                    │  Domain TBox (shared)   │
                    │  OWL classes/properties │
                    └───────────┬─────────────┘
                                │ shapes / validate
     ┌──────────┐  ┌──────────┐ │ ┌────────────┐
     │ PIM/SKU  │  │ FSM / HR │ │ │ Claims/CRM │
     │ manuals  │  │ semi WO  │ │ │ assets     │
     └────┬─────┘  └────┬─────┘ │ └─────┬──────┘
          │             │       │       │
          └─────────────┴───────┴───────┘
                        │
                        ▼
              OntologyBuilder (ABox)
                        │
                        ▼
              Validate vs TBox ── fail ──► fix pack or TBox review
                        │ ok
                        ▼
              Materialize catalog (selection)
                        │
                        ▼
              Promote Neo4j staging → production
                        │
                        ▼
              Diagnosis Chat / Explorer (production)
```

---

*Document version: 2026-07-11 — reflects multi-source packs `hmd-001` / `esp-001`, dual Neo4j, selection-scoped ETL, session reset-for-next-cycle, and TBox-extension scan.*
