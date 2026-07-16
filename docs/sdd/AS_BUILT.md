# AS_BUILT — code-true state

**Rule:** After each phase or material PR, update this file from **what was committed**, not from wish-list prose.
**Baseline date:** 2026-07-11 (WarrantyGraph).
**Full narrative:** `docs/23-Spec-Driven-Development-Platform-and-Domain.md` §1.

## Status summary

| Area | State |
|------|--------|
| Dual Neo4j (prod 7687 / staging 7688) | Implemented |
| Control-plane pipelines + Admin wizard | Implemented |
| Selection-scoped materialize/promote | Implemented |
| Shared TBox + pipeline ABox (multi-source packs) | Implemented |
| Runtime: parallel extract, caches, rate, admission | Implemented |
| Multi-source CI (`test_multi_source_tbox_abox`) | Implemented |
| Weighted diagnostic route (APOC `apoc.algo.dijkstra` + native `shortestPath` fallback) | Implemented (`graph/diagnostic_path.py`, `GET /graph/diagnostic-route`) |
| Strong/weak node resolution (difflib token-sort + stem; near-dup review) | Implemented (`graph/enterprise_pipeline/entity_resolution.py`, wired into `ontology_validate`) |
| Schema-bound LLM unstructured extractor (TBox-bound, off by default) | Implemented ready-but-inactive (`extractors/llm_graph_extract.py` — ChatOpenAI structured output, cheapest `LLM_EXTRACT_MODEL`=gpt-4o-mini, key from env, FinOps budget check/record, `POST /admin/pipeline/llm-extract`; `LLM_ENABLED=false` default) |
| Ontology/SHACL merge-block CI gate | Implemented (`scripts/validate_ontology_ci.py`, `.github/workflows/ontology-validation.yml`) |
| Page-cache tuning + Neo4j NetworkPolicy | Implemented (`k8s/base/neo4j-networkpolicy.yaml`, StatefulSet + compose page cache) |
| Neo4j Core-Replica cluster manifests | **Reference-only** (`k8s/cluster/` — Enterprise license + multi-node blockers) |
| LLMOps Tier 1 (obs, guardrails, evals, security, runbooks) | Implemented |
| LLMOps Tier 3 (gateway, PromptOps, FinOps) | **Ready-but-inactive** (`llm_enabled=false`) |
| Fault-code vision ML (GAN lab + OCR package + MLOps playbook) | **Scaffold** — `notebooks/fault_code_*`, `ml/fault_code_vision/`, registry stubs `fault-code-ocr`/`fault-code-gan` inactive; not on diagnose hot path yet |
| Diagnostic RL (bandits / Q / DQN playbook) | **Scaffold** — `ml/fault_code_rl/`, `notebooks/fault_code_rl_playbook.ipynb`, registry `diagnosis-step-bandit`/`diagnosis-session-dqn` inactive; re-rank only, does not replace GraphRAG |
| Observability stack (Prometheus scrape + Grafana + Tempo) | Implemented + **proven** (targets up, rules load) |
| CI supply chain (Trivy scan + SBOM/provenance + cosign sign + CodeQL) | Implemented |
| Progressive delivery | Eval-gate in CD + opt-in Argo canary manifests (needs cluster for live) |
| Terraform / cloud landing zone | Scaffold placeholders |
| OIDC / tenant ACL | **Not** productized |
| Live enterprise SoR connectors | Fixtures + mock pattern only |
| Async job queue | Not built (sync in API) |

## Infra (as-built)

| Service | Host ports | Role |
|---------|------------|------|
| Graph production | Bolt **7687**, Browser **7474** | Diagnose + explorer **read** |
| Graph staging | Bolt **7688**, Browser **7475** | Promote-first MERGE |
| Redis | **6379** | Optional; empty URL → in-process memory |
| API | **8080** | FastAPI |
| Frontend | **3000** | Next.js |
| Mock SoR | **8090** | Optional |

Compose: `docker/docker-compose.infra.yaml`. Dockerfiles under `docker/`.

## Pipeline registry IDs (as-built)

`structured_extract`, `semi_structured_ingest`, `unstructured_extract`, `preprocess_normalize`, `knowledge_materialize`, `smoke_validate`, `promote_graph`, `bootstrap_all`, `incremental_sync`.

Operator sequence: Sources → Fetch → Select → Validate → Materialize → Smoke → Approve → Promote staging → Promote production → optional `session/reset-for-next-cycle`.

## Runtime defaults (as-built)

| Knob | Default |
|------|---------|
| Connector extract workers | 4 |
| Ontology cache TTL | 300s |
| Subgraph cache TTL | 60s |
| Diagnose cache | ON, 90s, max 512 |
| Rate limit | 60/min |
| Max concurrent diagnoses | 32 |
| Neo4j pool | 50 |
| Redis | memory if no `REDIS_URL` |
| Demo / fixture fallback | ON |

Prove via `GET /health` → `runtime`.

## Domain packs (as-built demos)

- Multi-source: `hmd-001`, `esp-001` (+ manifests under `data/pipeline_sources/`)
- Enterprise fixtures: PIM / FSM / Claims / CRM assets
- Ranking: FMEA + Bayes; hybrid lexical + TF-IDF; CONFIRMS-targeted steps

## CI (as-built)

- `.github/workflows/ci.yml` — secret scan (gitleaks), ruff, multi-source/TBox tests, pytest+coverage, eval smoke, frontend build; **CodeQL** SAST + **Trivy** fs/config scan; image build with **SBOM + provenance**, **Trivy image scan** (fail HIGH/CRITICAL), **cosign** keyless signing
- `.github/dependabot.yml` — managed actions/pip/npm/docker updates
- `.github/workflows/cd.yml` — **eval-gate** job before any deploy; rolling default, opt-in `deploy_strategy: canary` (Argo Rollouts + `deploy/policy/verify-images.yaml`)
- Triggers: `main` and `feature/**`
- Gate file: `tests/test_multi_source_tbox_abox.py`
- Eval: `python evals/run_eval.py --suite smoke` in CI; full in `eval-nightly.yml`

## LLMOps (as-built)

| Discipline | State | Path |
|------------|-------|------|
| Observability | ACTIVE | `observability/` — JSON logs, Prometheus, OTEL opt-in, redaction |
| Guardrails | ACTIVE + **red-teamed** | `guardrails/` — input/output/action/rate; injection covers ignore/forget-instructions, role-injection, data/secret exfil, cypher; wired in `api/main.py` |
| EvalOps | ACTIVE | `evals/` — golden smoke + **calibrated** `golden/diagnosis.jsonl` (13 cases) + safety injection (8 attack classes); `thresholds.yaml` |
| FinOps | READY | `finops/budget.py` — daily USD budget when LLM called |
| Gateway | READY inactive | `gateway/` + `models/registry.yaml` |
| PromptOps | READY inactive | `promptops/` + `prompts/` |
| Security docs | ACTIVE | `security/threat-model.md`, `owasp-llm-mapping.md` |
| Governance | ACTIVE docs | `docs/governance/`, `docs/model-cards/system-card.md` |
| Runbooks | ACTIVE | `docs/runbooks/*` (7) |
| Monitoring stack | ACTIVE + **wired** | `monitoring/prometheus/prometheus.yml` (scrape) + `rules/`, `monitoring/grafana/provisioning/` + dashboards, `monitoring/tempo/`, `otel-collector.yaml`; prod: `k8s/monitoring/` (ServiceMonitor + PrometheusRule) |
| Handbook / playbook | Reference | `docs/llmops-handbook/` 00–21 + playbook (kickoff §A–O updated to OWASP 2025 / agentic / AI-BOM / EU AI Act) |
| ADR | Accepted | `docs/adr/0001-adopt-llmops-disciplines.md` |

**Defaults:** `llm_enabled=false`, `otel_enabled=false`, `enable_prometheus_metrics=true`, `enable_pii_redaction=true`, `rate_limit_per_minute=60`, `llm_cost_budget_usd_per_day=5.0`.

## Explicit non-claims

Do not tell buyers or agents these are done: OIDC multi-tenant ACL, live SAP/SFDC, Neo4j HA, async ETL queue, external SHACL engine, per-product OWL generation (by design not done), LLM as primary reasoner, live multi-cluster canary, full cloud Terraform landing zone, formal regulatory certification, OWL reasoner (HermiT/Pellet) on diagnose path, KGE/pykeen edge imputation, Neo4j Fabric multi-shard, Kafka streaming write path, vector-index-first retrieval.

**Scale & populate (module `10`) status nuance:** the **weighted diagnostic route** is real via **APOC** (`apoc.algo.dijkstra`) with a native `shortestPath()` fallback — but **GDS** (Dijkstra/Delta-Stepping/A*/Yen's) is **not installed**; do not claim GDS shortest-path. **Strong/weak resolution** is real via stdlib fuzzy matching — but **embedding-similarity** merge is `[REFERENCE]`. **SHACL-style** validation is a lightweight in-code validator — an **external SHACL/OWL reasoner** is not wired. The **Core-Replica cluster / read-replica pool / Helm-Operator** manifests under `k8s/cluster/` are `[REFERENCE]` (Neo4j **Enterprise license** + multi-node required); the demo runs a single-node StatefulSet + separate staging (environment partition, not HA).

## Documentation map (patterns + interview)

| Doc | Role |
|-----|------|
| [`../25-Delta-Partitioning-Concurrency-Sharding-Implementation.md`](../25-Delta-Partitioning-Concurrency-Sharding-Implementation.md) | **Delta stepping, partitioning, concurrency, sharding** — as-built vs gaps + step-by-step implement/run |
| [`../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md) | Canonical **AS-BUILT / LITE / ROADMAP / OUT-OF-SCOPE** for TBox origin, sparse data, scale, CAP, demo-vs-enterprise |
| [`../22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`](../22-TBox-ABox-Multi-Source-Onboard-Mechanism.md) | Operator TBox/ABox mechanism |
| [`../interview/Master-This-Codebase.md`](../interview/Master-This-Codebase.md) | Memorize/write/explain narrative for whole repo |
| [`../interview/Interview-Mastery-Guide.md`](../interview/Interview-Mastery-Guide.md) | Persona Q&A appendix |

## Change log (agent append-only)

| Date | Change | Code / PR note |
|------|--------|----------------|
| 2026-07-11 | Initial AS_BUILT from live tree + SDD §1 | `docs/sdd/` kit scaffolded |
| 2026-07 | Multi-source TBox/ABox packs, selection/promote UX, runtime health | feature branch LLMOps remote diagnostics |
| 2026-07-11 | LLMOps disciplines folded into SDD kit (`09-PLATFORM-LLMOPS.md`) | Handbook/playbook/ADR/code inventory |
| 2026-07-15 | Docs: patterns doc 24 + Master-This-Codebase interview narrative; non-claims expanded | docs-only alignment pass |
| 2026-07-15 | Observability wired + proven (prometheus.yml scrape, Grafana provisioning, Tempo, `k8s/monitoring/`); CI hardened (CodeQL, Trivy fs+image, SBOM/provenance, cosign, dependabot); CD eval-gate + opt-in Argo canary | ci.yml, cd.yml, docker/compose obs, monitoring/, k8s/monitoring/ |
| 2026-07-15 | Eval ground-truth: calibrated `golden/diagnosis.jsonl` + expanded `safety/injection.jsonl`; guardrail red-team closed forget-instructions/role-injection/exfil gaps (0 false positives) | evals/, guardrails/input.py |
| 2026-07-15 | SDD kit updated for greenfield replication (NEVER/MUST/01/04/09/README); kickoff prompt + todo §1.7 aligned to 2025 authoritative practice | docs/sdd/, docs/llmops-handbook/20, todo.md |
| 2026-07-15 | Doc 25: delta/partition/concurrency/sharding as-built + implementation steps (authoritative Neo4j sources) | docs/25-… |
| 2026-07-16 | Doc 25 §1.5 indexing code/run; Study Lab Masters mc-03 graph ops (indexes/delta/partition/concurrency); Turtle mc-01 unchanged; flashcards 5W+H for unique constraints + entity delta | docs/25 §1.5, study/masterclasses.py, study/masterclass_cards.py, study/flashcards_deck.py |
| 2026-07-16 | Scale & populate implementation: weighted diagnostic route (APOC dijkstra + shortestPath fallback, `/graph/diagnostic-route`); strong/weak entity resolver + near-dup review; schema-bound LLM extractor (off by default); ontology CI gate; Neo4j page-cache + NetworkPolicy; reference Enterprise cluster manifests; SDD module `10` + MUST/NEVER/PHASES/README + kickoff prompt | graph/diagnostic_path.py, graph/enterprise_pipeline/entity_resolution.py, extractors/llm_graph_extract.py, scripts/validate_ontology_ci.py, .github/workflows/ontology-validation.yml, k8s/base+cluster, docs/sdd/10 + kit, study mc-04 |
| 2026-07-16 | LLM extractor activated opt-in: ChatOpenAI structured-output bound to TBox + code allow-list filter, cheapest `LLM_EXTRACT_MODEL`=gpt-4o-mini, key from env, **FinOps budget check/record**, admin endpoint `POST /admin/pipeline/llm-extract`; SDD module 10 + MUST/NEVER + kickoff §P updated | extractors/llm_graph_extract.py, config/settings.py, api/main.py, .env.example, docs/sdd/10+MUST+NEVER+AS_BUILT, docs/llmops-handbook/20 |
