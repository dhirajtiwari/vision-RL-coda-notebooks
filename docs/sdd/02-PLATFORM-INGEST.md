# 02 — Platform ingest / control plane

**Load when:** P2 materialize/promote, P4 Admin, P8 multi-pack fleet.
**Ontology rule detail:** also open `05-DOMAIN-ONTOLOGY.md` if changing TBox/ABox shapes.

## Pipeline shape (non-negotiable)

```text
Connectors / extractors
  → parallel extract
  → serial OntologyBuilder / transform (ABox under shared TBox)
  → selection-scoped catalog upsert
  → shape validate
  → MERGE staging → MERGE production
```

## Registry capabilities (as-built IDs)

| ID | Purpose |
|----|---------|
| `structured_extract` | PIM / CRM / FSM / Claims |
| `semi_structured_ingest` | CSV / JSONL |
| `unstructured_extract` | Manuals / tickets text |
| `preprocess_normalize` | Quality / normalize |
| `knowledge_materialize` | Build catalog ABox |
| `smoke_validate` | Scenario gate |
| `promote_graph` | MERGE (`target_env`) |
| `bootstrap_all` | Chain through smoke (no auto-promote) |
| `incremental_sync` | Extract + preprocess + materialize |

## Operator sequence

Sources → Fetch (dry-run) → Select products → Validate ABox → Materialize → Smoke → Approve → Promote **staging** → Promote **production** → optional **session reset-for-next-cycle**.

## Selection / promote rules

- Materialize/promote **only** selected IDs when selection exists.
- Empty selection + actionable work → **fail closed**.
- Chat does **not** read staging.
- Split **fleet** status vs **selection/batch** status (avoid false UPDATE alarms).
- Catalog-authoritative fleet diff after promote (not raw PIM-only eternal UPDATE).
- Bulletin-only metadata must not force pending UPDATE without ABox growth.
- After fleet in-sync / idle complete wizard → reset path for next cycle.

## As-built map (this repo)

| Concern | Path |
|---------|------|
| Registry / runner | `graph/enterprise_pipeline/control_plane/` |
| ABox builder | `graph/enterprise_pipeline/transformers/ontology_builder.py` |
| Knowledge ETL | `graph/enterprise_pipeline/pipelines/knowledge_etl.py` |
| Populate | `graph/populate_graph.py` |
| Entity delta / change preview | `entity_delta`, `change_preview` under enterprise pipeline |
| Admin API | `api/main.py` (`/admin/pipeline/*`, `/admin/kg-pipelines/*`) |

## Exit

- P2: nodes in production after promote
- P4: wizard E2E with selection scope
- P8: second multi-source pack + reset story
