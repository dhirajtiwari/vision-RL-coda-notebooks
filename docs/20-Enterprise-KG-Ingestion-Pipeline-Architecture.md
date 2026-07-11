# Enterprise Knowledge Graph Ingestion Pipeline Architecture

**Audience:** architects, data engineers, knowledge admins
**Scope:** How real enterprises build pipelines from **structured / semi-structured / unstructured** sources into a **Neo4j knowledge graph**, how we map industry practice onto this application, and how **bootstrap vs incremental** and **batch vs on-demand** are designed.

---

## 1. Industry practice (authoritative patterns)

Enterprise knowledge graphs are not “import a CSV into Neo4j once.” Industry practice (Neo4j Graph ETL guidance, enterprise KG design literature, data platform practice) converges on:

### 1.1 Layers

| Layer | Purpose |
|-------|---------|
| **Source systems** | ERP/PIM, CRM, FSM, claims, lakes, document stores, tickets |
| **Ingestion** | Extract (batch, CDC, API, file drop) |
| **Preprocessing / staging** | Clean, type, dedupe, PII, quality scores |
| **Semantic mapping** | Map fields → ontology concepts (“semantic lift”) |
| **Entity resolution** | Golden records across sources |
| **Graph materialization** | MERGE into Neo4j with constraints |
| **Validation & promote** | Smoke / quality gates → staging → production |
| **Governance / lineage** | Who loaded what, from which source, when (PROV / audit) |

### 1.2 Source types

| Type | Examples | Typical tools / techniques |
|------|----------|----------------------------|
| **Structured** | RDBMS, APIs, CRM/PIM tables | JDBC/API connectors, dbt, Airflow/Prefect/Dagster, Spark |
| **Semi-structured** | JSON, JSONL, CSV, XML, Avro | Pandas/Polars, schema-on-read, JSON Schema validation |
| **Unstructured** | PDFs, manuals, tickets, emails | OCR (optional), text extract, NLP/LLM NER → triples, human review |

### 1.3 Load modes

| Mode | When | Pattern |
|------|------|---------|
| **Bootstrap (full)** | Project build / rebaseline | Full extract → preprocess → map → MERGE all |
| **Incremental (batch)** | Nightly / hourly live | CDC or watermark / changelog → delta MERGE |
| **On-demand** | Admin UI, hotfix, new product onboard | Same pipeline code, trigger = human or API |
| **Streaming** | High-volume IoT (optional later) | Kafka/CDC → micro-batches into graph |

### 1.4 Tools seniors often recommend (stack choices)

| Concern | Common enterprise choices | What we use in *this* demo platform |
|---------|---------------------------|-------------------------------------|
| Orchestration | Airflow, Dagster, Prefect, Azure DF | **In-process pipeline registry + orchestrator** (embeddable; same contracts as Airflow tasks) |
| Graph store | Neo4j, Neptune, TigerGraph | **Neo4j** |
| Transform | Spark, dbt, Python | **Python transformers** (deterministic, testable) |
| Unstructured → graph | spaCy, LLM extract, Unstructured.io | **Rule + pattern extractor** over text fixtures (LLM-optional hook) |
| Lineage | OpenLineage, PROV-O | **JSONL lineage + PROV-style fields** |
| Quality gates | Great Expectations, custom tests | **Smoke scenarios + preprocess quality report** |
| Promote | Staging DB → prod | **Catalog staging → smoke → human approve → promote MERGE** |

We intentionally keep the **control plane in-app** so the UI can run pipelines without requiring a separate Airflow cluster in the demo—while modeling the same stages an Airflow DAG would own.

---

## 2. Current application review (before expansion)

### Already present

| Capability | Module |
|------------|--------|
| Structured connectors (PIM/CRM/FSM/Claims) | `graph/enterprise_pipeline/connectors/*` |
| Ontology transform | `OntologyBuilder` |
| ETL → smoke → promote | `orchestrator.py`, pipelines/* |
| Admin API gates | `/admin/pipeline/*` |
| Basic Admin UI | frontend Admin view |
| Lineage batches | `utils/lineage_store.py` |

### Gaps this design closes

| Gap | Solution |
|-----|----------|
| No explicit multi-source-type pipelines | Registry: structured / semi / unstructured / preprocess / bootstrap / incremental |
| Weak preprocess stage | Dedicated preprocess + quality report |
| No unstructured path | Manual/text artifact pipeline → provisional triples |
| Limited run modes | `full` vs `incremental` vs `on_demand` on each run |
| Thin pipeline UI | **Knowledge Pipeline Control Room** multi-step UX |
| Sparse multi-artifact fixtures | Rich fixture packs under `data/pipeline_sources/` |

---

## 3. Target multi-pipeline architecture (this app)

```text
┌─────────────────────────────────────────────────────────────────┐
│  UI: Knowledge Pipeline Control Room  (Admin)                   │
│  run · dry-run · validate · approve · promote · history         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST /admin/kg-pipelines/*
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Pipeline Control Plane  (registry + runner + run store)        │
│  modes: bootstrap | incremental | on_demand                     │
└──────┬──────────────┬──────────────────┬────────────────────────┘
       │              │                  │
       ▼              ▼                  ▼
 Structured      Semi-structured    Unstructured
 connectors      JSON/CSV/JSONL     manuals/tickets
       │              │                  │
       └──────────────┼──────────────────┘
                      ▼
              Preprocess + quality
                      ▼
           Ontology map / merge catalog
                      ▼
         Smoke → Review → Promote → Neo4j
                      ▼
                 Lineage + cache invalidate
```

### Pipelines (first-class)

| ID | Name | Sources | Typical mode |
|----|------|---------|--------------|
| `structured_extract` | Structured enterprise extract | PIM/CRM/FSM/Claims API or fixtures | bootstrap / incremental / on_demand |
| `semi_structured_ingest` | Semi-structured files | CSV/JSONL work orders, parts lists | bootstrap / incremental |
| `unstructured_extract` | Unstructured text → provisional triples | Manuals, ticket dumps | bootstrap / on_demand |
| `preprocess_normalize` | Clean, dedupe, validate | Staging artifacts from above | always before materialize |
| `knowledge_materialize` | Ontology build + catalog write | Preprocessed records | full / incremental |
| `smoke_validate` | Scenario gate | Live Neo4j / catalog | gate |
| `promote_graph` | MERGE to Neo4j | Approved catalog | on_demand after gate |
| `bootstrap_all` | Full first-time chain | all | **project build phase** |
| `incremental_sync` | Live delta chain | structured + semi deltas | **scheduled live** |

---

## 4. Batch vs on-demand (decision)

| Situation | Mode | Why |
|-----------|------|-----|
| Initial project build / rebaseline | **Bootstrap batch** (`bootstrap_all`) | Full consistency, rebuild indexes/constraints |
| Nightly live sync | **Incremental batch** (`incremental_sync`) | Only deltas; lower cost |
| New product / emergency fix | **On-demand** from UI | Human-triggered, same code path |
| Streaming IoT | Out of scope for demo | Add Kafka later if needed |

**Rule:** *Same pipeline functions*; only **trigger** and **watermark/delta scope** change.

---

## 5. UI/UX principles (Control Room)

1. **Pipeline catalog** — cards with type, last run, status, source kinds
2. **Run drawer** — mode (bootstrap/incremental/on_demand), dry-run toggle, target env (staging/prod)
3. **Live run log** — stages with counts, errors, quality scores
4. **Artifact browser** — fixtures and generated staging files
5. **Gate strip** — Dry-run → Preprocess → Materialize → Smoke → Approve → Promote
6. **History** — lineage timeline
7. **RBAC cue** — admin token / future OIDC

---

## 6. Mapping to code (implementation)

| Concern | Module |
|---------|--------|
| Registry + runner | `graph/enterprise_pipeline/control_plane/` |
| Source packs | `data/pipeline_sources/{structured,semi,unstructured}/` |
| Preprocess | `.../preprocess/normalize.py` |
| Unstructured extract | `.../extractors/unstructured_text.py` |
| Semi ingest | `.../extractors/semi_structured.py` |
| API | `/admin/kg-pipelines/*` |
| UI | Admin → Knowledge Pipeline Control Room |
| Tests | `tests/test_kg_ingestion_pipelines.py` |

---

## 7. References (practice sources)

1. Neo4j — Graph ETL basics & knowledge graph construction guidance
2. Enterprise Knowledge — EKG design: ingestion, ontology, consumption layers
3. Industry EKG pattern: batch + CDC + semantic mapping (“semantic lift”)
4. W3C PROV-O — provenance for pipeline activities
5. DAMA-DMBOK themes — quality, lineage, metadata (conceptual)

*Implementation in this repo is intentionally lightweight and demo-runnable while matching the stage boundaries seniors expect in production platforms.*

---

## 8. Related docs in this repo

| Doc | Purpose |
|-----|---------|
| [`21-KG-Ingestion-Step-by-Step-Runbook.md`](21-KG-Ingestion-Step-by-Step-Runbook.md) | **How to run** bootstrap, incremental, UI, API, troubleshoot |
| [`todo-kg-ingestion-pipelines.md`](todo-kg-ingestion-pipelines.md) | Feature checklist + production gaps for this workstream |
| [`PIPELINE-AND-MODULE-GUIDE.md`](PIPELINE-AND-MODULE-GUIDE.md) | Classic ETL phases 0–5 |
| Root [`todo.md`](../todo.md) | Full product blueprint (all sessions) |
