# TODO — Multi-Source Knowledge Graph Ingestion Pipelines

> **Scope:** Structured / semi-structured / unstructured sources → preprocess → ontology catalog → smoke → promote → Neo4j.
> **Companion architecture:** [`20-Enterprise-KG-Ingestion-Pipeline-Architecture.md`](20-Enterprise-KG-Ingestion-Pipeline-Architecture.md)
> **Step-by-step runbook:** [`21-KG-Ingestion-Step-by-Step-Runbook.md`](21-KG-Ingestion-Step-by-Step-Runbook.md)
> **Legend:** `[x]` done · `[~]` partial/demo · `[ ]` gap

---

## 1. Architecture & design decisions

- [x] Document industry layers (ingest → preprocess → semantic map → materialize → gate → promote → lineage)
- [x] Map source types: structured / semi / unstructured
- [x] Define run modes: **bootstrap** (first-time) · **incremental** (live) · **on_demand** (admin)
- [x] Same pipeline code for batch schedule vs UI trigger
- [x] In-app control plane (Airflow-shaped stages without requiring Airflow for demo)
- [x] Architecture doc `docs/20-…`
- [x] Step-by-step runbook `docs/21-…`
- [ ] Optional: export DAG stubs for Airflow/Dagster/Prefect

---

## 2. Control plane (platform)

- [x] Pipeline models (`control_plane/models.py`)
- [x] Registry of pipelines (`registry.py`)
- [x] Runner with modes + dry_run + target_env (`runner.py`)
- [x] Run history store JSON + index (`run_store.py`)
- [x] Package exports `__init__.py`
- [x] Dry-run smoke does **not** fail without Neo4j
- [ ] Persist long-running job queue (async workers)
- [ ] Concurrent run locking (one promote at a time)
- [ ] RBAC per pipeline action (beyond admin token)

---

## 3. Pipelines (first-class)

| ID | Status | Notes |
|----|--------|-------|
| `structured_extract` | [x] | Reuses PIM/CRM/FSM/Claims connectors |
| `semi_structured_ingest` | [x] | CSV/JSONL fixtures |
| `unstructured_extract` | [x] | Pattern extract from txt/md |
| `preprocess_normalize` | [x] | Dedupe + quality score |
| `knowledge_materialize` | [x] | OntologyBuilder catalog write |
| `smoke_validate` | [x] | Scenario gate (live Neo4j) |
| `promote_graph` | [x] | MERGE Neo4j staging/production label |
| `bootstrap_all` | [x] | Full chain for project build |
| `incremental_sync` | [x] | Live delta chain (no auto-promote) |
| CDC / Kafka streaming | [ ] | Future |
| PDF OCR path | [ ] | Unstructured.io / OCR hook |
| LLM NER extract | [ ] | Optional gateway hook |

---

## 4. Source adapters & preprocess

- [x] Semi-structured loader (CSV/JSONL) + normalizers
- [x] Unstructured pattern extractor (error codes, symptom hints)
- [x] Preprocess quality (required fields, dedupe, pass_rate)
- [x] Staging write under `data/pipeline_staging/`
- [~] Incremental only trims work-order window (watermark/CDC not full)
- [ ] Entity resolution / golden records across sources
- [ ] PII redaction stage for tickets
- [ ] JSON Schema validation per artifact type

---

## 5. Fixtures & test artifacts

- [x] `data/pipeline_sources/semi_structured/bootstrap/` (work orders + parts)
- [x] `data/pipeline_sources/semi_structured/incremental/` (delta + bad row for quality)
- [x] `data/pipeline_sources/unstructured/bootstrap/` (manual + tickets)
- [x] Structured sources documented → `enterprise_sources/` + mock API
- [x] Tests `tests/test_kg_ingestion_pipelines.py` (registry, extract, preprocess, API, bootstrap dry)
- [ ] Golden expected stage metrics snapshot file
- [ ] Contract tests against mock enterprise HTTP when `:8090` up

---

## 6. API (control plane)

- [x] `GET /admin/kg-pipelines` — catalog
- [x] `POST /admin/kg-pipelines/{id}/run` — mode, dry_run, target_env
- [x] `GET /admin/kg-pipelines/runs` — history
- [x] `GET /admin/kg-pipelines/runs/{run_id}` — detail
- [x] `GET /admin/kg-pipelines/artifacts` — source + staging files
- [x] Admin token guard (shared with other admin routes)
- [x] Static routes (`runs`, `artifacts`) registered before `{pipeline_id}`
- [ ] WebSocket/SSE live log streaming
- [ ] Cancel running job

---

## 7. UI/UX — Knowledge Pipeline Control Room

- [x] Admin tab section: Control Room
- [x] Pipeline cards with source_kind + stages
- [x] Mode selector (bootstrap / incremental / on_demand)
- [x] Dry-run toggle
- [x] Target env staging | production
- [x] One-click bootstrap_all / incremental_sync / promote
- [x] Last run stage log
- [x] Run history list
- [x] Artifact browser (sources + staging)
- [x] Legacy gates still available (dry-run ETL → smoke → approve → promote)
- [ ] Diff preview: catalog before/after
- [ ] Per-stage expandable metrics charts
- [ ] Role-based UI (viewer vs operator vs approver)
- [ ] Confirm modal before production promote

---

## 8. Integration with existing ETL / graph

- [x] Reuse `run_knowledge_etl` for structured + materialize
- [x] Reuse `run_smoke_validation` / `run_staging_promotion` / `populate_graph`
- [x] Cache invalidate on promote
- [x] Lineage still via ETL batches + new pipeline run store
- [~] Semi/unstructured enrich catalog metadata (`pipeline_ingest` block) but do not yet fully merge provisional symptoms into Product HAS_SYMPTOM edges
- [ ] Full semantic merge of provisional symptoms into ontology as first-class nodes (with human approval)

---

## 9. How operators run it (checklist)

### First-time project build (bootstrap)

- [ ] Neo4j up; `pip install -r requirements.txt`
- [ ] Fixtures present under `data/pipeline_sources/`
- [ ] API up: `uvicorn api.main:app --port 8080`
- [ ] UI Admin → Control Room → mode **bootstrap**, dry-run **on** → `bootstrap_all`
- [ ] Review stages + artifacts
- [ ] Dry-run **off** → `bootstrap_all` again (writes catalog)
- [ ] Ensure Neo4j populated (or run `promote_graph` / legacy promote)
- [ ] `smoke_validate` (dry-run off) must pass before trusting prod
- [ ] Mode production + `promote_graph` if separate from staging path

### Live operations (incremental)

- [ ] Drop deltas into `semi_structured/incremental/` (and optional structured via connectors)
- [ ] Schedule or UI: `incremental_sync` (dry-run off)
- [ ] `smoke_validate`
- [ ] Human approve (legacy gate or policy)
- [ ] `promote_graph` target production

### On-demand hotfix

- [ ] Run single pipeline (e.g. `unstructured_extract`) on_demand
- [ ] `preprocess_normalize` → `knowledge_materialize` → smoke → promote

---

## 10. Production gaps (honest)

| Priority | Item |
|----------|------|
| P0 | Real connectors + secrets management |
| P0 | OIDC/RBAC for Control Room |
| P1 | Async workers + job queue |
| P1 | Separate Neo4j staging vs prod instances |
| P1 | Watermark/CDC for true incremental structured |
| P2 | LLM/NLP extraction for unstructured with review queue |
| P2 | OpenLineage export |
| P2 | Great Expectations / formal data contracts |

---

## 11. Acceptance criteria (this demo)

- [x] At least 3 source kinds runnable
- [x] Bootstrap vs incremental modes
- [x] Dry-run path that does not require Neo4j for non-smoke stages
- [x] Fixtures + automated tests green
- [x] API + Admin Control Room UI
- [x] Architecture + step-by-step docs
- [x] todo tracked (this file)

---

*Update checkboxes as you harden toward production. Keep gaps honest.*
