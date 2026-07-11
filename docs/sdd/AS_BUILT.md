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
| LLMOps Tier 1 (obs, guardrails, evals, security, runbooks) | Implemented |
| LLMOps Tier 3 (gateway, PromptOps, FinOps) | **Ready-but-inactive** (`llm_enabled=false`) |
| Progressive delivery / Terraform | Scaffold manifests/placeholders |
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

- `.github/workflows/ci.yml` — secret scan, ruff, multi-source/TBox tests, pytest, eval smoke, frontend build, images
- Triggers: `main` and `feature/**`
- Gate file: `tests/test_multi_source_tbox_abox.py`
- Eval: `python evals/run_eval.py --suite smoke` in CI; full in `eval-nightly.yml`

## LLMOps (as-built)

| Discipline | State | Path |
|------------|-------|------|
| Observability | ACTIVE | `observability/` — JSON logs, Prometheus, OTEL opt-in, redaction |
| Guardrails | ACTIVE | `guardrails/` — input/output/action/rate; wired in `api/main.py` |
| EvalOps | ACTIVE | `evals/` — golden smoke + safety injection; `thresholds.yaml` |
| FinOps | READY | `finops/budget.py` — daily USD budget when LLM called |
| Gateway | READY inactive | `gateway/` + `models/registry.yaml` |
| PromptOps | READY inactive | `promptops/` + `prompts/` |
| Security docs | ACTIVE | `security/threat-model.md`, `owasp-llm-mapping.md` |
| Governance | ACTIVE docs | `docs/governance/`, `docs/model-cards/system-card.md` |
| Runbooks | ACTIVE | `docs/runbooks/*` (7) |
| Monitoring configs | ACTIVE | `monitoring/` prometheus/grafana/otel-collector |
| Handbook / playbook | Reference | `docs/llmops-handbook/` 00–21 + playbook |
| ADR | Accepted | `docs/adr/0001-adopt-llmops-disciplines.md` |

**Defaults:** `llm_enabled=false`, `otel_enabled=false`, `enable_prometheus_metrics=true`, `enable_pii_redaction=true`, `rate_limit_per_minute=60`, `llm_cost_budget_usd_per_day=5.0`.

## Explicit non-claims

Do not tell buyers or agents these are done: OIDC multi-tenant ACL, live SAP/SFDC, Neo4j HA, async ETL queue, external SHACL engine, per-product OWL generation (by design not done), LLM as primary reasoner, live multi-cluster canary, full cloud Terraform landing zone, formal regulatory certification.

## Change log (agent append-only)

| Date | Change | Code / PR note |
|------|--------|----------------|
| 2026-07-11 | Initial AS_BUILT from live tree + SDD §1 | `docs/sdd/` kit scaffolded |
| 2026-07 | Multi-source TBox/ABox packs, selection/promote UX, runtime health | feature branch LLMOps remote diagnostics |
| 2026-07-11 | LLMOps disciplines folded into SDD kit (`09-PLATFORM-LLMOPS.md`) | Handbook/playbook/ADR/code inventory |
