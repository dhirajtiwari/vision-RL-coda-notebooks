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

## Explicit non-claims

Do not tell buyers or agents these are done: OIDC multi-tenant ACL, live SAP/SFDC, Neo4j HA, async ETL queue, external SHACL engine, per-product OWL generation (by design not done).

## Change log (agent append-only)

| Date | Change | Code / PR note |
|------|--------|----------------|
| 2026-07-11 | Initial AS_BUILT from live tree + SDD §1 | `docs/sdd/` kit scaffolded |
| 2026-07 | Multi-source TBox/ABox packs, selection/promote UX, runtime health | feature branch LLMOps remote diagnostics |
