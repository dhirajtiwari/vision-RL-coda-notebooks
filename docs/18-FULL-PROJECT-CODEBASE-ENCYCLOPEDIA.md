# WarrantyGraph — Full Project & Codebase Encyclopedia

> **This document is intentionally broader than any single working session.**
> It inventories the **entire repository**: product intent, every first-party package, data, APIs, frontend, ETL, graph intelligence, LLMOps, security, deploy, tests, and docs map.

| Companion docs | Scope |
|----------------|--------|
| This file (`18`) | **Whole codebase / whole project** |
| `docs/15`–`17` | Ontology, runtime scale, landscape diagrams |
| `docs/interview/*` | Interview Q&A style prep |
| `README.md` | Quick start |
| `PIPELINE-AND-MODULE-GUIDE.md` | Blueprint → claim phases |

**Regenerate compact PDF:** `python docs/full-project/generate_full_project_pdf.py`
**Output:** `docs/full-project/WarrantyGraph-Full-Project-Codebase-Encyclopedia.pdf`

**Multi-volume deep library (theory + annotated code + RDF/OWL):**
`python docs/multi-volume/generate_all_volumes.py` → `docs/multi-volume/00`–`05-*.pdf`

---

## 1. Product identity

| Item | Value |
|------|--------|
| **Name** | WarrantyGraph / Enterprise AI Diagnostics Platform |
| **Repo role** | Graph-native appliance warranty diagnosis demo that behaves like production |
| **Core idea** | Customer text → Neo4j GraphRAG → FMEA + Bayesian ranking → parts, steps, provenance, optional claim/escalation |
| **LLM posture** | **Not required** for core diagnosis; optional gateway (default off) |
| **Primary UI** | Next.js 16 on `:3000` |
| **API** | FastAPI on `:8080` |
| **Graph** | Neo4j Bolt `:7687` |
| **Mock enterprise** | FastAPI on `:8090` |

### What a request does (runtime)

1. Match product (message / `product_id` / CRM `asset_id`)
2. Match symptoms + error codes (lexical / hybrid TF-IDF)
3. Rank failure modes (INDICATES + reliability engine)
4. Build diagnostic tree + predict parts
5. Format response + provenance + optional graph subgraph
6. Escalate if low confidence / ambiguity / critical severity
7. Optionally submit claim under warranty policy

### What a batch job does (knowledge)

1. Extract PIM / FSM / Claims / CRM (parallel)
2. OntologyBuilder → catalog JSON + provenance
3. Smoke validation scenarios
4. Promote → `populate_graph` MERGE into Neo4j
5. Invalidate read caches

---

## 2. Repository map (top-level)

```text
diagnostic-chatbot/
├── agents/                 # LangGraph workflow + tools
├── api/                    # FastAPI REST surface
├── config/                 # Pydantic settings
├── data/                   # Catalogs, fixtures, SQLite, lineage
├── deploy/                 # Progressive delivery (Argo/Flagger)
├── docker/                 # Dockerfiles + compose (obs, redis)
├── docs/                   # Architecture, C4, graphviz, LLMOps handbook, full encyclopedia
├── domain/                 # Typed business models
├── evals/                  # Golden + safety eval gate
├── finops/                 # LLM cost budget / circuit breaker
├── frontend/               # Next.js 16 UI
├── gateway/                # Optional LLM model gateway
├── graph/                  # Neo4j, GraphRAG, ETL, OEM catalog, reliability
├── guardrails/             # Input/output/action/rate limit
├── infra/terraform/        # IaC modules
├── integrations/           # CRM, warranty, claims, cases
├── k8s/                    # Base + staging/prod overlays
├── models/                 # Model registry YAML
├── monitoring/             # Prometheus, Grafana, OTEL, alerts
├── observability/          # Logging, metrics, tracing, redaction
├── promptops/ + prompts/   # Versioned prompt artifacts
├── runtime/                # Cache, Redis, concurrency, partitions
├── security/               # Threat model, OWASP LLM mapping
├── services/               # Shared diagnosis orchestration
├── simulation/             # Mock enterprise apps API
├── tests/                  # Pytest suite
├── ui-streamlit-archive/   # Legacy Streamlit UI
├── utils/                  # Persistence, lineage, display, stores
├── Makefile, restart-all.sh, run_demo.sh, run_enterprise_demo.sh
├── requirements*.txt, pyproject.toml
└── .github/workflows/      # CI, CD, nightly eval
```

---

## 3. Runtime architecture (layers)

| Layer | Packages | Responsibility |
|-------|----------|----------------|
| **Experience** | `frontend/`, `ui-streamlit-archive/` | Chat, graph explorer, claims, ops, admin |
| **API** | `api/` | HTTP contracts, middleware, admin pipelines |
| **Orchestration** | `services/`, `agents/`, `integrations/` | Warranty gate, LangGraph, claims/cases |
| **Intelligence** | `graph/*.py` (non-ETL) | GraphRAG, FMEA/Bayes, trees, parts, viz |
| **Knowledge platform** | `graph/enterprise_pipeline/`, `populate_graph`, OEM catalog | ETL → Neo4j |
| **Platform cross-cut** | `runtime/`, `guardrails/`, `observability/`, `finops/`, `gateway/` | Scale, safety, cost, LLM, telemetry |
| **Config & domain** | `config/`, `domain/` | Settings + typed outcomes |
| **Ops data** | `utils/persistence`, escalation/lineage stores | SQLite + JSONL audit |
| **Deploy** | `docker/`, `k8s/`, `deploy/`, `infra/`, `monitoring/` | Run & observe in prod shape |

---

## 4. Package encyclopedia (every first-party area)

### 4.1 `api/` — REST surface

| File | Role |
|------|------|
| `main.py` | FastAPI app: diagnose, claims, graph, lineage, admin pipelines, health/metrics |
| `schemas.py` | `DiagnoseRequest/Response`, `ClaimStatus`, `GraphSubgraphResponse` |

**Routes (complete):**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness + neo4j + runtime (cache/redis) |
| GET | `/metrics` | Prometheus scrape |
| GET | `/products` | List products |
| POST | `/diagnose` | Full diagnosis |
| GET | `/graph/ontology` | Schema meta-graph |
| GET | `/graph/product/{id}` | Product neighborhood |
| GET | `/graph/diagnosis-subgraph` | Path-focused subgraph |
| GET/POST/PATCH | `/claims`, `/claims/submit`, `/claims/{id}/status` | Claim lifecycle |
| GET | `/lineage/batches` | ETL batch audit |
| GET | `/integrations/status` | Connector health |
| POST | `/admin/pipeline/*` | dry-run, validate, review, promote, onboard |
| GET | `/admin/pipeline/status` | Pipeline status |

**Middleware:** request id, rate limit on `/diagnose`, OTEL instrument, CORS for UI.

### 4.2 `services/` — single business path

| File | Role |
|------|------|
| `diagnosis_service.py` | `run_full_diagnosis`: warranty short-circuit → `run_diagnosis` → case handoff |

Prevents API vs UI rule drift.

### 4.3 `agents/` — LangGraph

| File | Role |
|------|------|
| `diagnosis_graph.py` | Nodes: detect_product → run_diagnosis → format → escalate |
| `tools.py` | Thin wrappers: diagnose, detect, list products, steps, rank |

Works **without** external LLM (graph-native).

### 4.4 `graph/` — knowledge + intelligence

| File | Role |
|------|------|
| `neo4j_client.py` | Shared Bolt driver + pool settings |
| `populate_graph.py` | Constraints + MERGE catalog into Neo4j |
| `graph_rag.py` | Core `diagnose()`, product resolve, match, rank, format |
| `reliability.py` | FMEA S/O/D, RPN, Action Priority, Bayes posteriors, dominance, recommendation strength |
| `diagnostic_engine.py` | NEXT_STEP / CONFIRMS / RULES_OUT trees |
| `parts_predictor.py` | REQUIRES_PART + BOM + SKU + claim scores |
| `symptom_retrieval.py` | Hybrid lexical + TF-IDF |
| `graph_visualization.py` | Ontology/product/diagnosis payloads + HTML/Mermaid helpers |
| `knowledge_lineage.py` | Per-product knowledge profile from graph |
| `provenance.py` | PROV-O-aligned provenance helpers |
| `oem_product_catalog.py` | 10 OEM product builders |
| `warranty_catalog_extensions.py` | Model/SKU/Component/Asset/Claim extensions |
| `synthetic_data_generator.py` | Legacy synthetic products + catalog build |
| `rdf_ontology_export.py` | Turtle / RDF-XML export |

**Enterprise ETL subtree `graph/enterprise_pipeline/`:**

| Path | Role |
|------|------|
| `orchestrator.py` | ETL → smoke → promote |
| `connectors/{pim,crm,claims,fsm}_connector.py` | Source adapters (HTTP or fixture) |
| `connectors/base.py` | `ConnectorResult`, ABC |
| `transformers/ontology_builder.py` | Merge sources → catalog |
| `transformers/pim_blueprint_sync.py` | Blueprints → `pim_catalog.json` |
| `pipelines/knowledge_etl.py` | Pipeline 1 |
| `pipelines/smoke_validation.py` | Pipeline 2 |
| `pipelines/staging_promotion.py` | Pipeline 3 |
| `http_client.py` | GET/POST JSON helper |

### 4.5 `integrations/`

| File | Role |
|------|------|
| `crm_enrichment.py` | Bind customer/asset → product/SKU/warranty |
| `warranty_eligibility.py` | Eligible? parts cost vs policy |
| `claims_workflow.py` | Submit/list/update claims; optional Neo4j Claim nodes |
| `case_management.py` | Escalation → simulated CCaaS case |

### 4.6 `simulation/`

| File | Role |
|------|------|
| `mock_enterprise_apps.py` | Mock PIM/CRM/FSM/Claims/Cases API on `:8090` |

### 4.7 `domain/`

| File | Role |
|------|------|
| `models.py` | `WarrantyDecision`, `DiagnosisOutcome` (Pydantic) |

### 4.8 `config/`

| File | Role |
|------|------|
| `settings.py` | Neo4j, paths, demo flags, Redis, cache TTLs, rate limits, LLM keys, OTEL, budgets, tenants, pools |

### 4.9 `runtime/` (scale primitives)

| File | Role |
|------|------|
| `cache.py` | TtlCache / RedisTtlCache, named caches |
| `redis_client.py` | Optional Redis connect/health |
| `concurrency.py` | `parallel_map` for I/O |
| `concurrency_limit.py` | Diagnose admission control |
| `partitioning.py` | Tenant/product/batch keys, batching |

### 4.10 `guardrails/`

| File | Role |
|------|------|
| `input.py` | Injection/jailbreak/sanitize |
| `output.py` | Length cap, PII redaction |
| `pipeline.py` | `guard_request` composition |
| `action.py` | Side-effect allowlist / HITL |
| `rate_limit.py` | Sliding window (memory or Redis) |

### 4.11 `observability/`

| File | Role |
|------|------|
| `logging_setup.py` | JSON logs, request_id |
| `metrics.py` | Prometheus counters/histograms |
| `tracing.py` | OTEL setup + FastAPI instrument |
| `redaction.py` | PII redaction for logs/telemetry |

### 4.12 `gateway/` + `models/` + `promptops/` + `prompts/` + `finops/`

| Area | Role |
|------|------|
| `gateway/router.py` | Alias → provider → retry/fallback → meter + budget |
| `gateway/providers.py` | OpenAI / Azure Foundry adapters |
| `gateway/registry.py` | Load `models/registry.yaml` |
| `models/registry.yaml` | Pinned model aliases |
| `promptops/` | Load versioned `prompts/<id>/vN.yaml` |
| `prompts/diagnosis-rewriter/` | Optional rewrite prompt artifact |
| `finops/budget.py` | Daily USD ceiling circuit breaker |

### 4.13 `utils/`

| File | Role |
|------|------|
| `persistence.py` | SQLite: escalations, cases, claims |
| `escalation_store.py` | Agent escalation queue API |
| `lineage_store.py` | ETL batch JSONL |
| `diagnosis_display.py` | Executive formatting, mermaid journeys |
| `connector_status.py` | Integration health payload |
| `logger.py` | Logger helper |

### 4.14 `frontend/` (Next.js)

| Path | Role |
|------|------|
| `app/page.tsx` | Main UI: chat, explorer, claims, ops |
| `app/layout.tsx`, `providers.tsx` | App shell, React Query |
| `lib/api.ts` | Typed-ish client for all API routes |
| `lib/types.ts` | Frontend types |
| `app/globals.css` | Theme tokens (dark/light) |

**UI capabilities (from product README):** diagnosis chat, confidence tiles, Knowledge Explorer (React Flow + path highlight), agent cases, enterprise ops lineage, admin pipeline actions.

### 4.15 `evals/`

| Path | Role |
|------|------|
| `run_eval.py` | Gate script (exit non-zero on fail) |
| `golden/smoke.jsonl` | Functional golden cases |
| `safety/injection.jsonl` | Adversarial prompts |
| `thresholds.yaml` | Pass bars |

### 4.16 `tests/`

| File | Focus |
|------|--------|
| `test_api.py` | Health, admin auth, diagnose status codes |
| `test_diagnosis.py` | Engine evaluation harness |
| `test_reliability.py` | Pure FMEA/Bayes math |
| `test_symptom_retrieval.py` | Hybrid matching |
| `test_product_resolution.py` | Product conflict / message preference |
| `test_services.py` | Warranty gate |
| `test_guardrails.py` | Input/output/rate/action |
| `test_observability.py` | Redaction, metrics, registry, budget |
| `test_oem_catalog.py` | OEM builders |
| `test_warranty_ontology.py` | BOM/SKU/assets |
| `test_pipeline_integration.py` | ETL fixture mode |
| `test_enterprise_scenarios.py` | Scenario JSON suite |
| `test_graph_visualization.py` | Viz payloads |
| `test_persistence.py` | SQLite store |
| `test_runtime.py` / `test_redis_runtime.py` | Cache/concurrency/Redis |
| `test_rdf_ontology_export.py` | RDF export |
| `test_e2e_diagnosis_flow.py` | API e2e + optional Neo4j |

### 4.17 Data plane `data/`

| Artifact | Purpose |
|----------|---------|
| `synthetic_diagnosis_data.json` | Runtime catalog (often ETL output) |
| `enterprise_knowledge_catalog.json` | Full enterprise catalog |
| `enterprise_sources/*.json` | PIM/CRM/FSM/claims fixtures |
| `provenance_manifest.json` | Default provenance by entity type |
| `lineage/etl_batches.jsonl` | Batch audit |
| `diagnostics.db` | SQLite ops store |
| `escalations.json` / `simulated_cases.json` | Legacy/parallel stores |

### 4.18 Deploy, infra, security, monitoring

| Area | Contents |
|------|----------|
| `docker/` | Dockerfiles: api, etl, frontend, mock, ui; compose: observability, redis |
| `k8s/base` | API, UI, mock, Neo4j, ETL CronJob, ingress, PVC, config |
| `k8s/overlays` | staging / prod |
| `deploy/rollouts` | Argo Rollouts, Flagger canary |
| `infra/terraform` | Cloud modules stubs/README |
| `monitoring/` | alerts, Grafana dashboard, OTEL collector, SLO rules |
| `security/` | threat-model, OWASP LLM mapping |
| `docs/governance/` | classification, retention, DPIA |
| `.github/workflows` | ci.yml, cd.yml, eval-nightly.yml |

### 4.19 Documentation corpus

| Series | Content |
|--------|---------|
| `docs/01`–`14` docx | Architecture, GraphRAG, Cypher, roadmaps, demos |
| `docs/15`–`18` md | Ontology, runtime, landscape, **this encyclopedia** |
| `docs/c4/` | Structurizr DSL + C4 graphviz |
| `docs/graphviz/` | 01–41 architecture/pipeline diagrams |
| `docs/llmops-handbook/` | Chapters 00–21 + PDFs + playbook |
| `docs/interview/` | Interview mastery guide + PDF |
| `docs/full-project/` | Full encyclopedia PDF generator + PDF |
| `docs/model-cards/` | System card |
| `docs/runbooks/` | Incident runbooks (cost, latency, PII, injection, outage, quality, RAG stale) |

---

## 5. Configuration surface (`config/settings.py`)

Major groups (env / `.env` via pydantic-settings):

- **Neo4j:** uri, user, password, database, pool size, acquisition timeout
- **Paths:** data_file, enterprise catalog, provenance manifest, lineage dir, sources dir
- **Demo mode:** `demo_mode`, fixture fallback, mock enterprise URL
- **Connector URLs:** CRM/PIM/Claims/FSM overrides
- **API:** host/port, admin token
- **Diagnosis:** escalation threshold, symptom min score, ambiguity margin
- **Runtime:** cache TTLs, ETL workers, product batch size, tenant id
- **Redis:** url, key prefix, timeouts
- **Concurrency:** max concurrent diagnoses, lease seconds
- **Guardrails:** rate limit, PII, max input/output lengths
- **Observability:** log level/json, OTEL flags, Prometheus
- **LLM:** enabled flag, keys, model alias, Azure fields
- **FinOps:** daily budget USD

**Safety:** refuses default Neo4j password when `demo_mode=false`.

---

## 6. Ontology entities & relationships (runtime Neo4j)

**Nodes:** Product, Model, SKU, Asset, Symptom, ErrorCode, FailureMode, DiagnosticStep, Component, Part, Claim, HistoricalResolution, WarrantyPolicy

**Core relationships:** HAS_MODEL, HAS_SKU, INSTANCE_OF, BOUND_TO_SKU, HAS_SYMPTOM, HAS_ERROR_CODE, CAN_HAVE, INDICATES, HAS_DIAGNOSTIC_STEP, CONFIRMS, RULES_OUT, NEXT_STEP, IMPACTS_COMPONENT, REALIZED_BY, REQUIRES_PART, COMPATIBLE_WITH, CONFIRMED, USED_PART, FOR_PRODUCT, COVERED_BY

---

## 6b. Indexes & constraints (What / Where / When / How / Why)

> Full detail: [`docs/19-Indexes-Constraints-and-Lookup-Performance.md`](19-Indexes-Constraints-and-Lookup-Performance.md)

### Neo4j uniqueness constraints

| | |
|--|--|
| **What** | `CREATE CONSTRAINT … REQUIRE <id> IS UNIQUE` on every major label’s natural key (`product_id`, `symptom_id`, `failure_mode_id`, …). In Neo4j 5 this also creates a **unique index**. |
| **Where** | `graph/populate_graph.py` → `create_constraints(tx)` |
| **When** | At the **start** of every `populate_graph()` call (CLI load, ETL with Neo4j, staging promote). **Not** recreated on each diagnose. |
| **How** | `session.execute_write(create_constraints)` then `MERGE (n:Label {id: $id})`. Runtime Cypher does `MATCH (p:Product {product_id: $pid})` → index seek, then relationship expand. |
| **Why** | Idempotent ETL (no duplicate entities); O(1)-ish id lookup; data integrity. |

### SQLite ops indexes

| | |
|--|--|
| **What** | PRIMARY KEY on `case_id` / `claim_id`; `CREATE INDEX idx_*_status ON …(status)`. |
| **Where** | `utils/persistence.py` → `OperationalStore._init_schema()` → `data/diagnostics.db` |
| **When** | First time the ops store opens (first claim/escalation/case). |
| **How / Why** | Fast get-by-id and filter agent queues by status — **not** used by GraphRAG. |

### Not used today

Full-text / vector indexes on symptoms; separate Neo4j `CREATE INDEX` beyond uniqueness constraints. Symptom text matching is Python hybrid TF-IDF after product is known.

---

## 6c. How to read any subsystem (What / Where / When / How / Why)

Use this template for the whole codebase:

| Question | Meaning |
|----------|---------|
| **What** | Concept or artifact in plain English |
| **Where** | File / package / port |
| **When** | Batch vs online; first load vs every request |
| **How** | Mechanism (code path, Cypher, formula) |
| **Why** | Design reason / trade-off |

### Quick WWWH cards (core subsystems)

| Topic | What | Where | When | How | Why |
|-------|------|-------|------|-----|-----|
| **Diagnosis** | Rank FM + parts for a message | `api` → `diagnosis_service` → `graph_rag` | Each `POST /diagnose` | Match symptoms → Bayes/FMEA → tree/parts | Explainable, deterministic |
| **FMEA** | S/O/D risk ratings | `reliability.py` | During FM ranking | Graph counts → S,O,D → RPN/AP | Industry-defensible triage |
| **Bayes** | P(fm\|symptoms) | `reliability.bayesian_posteriors` | After strong symptoms matched | Prior × ∏ likelihoods, normalize | Differential diagnosis |
| **ETL** | Build catalog + graph | `enterprise_pipeline/` | Batch / admin / cron | Parallel extract → OntologyBuilder → MERGE | Knowledge freshness |
| **LangGraph** | Multi-step agent | `agents/diagnosis_graph.py` | Inside diagnosis | detect→diagnose→format→escalate | Explicit workflow |
| **Redis (opt)** | Shared multi-pod state | `runtime/`, rate_limit, budget | When `REDIS_URL` set | Shared cache/rate/admission | Multi-replica correctness |
| **RDF export** | Formal ontology file | `rdf_ontology_export.py` | Manual / docs build | Turtle or RDF-XML from catalog | Interchange, not runtime |

---

## 7. End-to-end sequences

### 7.1 Diagnosis (online)

```text
Browser → POST /diagnose
  middleware (rate limit, request_id)
  ConcurrencyLimiter
  guard_request
  enrich_session_from_crm
  check_warranty_eligibility  [? block]
  run_full_diagnosis
    run_diagnosis (LangGraph)
      detect_product / resolve_product_for_diagnosis
      tool_diagnose → graph_rag.diagnose
        match_symptoms / match_error_codes
        rank_failure_modes (+ reliability)
        diagnostic_engine tree
        parts_predictor
        format + provenance + subgraph
      format_response
      handle_escalation → escalation_store / case_management
  validate_output
  DiagnoseResponse
```

### 7.2 Knowledge (batch)

```text
orchestrator / admin APIs
  run_knowledge_etl
    parallel connector fetch
    OntologyBuilder catalog
    write JSON + lineage
    optional populate_graph + cache invalidate
  run_smoke_validation
  run_staging_promotion → populate_graph
```

---

## 8. Local runbook

```bash
# Python
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Neo4j (Docker) then:
python graph/populate_graph.py

# API
uvicorn api.main:app --port 8080

# UI
cd frontend && npm install && npm run dev

# Optional mock enterprise
python -m simulation.mock_enterprise_apps   # :8090

# Optional Redis multi-replica shared state
docker compose -f docker/docker-compose.redis.yaml up -d
export REDIS_URL=redis://localhost:6379/0

# Full ETL spine
python -m graph.enterprise_pipeline.orchestrator

# One-command
./restart-all.sh
```

| URL | Service |
|-----|---------|
| http://localhost:3000 | Next.js UI |
| http://localhost:8080/docs | OpenAPI |
| http://localhost:8080/health | Health |
| http://localhost:7474 | Neo4j Browser |

---

## 9. Testing & quality gates

| Gate | How |
|------|-----|
| Unit/integration | `pytest` (pre-push hook) |
| Lint/format | ruff via pre-commit |
| Eval gate | `evals/run_eval.py` + thresholds |
| CI | `.github/workflows/ci.yml` (tests, audit, diagrams) |
| Nightly eval | `eval-nightly.yml` |
| CD | `cd.yml` images / deploy |

---

## 10. Security & residual risks (honest)

| Control | Status |
|---------|--------|
| Input injection guardrails | Implemented |
| Output PII redaction | Implemented |
| Action allowlist | Implemented |
| Rate limit | In-process or Redis |
| Admin token for pipelines | Optional setting |
| End-user OIDC/JWT | **Not productized** (demo open) |
| Encrypted Bolt in demo | Often plain local |
| Simulated fixture honesty | Provenance flags |

See `security/threat-model.md`, governance docs, runbooks.

---

## 11. OEM catalog (13 products)

10 OEM builders in `oem_product_catalog.py` + 3 legacy `wm-001` / `dw-001` / `mw-001` (extensions + synthetic).
Public-doc-pattern data; part numbers representative, not secret OEM SKUs.

---

## 12. How to navigate the codebase in 30 minutes

| Minute | Action |
|--------|--------|
| 0–5 | Read README architecture + this §1–3 |
| 5–10 | Skim `api/main.py` routes |
| 10–15 | Read `services/diagnosis_service.py` + `agents/diagnosis_graph.py` |
| 15–20 | Skim `graph_rag.diagnose` outline + `reliability.py` headers |
| 20–25 | Read `orchestrator.py` + `knowledge_etl.py` |
| 25–30 | Open `frontend/lib/api.ts` + glance `page.tsx` tabs |

---

## 13. Explicit non-goals / gaps

- Not a full multi-tenant SaaS with OIDC out of the box
- Not a live SAP/Salesforce connector (mock + fixtures by default)
- Not vector-DB-first RAG (graph-first; hybrid lexical optional)
- Not requiring LLM spend for core path
- Remaining scale items: async ETL workers, Neo4j HA, Postgres ops DB, claim→learning loop

---

## 14. Index of “where is X?”

| Need | Go to |
|------|--------|
| HTTP entry | `api/main.py` |
| Business rules once | `services/diagnosis_service.py` |
| Agent steps | `agents/diagnosis_graph.py` |
| Diagnosis brain | `graph/graph_rag.py` |
| Scoring math | `graph/reliability.py` |
| Parts | `graph/parts_predictor.py` |
| Trees | `graph/diagnostic_engine.py` |
| Load Neo4j | `graph/populate_graph.py` |
| ETL | `graph/enterprise_pipeline/` |
| OEM content | `graph/oem_product_catalog.py` |
| Settings | `config/settings.py` |
| UI API client | `frontend/lib/api.ts` |
| Mock backends | `simulation/mock_enterprise_apps.py` |
| Redis/cache | `runtime/` |
| Guardrails | `guardrails/` |
| Metrics/traces | `observability/` |
| LLM optional | `gateway/` + `models/registry.yaml` |
| Eval gate | `evals/run_eval.py` |
| K8s | `k8s/` |
| Diagrams | `docs/graphviz/` 39–41, C4 |

---

*End of encyclopedia body. Prefer the PDF for print/share; keep this MD as the editable source of truth for the full project inventory.*
