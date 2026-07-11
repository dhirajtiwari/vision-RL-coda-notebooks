# WarrantyGraph — Enterprise AI Diagnostics Platform

> **Graph-native appliance warranty diagnosis** powered by **Neo4j GraphRAG**, **LangGraph**, **FastAPI**, and a **Next.js** enterprise UI.
> Core diagnosis is **deterministic** (knowledge graph + FMEA/Bayes) — no LLM required.
> Optional LLM path is **ready-but-inactive** (`LLM_ENABLED=false`).

**Branch note:** Current platform maturity (dual Neo4j, multi-source packs, LLMOps, agent SDD kit) lives on `feature/llmops-for-remote-diagnostics`. Default `main` may lag until merged.

---

## What it does

1. **Binds identity** when CRM assets are available (customer + asset → product)
2. **Matches symptoms / error codes** against the knowledge graph (hybrid lexical + TF-IDF)
3. **Ranks failure modes** with FMEA-weighted Bayesian posteriors and dominance boost
4. **Returns explainable procedures** — CONFIRMS-targeted diagnostic steps, parts, provenance
5. **Highlights the reasoning path** in the Knowledge Explorer
6. **Escalates** when confidence is low or symptoms are critical
7. **Onboards knowledge safely** — multi-source packs → shared TBox / pipeline ABox → selection-scoped materialize → smoke → approve → promote **staging then production**

---

## Stack (current)

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js · React · React Flow · Tailwind · React Query (`frontend/`) |
| **API** | FastAPI · Uvicorn (`:8080`) |
| **Agent workflow** | LangGraph (diagnose orchestration) |
| **Knowledge graphs** | Neo4j **production** `:7687` (chat/explore) + **staging** `:7688` (promote-first) |
| **Cache / rate (optional)** | Redis `:6379` — memory backend if `REDIS_URL` empty |
| **Scoring** | FMEA + Bayesian posteriors + dominance / recommendation strength |
| **Ingest** | Control-plane pipelines: structured · semi · unstructured → OntologyBuilder ABox |
| **Runtime platform** | Parallel extract, TTL caches, rate limit, admission control (`runtime/`, `guardrails/`) |
| **LLMOps** | Guardrails, evals, observability active; gateway / PromptOps / FinOps ready-inactive |
| **UI personas** | Customer · Agent · Analyst · Admin (Next.js) |

---

## Architecture

```text
  CRM · PIM · FSM · Claims · multi-source packs (fixtures / mock SoR)
                │
                ▼
     Control plane (Admin wizard + registry pipelines)
     parallel extract → serial OntologyBuilder (ABox under shared TBox)
                │
                ▼
     Shape validate → materialize (selection-scoped)
                │
       ┌────────┴────────┐
       ▼                 ▼
  Neo4j STAGING     Neo4j PRODUCTION
   :7688               :7687  ◄── diagnose / explore READ path only
       │                 │
       └── promote ──────┘
                         │
              FMEA / Bayes + GraphRAG
                         │
              FastAPI :8080  +  Next.js :3000
              (guardrails · rate · caches · lineage)
```

**Ontology rule:** shared **TBox** (types once) + pipeline-built **ABox** (instances per pack).
No per-product OWL/schema generation — see [`docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`](docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md).

**Diagnosis path:** detect product/asset → retrieve evidence → score FMs → CONFIRMS steps → format → escalate?

---

## Documentation map

| Document | Audience | Content |
|----------|----------|---------|
| [`AGENTS.md`](AGENTS.md) + [`docs/sdd/`](docs/sdd/README.md) | **Claude Code / Codex** | Thin always-on SDD kit (`NEVER`/`MUST`/`OVERRIDES`/`PHASES`/`AS_BUILT` + modules `01`–`09`) |
| [`docs/23-…SDD….md`](docs/23-Spec-Driven-Development-Platform-and-Domain.md) | Humans / architects | Full portable SDD: platform vs domain, as-built, gaps |
| [`docs/sdd/09-PLATFORM-LLMOPS.md`](docs/sdd/09-PLATFORM-LLMOPS.md) | Agents (pull-on-demand) | LLMOps disciplines map (do **not** dump entire handbook) |
| [`docs/llmops-handbook/`](docs/llmops-handbook/00-index.md) | Humans | Handbook 00–21 + implementation playbook (recipes) |
| [`docs/22-TBox-ABox-….md`](docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md) | Engineers | Multi-source onboard, TBox vs ABox |
| [`docs/20`](docs/20-Enterprise-KG-Ingestion-Pipeline-Architecture.md) / [`21`](docs/21-KG-Ingestion-Step-by-Step-Runbook.md) | Operators | KG control plane architecture + runbook |
| [`docs/PIPELINE-AND-MODULE-GUIDE.md`](docs/PIPELINE-AND-MODULE-GUIDE.md) | Engineers | Module-by-module phases |
| [`todo.md`](todo.md) | Rebuild inventory | Full capability checklist for forking to a new vertical |

---

## Quick start

### Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.12+ | `python -m venv venv && source venv/bin/activate` |
| Node.js 18+ | Next.js frontend |
| Docker | Dual Neo4j (+ optional Redis) via compose |
| Ports | UI `3000`, API `8080`, Neo4j prod `7474/7687`, staging `7475/7688`, Redis `6379`, mock SoR `8090` |

### 1. Infra (dual graph + Redis)

```bash
docker compose -f docker/docker-compose.infra.yaml up -d
# Optional Redis: docker compose -f docker/docker-compose.redis.yaml up -d
```

### 2. App (API + UI)

```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # dual Neo4j defaults already match compose

# Recommended
./restart-all.sh

# Or manual:
# uvicorn api.main:app --host 0.0.0.0 --port 8080
# cd frontend && npm install && npm run dev
```

### 3. Load knowledge (baseline catalog)

```bash
python graph/populate_graph.py    # MERGE catalog into production Neo4j
```

For **selection-scoped multi-source onboard** (NEW packs such as dehumidifier / espresso), use the **Admin** wizard (Fetch → Select → Validate → Materialize → Smoke → Approve → Promote staging → Promote production). Details: docs 21–22 and `docs/sdd/02-PLATFORM-INGEST.md`.

### Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| Next.js UI | http://localhost:3000 | Chat · Explorer · Cases · Ops · Admin |
| API docs | http://localhost:8080/docs | OpenAPI |
| Health + runtime | http://localhost:8080/health | Graphs + caches/workers/rate backend |
| Metrics | http://localhost:8080/metrics | Prometheus (when enabled) |
| Neo4j prod browser | http://localhost:7474 | `neo4j` / `password` (demo only) |
| Neo4j staging browser | http://localhost:7475 | Promote-first target |
| Mock enterprise SoR | http://localhost:8090 | Optional simulation |

---

## UI (Next.js)

| Surface | Role |
|---------|------|
| **Diagnosis Chat** | Free-text symptoms; strength badge; posterior / graph / text tiles; provenance; jump to path |
| **Knowledge Explorer** | Full product subgraph + diagnosis path highlight (React Flow) |
| **Agent Cases** | Escalations, claims, status |
| **Enterprise Ops** | Lineage batches, connector health |
| **Admin** | Multi-source control plane: dry-run/fetch, selection, entity delta, validate, materialize, smoke, approve, dual promote, session reset for next cycle |

---

## Knowledge model

```text
Asset → Product / Model / SKU
  → Symptom + ErrorCode
  → FailureMode          (Bayesian P(fm|evidence))
  → DiagnosticStep       (prefer CONFIRMS(top FM))
  → Component / Part
  → Claim / HistoricalResolution / WarrantyPolicy
```

### Catalog footprint (demo)

- **Core OEM + demo appliances:** washer / dishwasher / microwave / fridge / dryer / range families (static OEM catalog + enterprise fixtures)
- **Multi-source NEW packs (pipeline demos):** e.g. `hmd-001` (dehumidifier), `esp-001` (espresso) under `data/pipeline_sources/` with structured / semi / unstructured + CRM/claims merge patterns
- Catalog size grows after promote — do not hard-code “exactly 13” as the only truth after multi-source onboard

### Example queries

```text
"My washing machine won't spin and water stays in the drum"
"Dishwasher leaves dishes wet and cold after the cycle"
"Machine is not heating"          # espresso pack after promote (esp-001)
"Dehumidifier is running but humidity stays high"
```

### Demo CRM (fixtures)

| Customer | Asset | Product |
|----------|-------|---------|
| CUST-10042 Jane Martinez | AST-WM-4421 | wm-001 |
| CUST-10087 Robert Chen | AST-DW-1180 | dw-001 |
| CUST-10042 | AST-MW-7702 | mw-001 |
| CUST-10120 Maria Lopez | AST-HMD001-4100 / AST-ESP001-2200 | hmd-001 / esp-001 (after pack promote) |

---

## Confidence engine

`graph/reliability.py` — deterministic (no LLM):

| Function | Purpose |
|----------|---------|
| `composite_confidence()` | Posterior + graph edge strength + text match |
| `dominance_boost()` | Boost when top FM dominates competitors |
| `recommendation_strength()` | Strong / Moderate / Weak / Insufficient data |

Modest posteriors (e.g. ~60%) can still be correct when dominance and graph links are strong — use **recommendation strength** and matched evidence IDs, not text-match alone.

---

## Control plane & multi-source

**Operator sequence (Admin):**
Sources → Fetch (dry-run) → Select products → Validate ABox → Materialize → Smoke → Approve → Promote **staging** → Promote **production** → (optional) reset session for next cycle.

| Capability | Behavior |
|------------|----------|
| Selection scope | Materialize/promote only selected IDs; empty selection fail-closed when work exists |
| Dual graph | Chat never reads staging as production |
| Pack discipline | Shared TBox; CI gate `tests/test_multi_source_tbox_abox.py` |
| Runtime | Parallel connector extract (default 4 workers), serial transform; cache invalidate on promote |

Pipeline registry IDs (examples): `structured_extract`, `semi_structured_ingest`, `unstructured_extract`, `knowledge_materialize`, `smoke_validate`, `promote_graph`, `bootstrap_all`, `incremental_sync`.

---

## Enterprise LLMOps

Core diagnosis is **graph-native**. LLM disciplines follow ADR 0001 and the handbook, adapted for this layout:

| Discipline | Location | Status |
|------------|----------|--------|
| Guardrails | `guardrails/` | **Active** (input/output/action + rate limit) |
| Observability | `observability/` | **Active** (JSON logs, Prometheus; OTEL opt-in) |
| EvalOps | `evals/` | **Active** CI smoke + nightly full |
| Security / governance | `security/`, `docs/governance/`, `docs/model-cards/` | **Active** docs + controls |
| Runbooks / monitoring | `docs/runbooks/`, `monitoring/` | **Active** configs |
| Gateway / PromptOps / FinOps | `gateway/`, `prompts/`, `finops/` | **Ready** — `LLM_ENABLED=false` |

Agent-facing map: [`docs/sdd/09-PLATFORM-LLMOPS.md`](docs/sdd/09-PLATFORM-LLMOPS.md).
Recipes: [`docs/llmops-handbook/`](docs/llmops-handbook/00-index.md).

---

## Project structure

```text
.
├── AGENTS.md                 # Agent entrypoint → docs/sdd/
├── frontend/                 # Next.js UI
├── api/                      # FastAPI: /diagnose, /health, /graph/*, /admin/*
├── agents/                   # LangGraph diagnosis workflow
├── services/                 # Diagnosis orchestration
├── graph/
│   ├── graph_rag.py          # GraphRAG + product resolution
│   ├── reliability.py        # FMEA / Bayes
│   ├── populate_graph.py
│   └── enterprise_pipeline/  # connectors, OntologyBuilder, control plane
├── runtime/                  # caches, parallel_map, admission
├── guardrails/ observability/ gateway/ promptops/ prompts/ models/ finops/
├── evals/                    # run_eval.py + golden + safety + thresholds
├── security/ monitoring/
├── integrations/ simulation/ # CRM/warranty/cases + mock SoR
├── config/settings.py        # 12-factor dual Neo4j, runtime, LLM flags
├── data/
│   ├── enterprise_sources/   # PIM/CRM/FSM/Claims fixtures
│   ├── pipeline_sources/     # multi-source packs (hmd/esp manifests…)
│   └── lineage/
├── docker/                   # dual Neo4j compose, service Dockerfiles
├── deploy/ k8s/ infra/       # progressive delivery scaffolds / placeholders
├── tests/                    # pytest (incl. multi-source TBox, guardrails, obs)
├── docs/
│   ├── sdd/                  # agent-native SDD kit
│   ├── llmops-handbook/
│   ├── 20–23*.md             # KG + SDD
│   └── …
├── .github/workflows/        # ci.yml (eval smoke), eval-nightly, cd
└── todo.md
```

---

## REST API (examples)

```bash
# Health (includes runtime block when available)
curl http://localhost:8080/health

# Diagnose
curl -X POST http://localhost:8080/diagnose \
  -H "Content-Type: application/json" \
  -d '{"message":"washer wont spin","customer_id":"CUST-10042","asset_id":"AST-WM-4421","product_id":"wm-001"}'

# Product graph (explorer)
curl http://localhost:8080/graph/product/wm-001

# Admin control plane (local demo often open; set ADMIN_API_TOKEN in real deploys)
# e.g. dry-run, plan, selection, promote, session/reset-for-next-cycle — see /docs
```

Typical diagnose fields: `recommendation_strength`, posteriors, `provenance_trail[]`, evidence, steps, path ids for explorer highlight.

---

## Tests & quality gates

```bash
source venv/bin/activate
pip install -r requirements-dev.txt

pytest tests/ -q
pytest tests/test_multi_source_tbox_abox.py -q
pytest tests/test_guardrails.py tests/test_observability.py -q

python evals/run_eval.py --suite smoke    # CI gate (safety floor 1.0)
```

| Gate | Where |
|------|--------|
| Unit / integration pytest | pre-push + CI |
| Multi-source / TBox discipline | `tests/test_multi_source_tbox_abox.py` |
| Eval smoke | CI `evals/run_eval.py --suite smoke` |
| Eval full | `eval-nightly.yml` (graph available) |
| Frontend build | CI |
| Ruff / ESLint / tsc | pre-commit |

Many tests degrade gracefully without Neo4j; full graph/eval suites need Docker graphs.

> **Note:** some pipeline tests may rewrite local catalog fixtures mid-run — restore dirty seed files before commit (`git restore data/…`). Documented in SDD as a hermetic-CI pitfall.

---

## Developer setup (hooks)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
pre-commit install -t pre-push
cd frontend && npm install && cd ..
```

| Stage | Tools |
|-------|--------|
| pre-commit | ruff, ruff-format, ESLint, tsc, file hygiene |
| pre-push | full pytest |

```bash
ruff check . --fix && ruff format .
pytest tests/ -q
cd frontend && npm run lint:fix && npm run typecheck && npm run build
pre-commit run --all-files
```

---

## Configuration

```bash
cp .env.example .env
```

| Variable | Default (demo) | Description |
|----------|----------------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Production graph (chat/explore) |
| `NEO4J_STAGING_URI` | `bolt://localhost:7688` | Staging promote target |
| `REDIS_URL` | empty | Shared rate/cache; memory if unset |
| `DEMO_MODE` / `ALLOW_FIXTURE_FALLBACK` | true | Local fixtures |
| `USE_MOCK_ENTERPRISE_APIS` | true | Mock SoR |
| `ENABLE_PROVENANCE` | true | Provenance on diagnoses |
| `ESCALATION_CONFIDENCE_THRESHOLD` | 0.65 | Escalate below |
| `RATE_LIMIT_PER_MINUTE` | 60 | API rate limit |
| `ENABLE_PII_REDACTION` | true | Logs / responses |
| `OTEL_ENABLED` | false | Opt-in tracing |
| `ENABLE_PROMETHEUS_METRICS` | true | `/metrics` |
| `LLM_ENABLED` | **false** | Optional rewriter path |
| `LLM_COST_BUDGET_USD_PER_DAY` | 5.00 | FinOps breaker when LLM on |
| `ADMIN_API_TOKEN` | empty (open) | Protect `/admin/*` outside local demo |

See [`.env.example`](.env.example) for the full flag list.

---

## Risk mitigation

| Risk | Mitigation |
|------|------------|
| Unsafe repair advice | Graph-grounded steps + critical-symptom escalation |
| Low-confidence misdiagnosis | Threshold escalation + recommendation strength |
| Unexplainable output | Provenance + evidence; no black-box core path |
| Bad / partial ETL | Shape validate before promote; smoke + approve |
| Whole-fleet accidental promote | Selection-scoped materialize/promote; fail-closed |
| Staging vs prod confusion | Dual graph; chat reads production only |
| Injection / abuse | Input guardrails + rate limit + safety evals |
| LLM cost (if enabled) | Daily budget circuit breaker + inactive by default |

---

## Assumptions & honesty

This is a **design / demo platform on synthetic fixtures**, not a certified multi-tenant SaaS.

- Graph-native core; LLM optional and off by default
- Enterprise connectors: **mock/fixtures** unless live URLs configured
- Dual **single-node** Neo4j in Docker — not HA multi-region
- Progressive delivery / Terraform under `deploy/` / `infra/` are **scaffolds**
- P0 gaps (OIDC, hard tenant ACL) deferred for demo — see `docs/sdd/08-GAPS.md` and SDD §6

---

## Diagrams

```bash
bash docs/graphviz/render_all.sh
```

C4 and multi-volume PDFs live under `docs/c4/`, `docs/multi-volume/`, and `docs/full-project/`.

---

## Related entrypoints

| Goal | Start here |
|------|------------|
| Run locally | This README → Quick start |
| Implement with AI agents | [`AGENTS.md`](AGENTS.md) → `docs/sdd/` |
| Rebuild for another vertical | [`todo.md`](todo.md) + `docs/sdd/OVERRIDES.md` |
| LLMOps recipes | `docs/llmops-handbook/` |
| Production gaps | `docs/sdd/08-GAPS.md` / docs/23 §6 |
