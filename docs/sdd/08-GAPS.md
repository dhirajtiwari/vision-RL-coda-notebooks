# 08 — Gaps, value, anti-patterns

**Load when:** planning beyond parity (P9), roadmap, buyer honesty.
**Do not load** for a single narrow implement task (use NEVER/MUST instead).
**Full tables:** `docs/23-Spec-Driven-Development-Platform-and-Domain.md` §6.

## How to read

| Column | Meaning |
|--------|---------|
| Gap | Not complete in as-built baseline |
| Pri | P0 real multi-tenant prod · P1 integration/scale · P2 quality · P3 later |

**Rule:** Gaps are mostly connectors, platform, security, scale — **not** “missing a new ontology per product.”

## Priority pyramid

```text
P0  Identity + tenant isolation          → can sell / can audit
P1  Live connectors + async ETL          → continuous knowledge
P1  Redis multi-pod + graph HA + load    → stays up under traffic
P1  Pack contract + hermetic CI          → delivery quality
P2  Learning loop, SHACL CI, NLP         → accuracy over time
P3  Multi-region, vector indexes         → only when scale forces it
```

## Gap clusters (summary)

### Identity / security (P0–P1)

| Gap | As-built | Pri |
|-----|----------|-----|
| End-user AuthN/Z (OIDC/JWT) | Demo often open; optional admin token | **P0** |
| Tenant ACL / hard isolation | Logical tenant keys only | **P0** |
| Encrypted Bolt + secret vault | Local password defaults | **P1** |
| Dual-control promote | Session approve + optional token | **P1** |

### Enterprise integration (P1)

| Gap | As-built | Pri |
|-----|----------|-----|
| Live SoR connectors | Fixtures + optional mock HTTP | **P1** |
| Async ETL workers / job queue | Sync inside API process | **P1** |
| Postgres multi-writer ops DB | SQLite some paths | **P1** |
| CDC / event bus | Register-asset pattern only | **P1** |
| Contract tests vs real APIs | Mock-oriented | **P1** |

### Knowledge quality (P2)

External SHACL/OWL reasoner in CI; RDF import; closed-loop learning; supersession chains; richer procedure trees; full NER; multi-language; less hardcoded product keywords; vector indexes at scale (**P3**).

**Documented with status tags (not “missing docs”):** full sparse-data strategy matrix, CAP, demo-vs-enterprise, and industry patterns live in [`../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md). Interview coverage: [`../interview/Master-This-Codebase.md`](../interview/Master-This-Codebase.md).

**Not a gap:** generating new OWL schema per product pack. Correct design = shared TBox + pipeline ABox.

### Runtime / scale (P1–P2)

Redis required multi-replica; graph HA; load suite; OTEL default-on; product-level parallel transform chunks; hermetic CI.

**Already good:** dual graph, selection promote, parallel extract, caches, rate/admission, lineage, pack TBox tests.

### LLMOps residual (vs handbook full enterprise)

| Gap | As-built | Pri |
|-----|----------|-----|
| OTEL default-on in prod | Flag off by default | **P2** |
| LLM semantic response cache | Diagnose cache only; LLM path optional | **P2** |
| Live progressive delivery (Argo/Flagger) | Manifests scaffold | **P1** when multi-cluster |
| Full Terraform cloud landing zone | Placeholders | **P1** when cloud target fixed |
| Formal compliance certification | Docs/drafts only | Legal track |
| LLM as primary reasoner | Deterministic GraphRAG primary | By design / OVERRIDES |

**Already good (do not rebuild from zero):** guardrails, rate limit, eval+safety gate, JSON logs, Prometheus, redaction, ready gateway/PromptOps/FinOps, threat model, OWASP map, system card, runbooks, ADR 0001.

Detail module: `09-PLATFORM-LLMOPS.md`.

## Anti-patterns (must not repeat)

Short form lives in **`NEVER.md`**. Narrative tables: docs/23 §6.7 + playbook §8.

Clusters: ontology/knowledge · ingest/promote/dual graph · diagnosis/UX · engineering process · **LLMOps** (prompt-only controls, `latest` models, loosened thresholds, handbook-as-context-dump).

## Kickoff checklist (new project)

- [ ] Copy or keep this file; mark P0/P1 **in scope for v1** vs deferred in `OVERRIDES.md`
- [ ] Anti-pattern review for first 4 sprints
- [ ] Never mark P0 auth as “later” if external users hit the API
- [ ] Never invent per-entity OWL in sprint 1 “to look complete”

## This repo v1 scope note

See `OVERRIDES.md` — demo defaults defer OIDC, live SoR, async queue, HA.
