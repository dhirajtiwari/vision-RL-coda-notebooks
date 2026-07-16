# Phases + exit gates

**Use:** identify the current phase; implement only that exit gate.
**Before P0 on a greenfield fork:** mark which P0/P1 gaps in `08-GAPS.md` are in scope for v1.

| Phase | Build | Module to open | Exit proof |
|-------|--------|----------------|------------|
| **P0** | Compose dual graph + API Dockerfile + `/health` | `01-PLATFORM-DOCKER.md` | Health green; both graphs reachable |
| **P1** | Domain TBox module + shape validator | `05-DOMAIN-ONTOLOGY.md` | Validate one empty-safe golden pack |
| **P2** | Connectors/fixtures + materialize + promote | `02-PLATFORM-INGEST.md` | Nodes in **production** graph |
| **P3** | Online query + ranking + provenance | `06-DOMAIN-ONLINE.md` | Golden phrase test passes |
| **P4** | Admin control plane + selection + smoke/approve | `02-PLATFORM-INGEST.md` | Wizard E2E |
| **P5** | Runtime: parallel, caches, rate, admission, lineage | `03-PLATFORM-RUNTIME.md` | `/health` → `runtime` populated |
| **P6** | UI personas | `06-DOMAIN-ONLINE.md` | Manual smoke |
| **P7** | CI workflows + pack contract tests | `04-PLATFORM-CI.md` | PR green |
| **P7b** | LLMOps Tier 1 (obs, guardrails, evals, security, runbooks) | `09-PLATFORM-LLMOPS.md` | Eval smoke + guardrail tests green; residual risks listed |
| **P7c** | LLMOps Tier 3 ready-but-inactive (gateway/prompts/finops) | `09-PLATFORM-LLMOPS.md` | `LLM_ENABLED=false`; registry pinned; budget module present |
| **P8** | Second multi-source pack + session reset | `02` + `05` | Fleet story works |
| **P9** | Production hardening — scoped §6 P0/P1 only | `08-GAPS.md` + `09` | Beyond demo as scoped |
| **P9b** | Scale & populate depth — weighted route, strong/weak resolve, ontology CI gate, page-cache/NetworkPolicy, cluster reference | `10-SCALING-POPULATING-KG.md` | Route endpoint answers; ontology gate green; cluster manifests tagged REFERENCE |

## This repo status (WarrantyGraph baseline 2026-07)

Phases **P0–P8** including **P7b/P7c LLMOps** are largely **as-built** (LLM path inactive by design). Treat new work as:

- **Parity fixes** under existing phases (must update `AS_BUILT.md`), or
- **P9 / gap work** only when `OVERRIDES.md` / product owner scopes it.

## Exit gate checklists (parity maturity)

### Platform (`07-ACCEPTANCE.md` detail)

- [ ] `docker compose` starts prod + staging graphs (Redis optional)
- [ ] API `/health` reports both graphs + runtime block
- [ ] Pipeline: extract → materialize → smoke → promote
- [ ] Parallel extract, serial transform
- [ ] Selection-scoped materialize/promote; empty selection fail-closed when work exists
- [ ] Promote staging then production; diagnose reads production only
- [ ] Named caches + invalidate after promote/load
- [ ] Rate limit + concurrent admission
- [ ] Lineage/audit of admin actions
- [ ] CI: lint + tests + pack-under-TBox + UI build + eval smoke
- [ ] Demo/live labeling for fixtures
- [ ] Anti-pattern checklist (`NEVER.md` / `08-GAPS.md` §6.7) team-reviewed
- [ ] LLMOps Tier 1 + ready Tier 3 (see `09-PLATFORM-LLMOPS.md`)

### Domain

- [ ] Shared TBox module (exportable)
- [ ] ≥1 multi-source ABox pack validated without per-entity OWL
- [ ] E2E promote + identity-bound diagnose with ranked result + steps + provenance
- [ ] Admin path: fetch → select → validate → materialize → smoke → approve → promote
- [ ] Idle/reset path after fleet in-sync

## Agent rule

Cannot claim a phase **done** unless:

1. Exit checkboxes for that phase are true, **and**
2. Listed tests pass, **and**
3. `AS_BUILT.md` reflects committed code.
