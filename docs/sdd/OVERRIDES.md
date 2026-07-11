# Project overrides (this product only)

**Conflict rule:** This file **wins** over platform defaults in `MUST.md` **only when the override is explicit**. Silent deviation is a defect.
When forking to a new vertical: rewrite this file **before** serious coding.

## Identity

| Field | This project (WarrantyGraph) |
|-------|------------------------------|
| Domain | Appliance warranty remote diagnostics |
| Primary users | Customer, Agent, Analyst, Admin |
| Success metrics | Correct ranked failure mode + CONFIRMS steps + provenance; promote-safe KG updates |

## Topology changes vs baseline SDD

| Item | Override |
|------|----------|
| Dual graph | **NO change** — keep dual (prod :7687, staging :7688) |
| Admin UI in v1 | **Present** — Next.js Admin wizard |
| Auth | **Demo open** by default; optional admin token — **not** production OIDC (see gaps) |
| Neo4j secrets | Local defaults `neo4j/password` — **override for any shared deploy** |

## Ontology

| Item | This project |
|------|--------------|
| Entity names | Product, Model, SKU, Asset, Symptom, ErrorCode, FailureMode, DiagnosticStep, Component, Part, Claim, HistoricalResolution, WarrantyPolicy |
| Ranking theory | FMEA-style S/O/D + RPN/Action Priority + Naive Bayes over likelihood edges |
| Text match | Hybrid lexical + TF-IDF |
| Steps | Prefer CONFIRMS edges to top failure mode (+ limited entry prereqs) |
| Multi-source demo packs | e.g. `hmd-001` (dehumidifier), `esp-001` (espresso) under `data/pipeline_sources/` + enterprise fixtures |

## Sources

| Item | This project |
|------|--------------|
| SoR pattern | PIM, FSM, Claims, CRM (+ semi/unstructured packs) |
| Fixture-only until | Live SAP/Salesforce/etc. **not** productized — fixtures + optional mock HTTP |
| Demo mode | `demo_mode` / fixture fallback **ON** by default |

## Explicitly deferred gaps (from `08-GAPS.md` / SDD §6)

Mark v1 scope honestly. Agents must not “implement enterprise auth” unless this section says so.

| Gap cluster | In this repo v1? |
|-------------|------------------|
| P0 AuthN/Z OIDC + tenant ACL | **Deferred** (demo) |
| P1 Live SoR connectors | **Deferred** — pattern + fixtures |
| P1 Async ETL job queue | **Deferred** — sync in API process |
| P1 Redis multi-replica required | **Optional** — memory default single-node |
| P1 Graph HA | **Deferred** — dual single-node Docker |
| P2 SHACL engine / learning loop | **Deferred** |

## Forbidden platform changes (agents must not remove)

- Keep dual graph (prod + staging).
- Keep selection-scoped promote and fail-closed empty selection.
- Keep shared TBox + pipeline ABox (no per-pack OWL generation).
- Keep production-only diagnose read path.
- Keep pack-under-TBox CI tests once present.
- Keep honest labeling of fixture vs live sources.

## New vertical fork template

When starting a **different** product, replace the tables above and keep structure:

```text
Domain: ________
Primary user: ________
Topology deltas: ________
Entity names / ranking: ________
SoR list + fixture deadline: ________
v1 gap scope: ________
Forbidden platform removals: ________
```
