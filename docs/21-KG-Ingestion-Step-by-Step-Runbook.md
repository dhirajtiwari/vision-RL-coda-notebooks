# Knowledge Graph Ingestion — Step-by-Step Runbook

**How to make multi-source Neo4j pipelines work in this application**
Architecture theory: [`20-Enterprise-KG-Ingestion-Pipeline-Architecture.md`](20-Enterprise-KG-Ingestion-Pipeline-Architecture.md)
Checklist: [`todo-kg-ingestion-pipelines.md`](todo-kg-ingestion-pipelines.md)

---

## 0. Mental model (30 seconds)

```text
SOURCES                    STAGING                    GATES                 GRAPH
─────────                  ───────                    ─────                 ─────
Structured (API/fixtures) ─┐
Semi (CSV/JSONL)         ─┼→ preprocess → catalog  → smoke → approve → Neo4j MERGE
Unstructured (txt/md)    ─┘   quality      JSON       scenarios   human
```

| Mode | When you use it |
|------|-----------------|
| **bootstrap** | First project build, full rebaseline |
| **incremental** | Live system, only new/changed files or deltas |
| **on_demand** | Admin clicks Run on one pipeline |

| Trigger | Same pipelines? |
|---------|-----------------|
| CLI / pytest / cron | Yes |
| Admin UI Control Room | Yes |
| REST `/admin/kg-pipelines/.../run` | Yes |

---

## 1. Prerequisites

### 1.1 Software

```bash
cd /Users/dhiraj/diagnosis-chatbot-demo/diagnostic-chatbot
source venv/bin/activate
pip install -r requirements.txt
# Infra (production Neo4j :7687, staging Neo4j :7688, Redis :6379)
open -a Docker   # if needed
docker compose -f docker/docker-compose.infra.yaml up -d
# If you already use neo4j-demo on 7687, still start staging:
docker compose -f docker/docker-compose.infra.yaml up -d neo4j-staging redis
export REDIS_URL=redis://localhost:6379/0
export NEO4J_URI=bolt://localhost:7687
export NEO4J_STAGING_URI=bolt://localhost:7688
```

| Need | For |
|------|-----|
| Python 3.12 + venv | Pipelines + API |
| Neo4j **production** `:7687` | Live `/diagnose` reads |
| Neo4j **staging** `:7688` | Promote-first target; validate before prod |
| Redis `:6379` | Shared rate limit, subgraph + **diagnose** cache |
| Node (optional) | Admin UI Control Room |
| Docker | Neo4j prod/staging + Redis |

### 1.2 Verify fixtures exist

```bash
ls data/pipeline_sources/semi_structured/bootstrap/
ls data/pipeline_sources/unstructured/bootstrap/
ls data/enterprise_sources/   # structured connectors
```

Expected semi: `work_orders.jsonl`, `parts_delta.csv`
Expected unstructured: `*.txt` / `*.md` manuals/tickets

### 1.3 Start services

```bash
# Terminal A — Neo4j must be up for promote/smoke (real runs)

# Terminal B — API
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8080

# Terminal C — UI (optional)
cd frontend && npm run dev   # http://localhost:3000 → Admin
```

Health:

```bash
curl -s http://localhost:8080/health | python -m json.tool
curl -s http://localhost:8080/admin/kg-pipelines | python -m json.tool | head
```

If `admin_api_token` is set, pass header: `-H "X-Admin-Token: $TOKEN"`.

---

## 2. What each pipeline does (What / Where / When / How)

| Pipeline ID | What | Where (code) | When | How |
|-------------|------|--------------|------|-----|
| `structured_extract` | Pull PIM/CRM/FSM/Claims | `runner._run_structured` → `run_knowledge_etl` | Bootstrap / live / on demand | Parallel connectors → catalog stats |
| `semi_structured_ingest` | Load CSV/JSONL | `extractors/semi_structured.py` | Bootstrap folder or incremental folder | Normalize rows → staging JSON |
| `unstructured_extract` | Text → provisional symptoms/codes | `extractors/unstructured_text.py` | Bootstrap / on demand | Regex + heuristics |
| `preprocess_normalize` | Quality gate | `preprocess/normalize.py` | After extracts | Dedupe, required fields, pass_rate |
| `knowledge_materialize` | Write ontology catalog | `run_knowledge_etl` + annotate `pipeline_ingest` | After preprocess | OntologyBuilder → enterprise catalog files |
| `smoke_validate` | Diagnosis scenario gate | `run_smoke_validation` | Before promote | Needs Neo4j; skipped on dry_run |
| `promote_graph` | Load Neo4j | `populate_graph` / staging_promotion | After approval | Constraints + MERGE + cache invalidate |
| `bootstrap_all` | Full chain | chain of above | **Project build** | Orchestrates stages 1→6 |
| `incremental_sync` | Live delta chain | chain without auto-promote | **Scheduled live** | Structured+semi→preprocess→materialize |

---

## 3. Step-by-step: first-time bootstrap (project build)

### Step A — Dry-run the full chain (safe)

**Goal:** Prove pipelines run without writing graph; no Neo4j required for most stages.

**CLI:**

```bash
source venv/bin/activate
python - <<'PY'
from graph.enterprise_pipeline.control_plane import run_pipeline
r = run_pipeline("bootstrap_all", mode="bootstrap", dry_run=True)
print(r.status.value)
for s in r.stages:
    print(f"  {s.status.value:10} {s.name}: {s.message}")
if r.errors:
    print("errors", r.errors)
PY
```

**UI:** Admin → Knowledge Pipeline Control Room → Mode **bootstrap** → check **Dry-run** → **Run bootstrap_all**.

**Expect:** status `success` (or `partial`); smoke stage says dry-run skipped.

### Step B — Real extract + preprocess + materialize

```bash
python - <<'PY'
from graph.enterprise_pipeline.control_plane import run_pipeline
for pid in [
    "structured_extract",
    "semi_structured_ingest",
    "unstructured_extract",
    "preprocess_normalize",
    "knowledge_materialize",
]:
    r = run_pipeline(pid, mode="bootstrap", dry_run=False)
    print(pid, r.status.value, r.errors)
PY
```

**Or:** UI dry-run **off** → run each card, or `bootstrap_all` with dry-run off (includes smoke — needs Neo4j).

**Artifacts appear in:**

- `data/pipeline_staging/*-semi.json`
- `data/pipeline_staging/*-unstructured.json`
- `data/pipeline_staging/*-preprocessed.json`
- `data/enterprise_knowledge_catalog.json` (materialize)

### Step C — Smoke validation (Neo4j required)

```bash
# Ensure graph has data first if empty:
python graph/populate_graph.py

python - <<'PY'
from graph.enterprise_pipeline.control_plane import run_pipeline
r = run_pipeline("smoke_validate", mode="on_demand", dry_run=False)
print(r.status.value, r.stages[0].metrics if r.stages else r.errors)
PY
```

**UI:** Run `smoke_validate` with dry-run **off**.
**Legacy UI:** Validate button still works (`/admin/pipeline/validate`).

### Step D — Human review gate

1. UI: **Refresh Review** / check source counts
2. **Approve Changes (Gate)**
3. Or policy: only then allow promote

### Step E — Promote to staging Neo4j first, then production

```bash
python - <<'PY'
from graph.enterprise_pipeline.control_plane import run_pipeline
# 1) MERGE into staging (:7688)
r = run_pipeline("promote_graph", mode="on_demand", dry_run=False, target_env="staging")
print("staging", r.status.value, r.stages[-1].metrics if r.stages else r.errors)
# 2) After smoke on staging, promote production (:7687) used by /diagnose
r2 = run_pipeline("promote_graph", mode="on_demand", dry_run=False, target_env="production")
print("production", r2.status.value, r2.stages[-1].metrics if r2.stages else r2.errors)
PY
```

**UI:** Target **staging** → Promote → smoke → Target **production** → Promote.
**Legacy:** PROMOTE loads production Neo4j after smoke + approve.

**Diagnose always reads production Neo4j** (`NEO4J_URI`). Staging is for safe load/test before prod promote.

### Step E2 — Diagnose read-path cache (fast repeat traffic)

- Enabled by default (`enable_diagnose_cache=true`, TTL ~90s)
- Key = hash(tenant + product + asset + normalized message + catalog version)
- Hits skip re-running GraphRAG; response diagnosis may include `"_cache_hit": true`
- Cleared when pipelines call `invalidate_all_named_caches()` after promote

### Step F — Verify diagnosis uses graph

```bash
curl -s -X POST http://localhost:8080/diagnose \
  -H 'Content-Type: application/json' \
  -d '{"message":"washing machine will not drain E21","product_id":"wm-001"}' | python -m json.tool | head -40
```

---

## 4. Step-by-step: live incremental

### Step 1 — Drop deltas

Place new files under:

```text
data/pipeline_sources/semi_structured/incremental/
data/pipeline_sources/unstructured/incremental/   # optional
```

Structured deltas continue via connectors / `enterprise_sources` or mock API.

### Step 2 — Run incremental chain

```bash
python - <<'PY'
from graph.enterprise_pipeline.control_plane import run_pipeline
r = run_pipeline("incremental_sync", mode="incremental", dry_run=False)
print(r.status.value)
for s in r.stages:
    print(s.name, s.status.value, s.metrics)
PY
```

**UI:** Mode **incremental** → **Run incremental_sync**.

### Step 3 — Gate + promote

Same as bootstrap Steps C–E (`smoke_validate` → approve → `promote_graph`).

**Why no auto-promote?** Live systems should not MERGE bad deltas without quality + human/policy gate.

---

## 5. Step-by-step: on-demand single pipeline

Example: only re-run unstructured after adding a manual.

```bash
# add file under unstructured/bootstrap or incremental
python -c "from graph.enterprise_pipeline.control_plane import run_pipeline as R; \
 print(R('unstructured_extract', mode='on_demand', dry_run=False).status.value); \
 print(R('preprocess_normalize', mode='on_demand', dry_run=False).status.value); \
 print(R('knowledge_materialize', mode='on_demand', dry_run=False).status.value)"
```

**UI:** Click **Run** on the pipeline card with mode **on_demand**.

---

## 6. Using the Admin Control Room (UI/UX map)

| UI element | Action |
|------------|--------|
| Mode dropdown | bootstrap / incremental / on_demand |
| Target | staging vs production (promote) |
| Dry-run checkbox | Preview; skips durable writes where supported; skips live smoke |
| Pipeline cards | Run one pipeline |
| bootstrap_all button | Full first-time chain |
| incremental_sync button | Live delta chain |
| Promote graph button | MERGE Neo4j |
| Last run panel | Stage-by-stage status |
| Run history | Recent `run_id`s |
| Artifacts list | Fixture paths + staging JSON |

**Recommended operator flow (first week):**

1. Dry-run bootstrap_all
2. Real bootstrap stages (or bootstrap_all with Neo4j up)
3. Smoke
4. Approve
5. Promote
6. Diagnose smoke test in Chat

---

## 7. REST examples

```bash
# List pipelines
curl -s http://localhost:8080/admin/kg-pipelines | python -m json.tool

# Dry-run semi-structured
curl -s -X POST \
  'http://localhost:8080/admin/kg-pipelines/semi_structured_ingest/run?mode=bootstrap&dry_run=true' \
  | python -m json.tool

# Bootstrap full chain (real writes; smoke needs Neo4j)
curl -s -X POST \
  'http://localhost:8080/admin/kg-pipelines/bootstrap_all/run?mode=bootstrap&dry_run=false' \
  | python -m json.tool

# History
curl -s 'http://localhost:8080/admin/kg-pipelines/runs?limit=10' | python -m json.tool

# Artifacts
curl -s http://localhost:8080/admin/kg-pipelines/artifacts | python -m json.tool
```

---

## 8. Where things live on disk

```text
data/
  pipeline_sources/
    structured/README.md          # points to enterprise_sources / mock API
    semi_structured/
      bootstrap/                  # full file packs
      incremental/                # deltas
    unstructured/
      bootstrap/
      incremental/
  pipeline_staging/               # run outputs (generated)
  lineage/
    pipeline_runs/                # run JSON + index.jsonl
    etl_batches.jsonl             # legacy ETL lineage
  enterprise_knowledge_catalog.json
  enterprise_sources/             # structured fixtures for connectors
```

**Code:**

```text
graph/enterprise_pipeline/
  control_plane/     # registry, runner, run_store, models
  extractors/        # semi + unstructured
  preprocess/        # normalize + quality
  connectors/        # structured
  pipelines/         # classic ETL, smoke, promote
  orchestrator.py    # legacy CLI spine
```

---

## 9. Testing

```bash
source venv/bin/activate
pytest tests/test_kg_ingestion_pipelines.py -q
```

Covers: registry, fixtures load, extract patterns, preprocess rejects, dry runs, API list/run.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `bootstrap_all` fails on smoke | Neo4j down or empty graph | Start Neo4j; `populate_graph.py`; re-run smoke |
| Semi pipeline 0 records | Wrong folder for mode | bootstrap uses `.../bootstrap/`; incremental uses `.../incremental/` |
| Preprocess rejects all | Missing product_id / failure_mode_id | Fix source rows; quality_score &lt; 0.5 drops |
| Admin Control Room empty | API not running | Start uvicorn; check CORS / NEXT_PUBLIC_API_URL |
| 401 on admin routes | Admin token set | Pass `X-Admin-Token` or clear `ADMIN_API_TOKEN` for local demo |
| Promote no catalog | Materialize never ran | Run `knowledge_materialize` dry_run=false |

---

## 11. Mapping to enterprise tools (when you leave the demo)

| This app stage | Production analogue |
|----------------|---------------------|
| `run_pipeline` | Airflow/Dagster/Prefect task |
| `bootstrap_all` | Full-load DAG |
| `incremental_sync` | Nightly/hourly DAG + CDC |
| Control Room UI | Internal data ops portal / Backstage |
| `pipeline_runs` | OpenLineage / run metadata DB |
| dry_run | Airflow test / data preview env |
| promote_graph | Deploy graph to prod Neo4j cluster |

Keep **stage names and contracts**; swap the orchestrator.

---

## 12. Definition of done (operator)

You can claim the system works when:

1. Dry-run `bootstrap_all` succeeds without Neo4j
2. Real semi + unstructured + preprocess produce staging JSON
3. Materialize updates catalog
4. Smoke passes with Neo4j
5. Promote makes diagnosis return graph-backed failure modes
6. UI Control Room lists pipelines, runs a job, shows history

---

*For industry context and tool choices, see doc 20. For open production gaps, see `todo-kg-ingestion-pipelines.md`.*
