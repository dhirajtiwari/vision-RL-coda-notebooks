# Spec-Driven Development (SDD) — Platform vs Domain
## Self-contained blueprint for a **fresh** project (any machine)

| Field | Value |
|-------|--------|
| **Code truth baseline** | Verified against **this repository’s live tree and settings** (WarrantyGraph / remote-diagnostics) as of **2026-07-11** |
| **Audience** | You, future you, AI coding agents, new engineers |
| **Goal of the spec** | On a **empty machine / empty repo**, build to **parity with this project’s as-built maturity**, then extend |
| **Docker** | **Default delivery model** (infra compose + service Dockerfiles) |
| **Dependency on this machine** | **None required** — this document is self-contained. Paths below are *examples of as-built names*, not prerequisites to have this laptop. |

---

## 0. Why this exists (and how to use it carefully)

### 0.1 Code is truth

Other docs in a monorepo can lag. For **SDD**, treat:

1. **Running code + tests + compose files** as the source of truth for “what is implemented.”
2. This SDD as a **portable contract** that *describes* that truth in platform vs domain terms.
3. Anything **not** proven by code as **OUT OF SCOPE / TARGET** (gaps), never as “already built.”

When code and this file disagree later: **update this file**, do not invent behavior in prose.

### 0.2 Fresh machine principle

A useful SDD must work when:

- You have **no** prior clone of WarrantyGraph.
- You have **no** access to `docs/22`, handbook PDFs, or interview guides.
- You only have: **this SDD (or a copy of it)** + a blank git repo + Docker + Python/Node.

Therefore this document **embeds** the rules, topology, exit gates, and module responsibilities. It does **not** say “see doc X on machine Y.” Optional “as-built map” at the end is only for people who *do* have this repo open.

### 0.3 Two layers (always)

```text
PLATFORM  = reusable for any multi-source knowledge + query product
DOMAIN    = this vertical’s entities, scoring, fixtures, UI copy
```

| Fork for new vertical | Action |
|----------------------|--------|
| Platform | Keep architecture, Docker, control plane, runtime, CI shape |
| Domain | Replace ontology labels, seed data, ranking, personas |

### 0.4 Agent-native SDD (Claude Code / Codex / “lost in the middle”)

**Live kit in this repo:** [`docs/sdd/`](./sdd/README.md) (thin always-on files + modular pull-on-demand).
**Repo entrypoint:** root [`AGENTS.md`](../AGENTS.md) points agents at that kit.
This section is the **design contract**; prefer editing the live files under `docs/sdd/` for day-to-day agent use, then sync bullets back here when the contract changes.

Large models **under-attend the middle** of long prompts/docs. If you paste this entire file into every session, agents will miss constraints buried in §6 or §1.5. **Do not rely on one giant context dump.**

#### Design rules for agent builds

| Rule | Practice |
|------|----------|
| **Progressive disclosure** | Always-on files stay tiny (~100–200 lines). Details live in modular specs loaded **only when the task needs them**. |
| **Hard constraints first** | `NEVER.md` / `MUST.md` are short bullet lists — never paragraphs in the middle of a 600-line doc. |
| **Domain overrides explicit** | New project nuances go in `OVERRIDES.md` and **win** over platform defaults when they conflict. |
| **Phase = context pack** | Agent loads only the specs for the **current phase** (e.g. P0 Docker: only `01-PLATFORM-DOCKER.md` + `NEVER.md`). |
| **Exit gates as tests** | What must be true is encoded in **checklists + pytest**, not only prose. |
| **Code remains truth** | After each phase, agent updates `AS_BUILT.md` from **what was committed**, not from wish-list prose. |
| **One task, one module** | Prompt: “Implement selection-scoped promote per `02-…` §X; do not redesign auth.” |

#### Always-on vs pull-on-demand (greenfield layout)

```text
docs/sdd/
  AGENTS.md              # ALWAYS load — role, order of work, which files to open
  NEVER.md               # ALWAYS load — ≤40 bullets, anti-patterns (from §6.7)
  MUST.md                # ALWAYS load — platform non-negotiables (dual graph, TBox/ABox…)
  OVERRIDES.md           # ALWAYS load — THIS project’s differences vs baseline
  PHASES.md              # ALWAYS load — phase table + exit gates only
  01-PLATFORM-DOCKER.md  # pull when doing infra
  02-PLATFORM-INGEST.md  # pull when doing pipelines
  03-PLATFORM-RUNTIME.md # pull when doing cache/parallel
  04-PLATFORM-CI.md
  05-DOMAIN-ONTOLOGY.md  # pull when defining entities / packs
  06-DOMAIN-ONLINE.md
  07-ACCEPTANCE.md
  08-GAPS.md             # pull when planning beyond parity or production
  AS_BUILT.md            # agent updates after each phase (code-true)
  REFERENCE-FULL.md      # optional: this entire docs/23 for humans only
```

**Session budget (recommended):**

| Tokens / attention | Files |
|--------------------|--------|
| Every agent session | `AGENTS.md` + `NEVER.md` + `MUST.md` + `OVERRIDES.md` + `PHASES.md` + current task file |
| Never by default | Full `REFERENCE-FULL.md` / entire monorepo encyclopedia |

#### `AGENTS.md` skeleton (paste into every new project)

```markdown
# Agent instructions (always read first)

## Role
You implement a Docker-first multi-source knowledge + query system.
Platform rules are fixed unless OVERRIDES.md changes them.

## Before any code
1. Read NEVER.md and MUST.md completely.
2. Read OVERRIDES.md — if a conflict exists, OVERRIDES wins and you record it in AS_BUILT.md.
3. Open PHASES.md; identify current phase exit gate.
4. Open ONLY the module file for this task (01…08). Do not invent requirements from memory.

## While coding
- Prefer smallest change that satisfies the exit gate.
- Do not generate per-entity OWL/TBox files for new packs.
- Do not make chat/read path use staging graph.
- Do not promote without explicit selection when work exists.
- After implement: run the phase’s tests; update AS_BUILT.md with what code actually does.

## Done definition
Exit gate checkboxes for this phase are true AND tests pass AND AS_BUILT.md updated.
```

#### `NEVER.md` skeleton (keep short — always in context)

```markdown
# NEVER (hard fail if agent does these)
- NEVER invent a new ontology/schema language per product/device pack (ABox only under shared TBox).
- NEVER point online query/chat at staging graph as production.
- NEVER promote the whole fleet when operator selected a subset.
- NEVER cache query answers by raw message alone (must include identity + catalog/version).
- NEVER claim live SoR integration when only fixtures run — label simulated.
- NEVER hard-block diagnose solely on soft text mismatch when asset is already bound.
- NEVER bury new constraints only in a long essay — add a NEVER/MUST bullet.
- NEVER skip updating AS_BUILT.md after a phase.
```

#### `OVERRIDES.md` — how new projects differ safely

New projects will **not** match WarrantyGraph 1:1. Capture deltas here so agents don’t “fix” domain-specific choices.

```markdown
# Project overrides (this product only)

## Identity
- Domain: ________
- Primary user: ________

## Topology changes vs baseline SDD
- e.g. single graph only: NO (default dual) | YES → document why and read-path rules
- e.g. no Admin UI in v1: YES → CLI promote only

## Ontology
- Entity names: ________
- Ranking theory: ________ (if not FMEA+Bayes)

## Sources
- SoR list: ________
- Fixture-only until date: ________

## Explicitly deferred gaps (from §6)
- P0 auth: in v1? yes/no
- Live connectors: phase ____

## Forbidden platform changes
- (list anything agents must not remove, e.g. “keep dual graph”)
```

**Conflict rule:** `OVERRIDES.md` > platform defaults in `MUST.md` **only** when the override is explicit. Silent deviation is a defect.

#### Encoding gates so agents cannot “forget”

| Mechanism | What it forces |
|-----------|----------------|
| **PHASES.md exit checkboxes** | Human/agent cannot claim phase done without list |
| **pytest pack/TBox tests** | CI fails if packs invent unknown keys or break shapes |
| **Compose healthcheck** | Infra not “done” until graphs respond |
| **AS_BUILT.md** | Next session reads code-true state, not stale plan |
| **PR template** | “Which SDD modules did you open? Which NEVER rules apply?” |

#### Handling large REFERENCE-FULL.md

| Audience | How to use this long document |
|----------|-------------------------------|
| **Human architect** | Read end-to-end once; then maintain modular files |
| **Claude Code / Codex** | Do **not** attach full file each turn; attach **AGENTS+NEVER+MUST+OVERRIDES+one module** |
| **Planning agent** | May load §6 gaps when choosing roadmap; not when implementing a single pipeline |
| **Lost-in-middle mitigation** | Put MUST/NEVER at **top of every session**; repeat exit gate at **end of prompt** |

#### Prompt pattern for agents (copy/paste)

```text
Context files: AGENTS.md, NEVER.md, MUST.md, OVERRIDES.md, PHASES.md, 02-PLATFORM-INGEST.md
Task: Implement selection-scoped materialize for phase P4.
Constraints: obey NEVER.md; dual graph; production read path only.
Done when: PHASES.md P4 exit gate true + listed tests pass + AS_BUILT.md updated.
Do not: redesign auth, add per-product OWL, or expand scope to P9 gaps.
```

---

## 1. As-built platform facts (verified in code)

These are **implemented today** (not aspirational). Defaults from live `config/settings.py` and modules.

### 1.1 Docker / infra (as-built)

**Compose file (example name):** `docker/docker-compose.infra.yaml`

| Service | Image | Host ports | Role |
|---------|-------|------------|------|
| Graph **production** | `neo4j:5-community` | Bolt **7687**, Browser **7474** | Online diagnose + explorer **read path** |
| Graph **staging** | `neo4j:5-community` | Bolt **7688**, Browser **7475** | Promote-first MERGE target |
| Redis | `redis:7-alpine` | **6379** | Optional shared cache/rate/admission |

**Service images (as-built Dockerfiles):**

| File | Role |
|------|------|
| `docker/Dockerfile.api` | API + control plane |
| `docker/Dockerfile.frontend` | Web UI |
| `docker/Dockerfile.etl` | Batch/ETL image |
| `docker/Dockerfile.mock` | Simulated enterprise SoR (optional) |
| `docker/Dockerfile.ui` | Legacy/alternate UI image |

**Also present:** `docker-compose.redis.yaml`, `docker-compose.observability.yaml` (optional stacks).

**Auth defaults (demo):** Neo4j `neo4j/password` — **not** production-safe; SDD for real deploys must override secrets.

### 1.2 Application processes (as-built)

| Process | Default port | How started (this project) |
|---------|--------------|----------------------------|
| API | **8080** | `uvicorn api.main:app` (or container) |
| Web UI | **3000** | Next.js `frontend/` |
| Mock SoR | **8090** | optional simulation |

### 1.3 Dual-graph routing (as-built)

| Env | Setting (example) | Used for |
|-----|-------------------|----------|
| Production | `NEO4J_URI=bolt://localhost:7687` | **Diagnosis Chat**, graph reads for customers |
| Staging | `NEO4J_STAGING_URI=bolt://localhost:7688` | First MERGE after approve |

Promote is **not** “write wherever.” Online path must not depend on staging.

### 1.4 Control-plane pipelines (as-built registry IDs)

These pipeline **IDs** exist in code (`graph/enterprise_pipeline/control_plane/registry.py`):

| ID | Purpose |
|----|---------|
| `structured_extract` | PIM / CRM / FSM / Claims connectors |
| `semi_structured_ingest` | CSV / JSONL |
| `unstructured_extract` | Text manuals / tickets |
| `preprocess_normalize` | Quality / normalize staging |
| `knowledge_materialize` | Build catalog ABox (OntologyBuilder) |
| `smoke_validate` | Scenario gate |
| `promote_graph` | MERGE into Neo4j (`target_env`) |
| `bootstrap_all` | Full chain through smoke (no auto-promote) |
| `incremental_sync` | Extract + preprocess + materialize (no auto-promote) |

**Operator sequence (Admin):**
Sources → Fetch (dry-run) → Select products → Validate ABox → Materialize → Smoke → Approve → Promote staging → Promote production → (optional) reset session for next cycle.

### 1.5 Platform runtime knobs (as-built defaults)

| Capability | Default | Module / wiring |
|------------|---------|-----------------|
| Parallel connector extract | **4** workers | `etl_connector_max_workers`, `parallel_map` in knowledge ETL |
| Product transform batch size | **0** (single batch) | `etl_product_batch_size` |
| Ontology schema cache TTL | **300s** | `runtime/cache.py` + graph ontology GET |
| Product subgraph cache TTL | **60s** | Explorer |
| Diagnose result cache | **ON**, TTL **90s**, max **512** | `runtime/diagnose_cache.py`, `services/diagnosis_service.py` |
| Redis | **empty URL** → in-process **memory** | `redis_url`; multi-replica needs `REDIS_URL` |
| Rate limit | **60 / minute** | `guardrails/rate_limit.py` on API |
| Concurrent diagnose admission | **32** | `max_concurrent_diagnoses` |
| Neo4j pool | **50** | driver settings |
| Provenance stamps | **ON** | `enable_provenance` |
| OpenTelemetry | **OFF** | `otel_enabled=false` |
| Demo mode / fixture fallback | **ON** | `demo_mode`, `allow_fixture_fallback` |
| Cache invalidation | On successful ETL load / promote | `invalidate_all_named_caches()` |

### 1.6 Admin API surface (as-built, representative)

Control and gates (not exhaustive list of every route):

- `GET /health` — includes `runtime` (caches, redis mode, workers, pool)
- `POST /diagnose`
- `GET /graph/ontology`, `/graph/product/{id}`, diagnosis subgraph, RDF helpers
- `GET/POST /admin/pipeline/*` — dry-run-etl, change-preview, plan, selection, lock-selection, validate, entity-delta, neo4j-verify, approve-review, promote, **session/reset-for-next-cycle**
- `GET/POST /admin/kg-pipelines/*` — registry run/list
- `GET /admin/ontology/tbox`, validate-selection
- CRM: `/crm/customers`, assets

### 1.7 CI (as-built)

| Workflow | Role |
|----------|------|
| `.github/workflows/ci.yml` | Secret scan, ruff, **multi-source/TBox tests**, full pytest, eval smoke, frontend build, image builds |
| Triggers | `main` and **`feature/**`** push/PR |
| `eval-nightly.yml` | Heavier eval when graph available |
| `cd.yml` | Deploy after CI |

**Test gate for multi-source / TBox discipline (as-built):**
`tests/test_multi_source_tbox_abox.py` (+ related pipeline tests).

### 1.8 Explicitly **not** as-built (do not claim in greenfield “done” until you build them)

From live gaps / partials (see also backlog research):

| Item | Status |
|------|--------|
| OIDC / end-user JWT multi-tenant ACL | **Not productized** |
| Live SAP/Salesforce/etc. connectors | **Pattern + mock/fixtures** |
| Async job queue (Airflow/etc.) | **Not built** (sync in API process) |
| Neo4j HA / multi-region | **Local dual single-node only** |
| Postgres ops multi-writer | **SQLite** for some ops |
| Redis required for demo | **Optional**; memory works single-node |
| External SHACL engine / OWL reasoner in CI | **In-repo shapes only** |
| Per-product OWL generation | **By design not done** |

---

## 2. Ontology rule (platform — non-negotiable)

Embed this in every greenfield SDD; do not outsource to another doc.

| Term | Definition | Fresh-project action |
|------|------------|----------------------|
| **TBox** | Shared **types**: classes + allowed relationships | Define **once** in code (exportable to Turtle/OWL) |
| **ABox** | **Instances** for one device/product/site | Built by pipeline from sources |
| **NEW entity pack** | New ABox under existing classes | **Not** a new schema language |
| **TBox extension** | New *kind* of entity/key unknown to TBox | Detect + human governance; **never auto-merge from a pack** |

**Pipeline ABox build (as-built pattern):**

```text
Connectors (structured) + file extractors (semi/unstructured)
        → parallel extract
        → serial OntologyBuilder / transform
           - typed core instances
           - re-attach rich keys (model/SKU/BOM/links)
           - merge assets/claims when available
        → catalog JSON (selection-scoped upsert)
        → shape validate vs TBox
        → MERGE graph staging → production
```

**Sources on disk ≠ ontology schema built.** Sources feed **instances**. Schema lives in the **platform TBox module**.

---

## 3. Domain layer (this project only — replace on fork)

### 3.1 As-built domain (WarrantyGraph)

| Item | As-built choice |
|------|-----------------|
| Entities | Product, Model, SKU, Asset, Symptom, ErrorCode, FailureMode, DiagnosticStep, Component, Part, Claim, HistoricalResolution, WarrantyPolicy |
| Chain | Asset → Product → Symptom/ErrorCode → FailureMode → DiagnosticStep → Part (+ history/claims) |
| Ranking | FMEA-style S/O/D + RPN/Action Priority + Naive Bayes over graph likelihood edges |
| Text match | Hybrid lexical + TF-IDF; weak scores can still yield strong posteriors if graph links strong |
| Steps | Prefer **CONFIRMS** edges to top failure mode (+ limited entry prereqs) |
| Multi-source demo packs | e.g. dehumidifier + espresso style packs under pipeline + enterprise fixtures |
| UI personas | Customer / Agent / Analyst / Admin |

### 3.2 Domain blanks for a **new** vertical (fill in SDD for that product)

```text
Domain name: ________________
Primary user: ________________
Success metrics: ________________
Entities + identity keys: ________________
Evidence → hypothesis → action chain: ________________
Sources (SoR names): ________________
Ranking theory: ________________
Escalation policy: ________________
5 golden phrases + expected top hypothesis: ________________
```

---

## 4. Greenfield SDD package (what to put in a **new** empty repo)

On a new machine, create these files first. Prefer the **agent-native** set (§0.4) so Claude Code / Codex are not fed one giant middle-heavy doc.

**In this repository the kit is already materialized** at [`docs/sdd/`](./sdd/README.md) (+ root [`AGENTS.md`](../AGENTS.md)). Copy that directory to greenfield forks.

```text
docs/sdd/
  AGENTS.md NEVER.md MUST.md OVERRIDES.md PHASES.md AS_BUILT.md   # always-on, thin
  01-PLATFORM-DOCKER.md      # from §1.1
  02-PLATFORM-INGEST.md      # from §1.4–1.5, §2
  03-PLATFORM-RUNTIME.md     # parallel, cache, rate, admission
  04-PLATFORM-CI.md
  05-DOMAIN-ONTOLOGY.md      # §3 blanks
  06-DOMAIN-ONLINE.md
  07-ACCEPTANCE.md           # §5
  08-GAPS.md                 # §6 full tables (human + planning agents only)
  REFERENCE-FULL.md          # points at this docs/23 for humans
  README.md                  # kit index
AGENTS.md                    # repo root entrypoint → docs/sdd/
```

**Humans** may read `REFERENCE-FULL.md` / this file once. **Agents** use always-on + one module per task (§0.4).

---

## 5. Acceptance gates — “parity with as-built maturity”

A fresh Docker project matches **this codebase’s current maturity** when:

### 5.1 Platform (must)

- [ ] `docker compose` starts **prod graph + staging graph** (Redis optional)
- [ ] API `/health` reports both graphs + **runtime** block (caches, workers, rate backend)
- [ ] Pipeline registry implements extract → materialize → smoke → promote
- [ ] Parallel extract, serial transform
- [ ] Selection-scoped materialize/promote (empty selection rejected when work exists)
- [ ] Promote **staging then production**; diagnose reads **production only**
- [ ] Named caches + invalidate after promote/load
- [ ] Rate limit + concurrent admission
- [ ] Durable lineage/audit of pipeline/admin actions
- [ ] CI: lint + unit/integration tests + pack-under-TBox tests + UI build
- [ ] Demo/live labeling for fixture data
- [ ] **§6 anti-patterns checklist** reviewed by the team (sign-off)

### 5.2 Domain (must for vertical demo)

- [ ] Shared TBox module (exportable)
- [ ] ≥1 multi-source ABox pack validated without a per-entity OWL file
- [ ] End-to-end promote + identity-bound query returns ranked result + steps + provenance
- [ ] Admin path: fetch → select → validate → materialize → smoke → approve → promote
- [ ] Idle/reset path after fleet in-sync

### 5.3 Beyond parity

Use **§6** (full gap research). Do not claim production SaaS until **P0** gaps are closed.

---

## 6. Gaps, value, and anti-patterns (carry into every new project)

> **Purpose of this section:** When you start a **new** project, copy this section whole.
> It records (1) **honest gaps** vs as-built, (2) **why enterprises pay to close them**, (3) **mistakes we already paid for** — so you do not repeat them.
> **Self-contained:** no need for monorepo `todo.md` on the new machine.

### 6.0 How to read gaps

| Column | Meaning |
|--------|---------|
| **Gap** | Not complete in as-built baseline |
| **As-built today** | What this reference project actually has |
| **Industry why** | Why mature platforms invest |
| **Value if closed** | Outcome for product / risk / sales |
| **Pri** | P0 = real multi-tenant prod · P1 = integration/scale · P2 = quality · P3 = later |

**Rule:** Gaps are mostly **connectors, platform, security, scale** — **not** “missing a new ontology per product.”

---

### 6.1 Identity, security & multi-tenancy

| Gap | As-built today | Industry why | Value if closed | Pri |
|-----|----------------|--------------|-----------------|-----|
| End-user AuthN/Z (OIDC/JWT) | Demo often open; optional admin token header | Named agents; least privilege; audit who promoted | Commercial security; accountability | **P0** |
| Tenant ACL / hard isolation | Logical `tenant_id` / partition keys only | Multi-OEM SaaS must not leak catalogs | Multi-tenant product viability | **P0** |
| Encrypted Bolt + secret vault | Local password defaults in compose | Prod graph always TLS | Compliance path | **P1** |
| Dual-control promote workflow | Session approve + optional token | Change boards | Safer production KG writes | **P1** |

**Cluster value:** Without identity, excellent GraphRAG is still a **demo**. Buyers ask “who can push production knowledge?” first.

**Do not repeat:** Ship open Admin promote on the public internet; call that “enterprise ready.”

---

### 6.2 Enterprise integration & data plane

| Gap | As-built today | Industry why | Value if closed | Pri |
|-----|----------------|--------------|-----------------|-----|
| Live SoR connectors | Fixtures + optional mock HTTP; URL hooks | SoR changes daily | Continuous ABox; no hand packs at scale | **P1** |
| Hand-authored multi-source packs | Valid **demo** pattern | Real ops use APIs/CDC | Architect credibility | **P1** |
| CDC / event bus (sale → asset) | Register-asset API pattern only | Event-driven installed base | Correct product on first call | **P1** |
| Async ETL workers / job queue | Sync work inside API process | Long jobs must not block HTTP | Multi-hour OEM loads | **P1** |
| Postgres (or equiv) ops DB | SQLite for some ops paths | Multi-writer API replicas | Horizontal API scale | **P1** |
| Contract tests vs real APIs | Mock-oriented tests | Schema drift breaks ETL | Safer connector upgrades | **P1** |
| Always-on incremental live path | Incremental pipeline exists; demo-shaped | Deltas after go-live | Cost + freshness | **P1** |

**Cluster value:** Pipeline **shape** is enterprise; default **sources** are still demo. Closing this moves “architecture demo” → “integration platform.”

**Do not repeat:** Claim “live SAP/Salesforce integration” while only JSON fixtures run.

---

### 6.3 Knowledge, ontology & diagnosis quality

| Gap | As-built today | Industry why | Value if closed | Pri |
|-----|----------------|--------------|-----------------|-----|
| External SHACL / OWL reasoner in CI | In-repo shape checks + Turtle export | Formal contracts before promote | Blocks bad ABox in CI | **P2** |
| RDF as SoR / RDF→graph import | Export only | Some OEMs exchange RDF packs | Data-mesh interop | **P2** |
| Closed-loop learning (outcomes → edge weights) | Static likelihoods on edges | Field results should improve rank | Lower wrong-action rate over time | **P2** |
| Spare supersession chains | Basic spare links | BOM revisions | Correct replacement first time | **P2** |
| Rich branching procedure trees | CONFIRMS + limited tree | Manuals branch | Tech trust | **P2** |
| Full NLP NER for unstructured | Regex/heuristics | Manuals are free text | Faster bulletin ingest | **P2** |
| Multi-language content | EN-centric fixtures | Global CSP | Local language match | **P2** |
| Hardcoded product keyword maps | Present for free-text product hit | Brittle vs product master | Prefer asset/CRM/graph identity | **P2** |
| Vector/full-text at catalog scale | In-process hybrid match | Scale beyond demo catalog | Latency + recall | **P3** |

**Not a gap (do not “fix” this):** generating a **new OWL schema per product pack**.
Correct design: **shared TBox + pipeline-built ABox**.

**Do not repeat:** Author only lab-language evidence (“filter LED”) when users say “won’t start”; expand customer-language evidence in packs.

---

### 6.4 Runtime platform, scale & resilience

| Gap | As-built today | Industry why | Value if closed | Pri |
|-----|----------------|--------------|-----------------|-----|
| Redis **required** multi-replica | Code ready; default **memory** if no `REDIS_URL` | Shared rate/cache/admission across pods | Correct multi-pod limits | **P1** |
| Graph HA / read replicas | Dual **single-node** Docker (stage+prod) | Failover + scale reads | Chat uptime SLOs | **P1** |
| Multi-region active-active | Not built | Global latency / DR | Regional compliance | **P3** |
| Load/perf suite at scale | Functional tests | Prove concurrency + pool | Capacity planning | **P1** |
| OTEL default-on | Optional, default off | Distributed tracing | Debug cross-service latency | **P2** |
| Product-level parallel transform chunks | Default single transform batch | Huge catalogs | Throughput without OOM | **P2** |
| Hermetic CI (tests don’t dirty seeds) | Known pitfall; suite can rewrite fixtures | CI must be clean | Reliable release gates | **P1** |

**Already working (do not re-build from zero):** parallel connector extract, schema/subgraph/diagnose caches, rate limit, admission control, connection pool, invalidate-on-promote, lineage partitions, provenance. Prove via `/health` → `runtime`.

**Do not repeat:** Parallelize a single diagnose ranking path “for performance” without evidence — prefer correctness; path queries are already bounded.

---

### 6.5 Ops / UX gaps

| Gap | As-built today | Industry why | Value if closed | Pri |
|-----|----------------|--------------|-----------------|-----|
| Explicit source-pack contract doc | Implicit validators + examples | Stewards need one contract | Fewer broken Fetch/ETL runs | **P1** |
| Always-visible runtime panel | Health has data; not always first-class UI | Ops needs hit rates/workers | Trust platform is on | **P2** |

---

### 6.6 Priority pyramid (new projects)

```text
P0  Identity + tenant isolation          → can sell / can audit
P1  Live connectors + async ETL          → continuous knowledge
P1  Redis multi-pod + graph HA + load    → stays up under traffic
P1  Pack contract + hermetic CI          → delivery quality
P2  Learning loop, SHACL CI, NLP         → accuracy over time
P3  Multi-region, vector indexes         → only when scale forces it
```

---

### 6.7 Anti-patterns we already hit (MUST NOT REPEAT)

Copy this table into every new project’s SDD. These are **paid lessons**.

#### Ontology / knowledge

| Mistake | What went wrong | Correct practice |
|---------|-----------------|------------------|
| Treat every new SKU as “new ontology” | Wasted effort; wrong layer | NEW pack = **ABox individuals** under shared **TBox** |
| Build OWL when adding source files | Schema drift; fake “ontology build” | Pipeline builds **instances**; TBox is governance |
| Validate only after graph load | Bad data already in prod | Shape-check ABox **before** materialize/promote |
| Show full TBox dump as “the change” | Operator confusion | Highlight **NEW ABox** / entity delta |
| Unknown list key silently ignored forever | Missing domain concept | Surface **tbox_extension** candidate; review |

#### Ingest / promote / dual graph

| Mistake | What went wrong | Correct practice |
|---------|-----------------|------------------|
| Selection is cosmetic | Promoted entire fleet | Fail-closed; materialize/promote **only** selected IDs |
| Staging success = chat ready | Users see old answers | Chat/explore read **production only** |
| Fleet UPDATE = this batch failed | False alarm after successful promote | Split **fleet** vs **selection/batch** status |
| Diff uses raw PIM after promote | Eternal UPDATE flags | Catalog-authoritative fleet diff where promote writes catalog |
| Bulletin-only metadata forces UPDATE | Noise batch | Require real ABox growth for pending UPDATE |
| Naive index pairing of steps↔FMs | Wrong CONFIRMS edges | Keyword/order repair; validate link tables |
| Drop required shape fields in packs | Fetch/ETL crash | Pack contract: required fields for each entity type |
| Wizard stuck “complete” after idle fleet | Cannot start next work | Session **reset-for-next-cycle** after in-sync |

#### Diagnosis / ranking / UX

| Mistake | What went wrong | Correct practice |
|---------|-----------------|------------------|
| Steps = all orders ≤ N | Wrong steps for top hypothesis | **CONFIRMS(top hypothesis)** (+ limited entry prereqs) |
| Soft mismatch hard-blocks bound asset | User cannot diagnose own appliance | Asset-bound: **warn**, still diagnose bound product |
| Substring product codes in English words | Wrong product family | Word boundaries; careful short tokens |
| Treat 60–70% text match as “not in KG” | False bug reports | Check matched evidence id + posterior; partial lexical is normal |
| Provenance shows neighborhood not ranked path | Weak explainability | Prefer evidence for **ranked** conclusion |
| Explorer path dumps all steps | Noise | Filter to confirming path |

#### Engineering process

| Mistake | What went wrong | Correct practice |
|---------|-----------------|------------------|
| Tests rewrite seed fixtures mid-suite | Flaky CI / dirty tree | Hermetic tests; restore seeds; isolate pack tests |
| Dual promote buttons / unclear target | Wrong env | One promote control with explicit `target_env` |
| Claim capabilities not in code | Buyer distrust | Label simulated; keep gap list honest |
| Depend on another machine’s monorepo docs | Cannot rebuild elsewhere | **This SDD travels alone** |

---

### 6.8 What is **already good** (do not throw away on rewrite)

Carry these **as platform defaults** into new projects — they are as-built value:

1. Dual graph env (stage then prod)
2. Selection-scoped promote + human smoke/approve
3. Parallel extract / serial transform
4. TTL caches + invalidate on publish
5. Rate limit + admission control
6. Lineage + admin audit
7. Shared TBox + ABox-from-pipeline
8. Asset/identity-first online path when CRM exists
9. Fail-closed empty selection
10. CI pack-under-TBox tests

---

### 6.9 New-project kickoff checklist (gaps-aware)

On day 0 of a **new** project:

- [ ] Copy **§6** into `docs/sdd/08-GAPS-AND-ANTI-PATTERNS.md`
- [ ] Mark which P0/P1 gaps are **in scope for v1** vs deferred
- [ ] Add “anti-pattern of the week” review for first 4 sprints
- [ ] Never mark P0 auth as “later” if external users will hit the API
- [ ] Never invent per-entity OWL in sprint 1 “to look complete”

---

## 7. Implementation order on a blank machine

| Phase | Build | Exit proof |
|-------|--------|------------|
| **P0** | Compose dual graph + API Dockerfile + `/health` | Health green |
| **P1** | Domain TBox module + shape validator | Validate one empty-safe golden pack |
| **P2** | Connectors or fixtures + materialize + promote | Nodes in **production** graph |
| **P3** | Online query + ranking + provenance | Golden phrase test |
| **P4** | Admin control plane + selection + smoke/approve | Wizard E2E |
| **P5** | Runtime: parallel, caches, rate, admission, lineage | Health.runtime populated |
| **P6** | UI personas | Manual smoke |
| **P7** | CI workflows + pack contract tests | PR green |
| **P8** | Second multi-source pack + session reset | Fleet story works |
| **P9** | Production hardening — **§6 P0/P1 gaps only as scoped** | Beyond demo |

**Before P0:** paste **§6** into the new repo and mark which gaps are in-scope for v1.

---

## 8. Suggested greenfield repo tree (portable)

Names can change; **capabilities** must map 1:1.

```text
project/
├── docker/
│   ├── docker-compose.infra.yaml    # graph-prod, graph-stage, redis
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   └── Dockerfile.mock              # optional
├── config/settings.py               # 12-factor; dual graph URIs; cache/etl knobs
├── api/                             # FastAPI (or equivalent) + /health + /admin
├── graph/ or knowledge/             # TBox export, builder, populate, connectors
├── runtime/                         # cache, parallel_map, admission, partition, redis
├── guardrails/                      # rate limit, input/output
├── services/                        # online query orchestration
├── frontend/                        # chat + admin + explorer
├── data/
│   ├── domain_sources/              # SoR fixtures (domain)
│   ├── pipeline_sources/            # multi-source packs
│   └── lineage/                     # runs + audit
├── tests/
│   ├── test_pack_tbox_abox.py       # packs under shared TBox (no per-entity schema)
│   └── ...
├── evals/                           # golden + safety
├── .github/workflows/ci.yml
├── docs/sdd/00–08                   # includes 08-GAPS-AND-ANTI-PATTERNS from §6
├── Makefile
└── .env.example
```

---

## 9. Optional: as-built map (only if this repo is open)

If you **do** have the WarrantyGraph checkout, these paths match §1 (convenience only).
**Fresh builds must not require these paths.**

| Concern | Path |
|---------|------|
| Settings | `config/settings.py` |
| Infra compose | `docker/docker-compose.infra.yaml` |
| Pipeline registry/runner | `graph/enterprise_pipeline/control_plane/` |
| ABox builder | `graph/enterprise_pipeline/transformers/ontology_builder.py` |
| Shape validate | `graph/enterprise_pipeline/ontology_validate.py` |
| Knowledge ETL | `graph/enterprise_pipeline/pipelines/knowledge_etl.py` |
| Graph load | `graph/populate_graph.py` |
| Dual Neo4j | `graph/neo4j_client.py` |
| Diagnose | `services/diagnosis_service.py`, `graph/graph_rag.py` |
| Runtime | `runtime/*` |
| CI multi-source tests | `tests/test_multi_source_tbox_abox.py` |
| CI workflow | `.github/workflows/ci.yml` |
| Duplicate gap tables (optional) | `todo.md` §26 — **§6 of this SDD is the portable source** |

---

## 10. Decision record

| Question | Answer |
|----------|--------|
| Keep SDD collateral? | **Yes** — versioned, updated when **code** changes |
| Platform vs domain? | **Hard split** |
| Docker default? | **Yes** |
| Self-contained for new machine? | **Yes — this document alone + empty repo** |
| Code is truth? | **Yes — §1 as-built; §6 gaps/anti-patterns** |
| Ontology on source add? | **ABox via pipeline only; shared TBox** |
| Include gaps in SDD? | **Yes — §6 travels with every greenfield** so mistakes are not repeated |
| Agent / lost-in-middle? | **Thin always-on files** (AGENTS/NEVER/MUST/OVERRIDES/PHASES); full doc is human reference only |
| New project nuances? | **OVERRIDES.md wins** when explicit; silent drift forbidden |

---

## 11. Maintenance rule

Whenever you change:

- compose ports / services
- pipeline IDs
- promote rules
- cache/parallel defaults
- CI gates
- **new production gaps or paid lessons**

→ **Update §1 and/or §6 of this SDD in the same PR as the code.**
→ Also update the **thin always-on** files if a NEVER/MUST rule changed (`NEVER.md`, `MUST.md`).

If the SDD drifts, re-generate §1 from settings, registry, compose, and CI. Append new anti-patterns to **§6.7** (and `NEVER.md`) the same week you hit them.

For agent sessions: if a constraint mattered enough to fix a bug, it belongs in **`NEVER.md` or `MUST.md`**, not only in a long paragraph of `REFERENCE-FULL.md`.

---

*Baseline: WarrantyGraph as-built 2026-07-11. Portable for greenfield Docker projects without local monorepo references. §6 gaps/anti-patterns + §0.4 agent packaging for Claude Code/Codex.*
