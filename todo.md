# WarrantyGraph — Complete Feature Blueprint & Rebuild Checklist

> **Purpose of this file:** A single, realistic inventory of **everything built** across all sessions for this application — product features, theory, pipelines, LLMOps, deploy, docs — so you can **rebuild the same class of solution** for another use case (HVAC, medical devices, telecom CPE, fleet, industrial IoT, etc.).
>
> **How to reuse for a new domain:** Keep the *architecture and checkboxes*; replace *appliance warranty* nouns (Product/Symptom/FailureMode/Part/Claim) with your domain entities; re-author blueprints and connectors; keep scoring/runtime/LLMOps patterns unless evidence says otherwise.
>
> **Legend:** `[x]` built in this repo · `[~]` partial / demo-shaped · `[ ]` not built (honest gap / next build)

---

## 0. Solution identity (what we are building)

| Item | This application | New use-case template |
|------|------------------|------------------------|
| **Name** | WarrantyGraph / Remote Diagnostics Graph | ________________ |
| **Problem** | Inconsistent warranty diagnosis, wrong parts, weak explainability | ________________ |
| **User** | Contact-center agent / customer / knowledge admin | ________________ |
| **Core loop** | Free text → product resolve → graph evidence → ranked diagnosis → parts/steps → claim/escalate | Same shape |
| **Truth store** | Neo4j property graph | Graph or equivalent multi-hop store |
| **LLM role** | Optional phrasing only; **off by default** | Prefer same unless domain needs generative planning |
| **Demo vs prod** | Demo that behaves like production (fixtures + mock enterprise) | Same: honest simulation labels |

### Ports / entrypoints (as built)

| Service | Port / command |
|---------|----------------|
| Next.js UI | `:3000` — `frontend/` |
| FastAPI | `:8080` — `uvicorn api.main:app` |
| Neo4j | Bolt `:7687` — `populate_graph.py` |
| Mock enterprise | `:8090` — `simulation.mock_enterprise_apps` |
| Redis (optional) | `:6379` — `REDIS_URL` |
| ETL | `python -m graph.enterprise_pipeline.orchestrator` |

---

## 1. Theory & research foundations (must carry to any rebuild)

Use these as **defensible** design choices, not magic constants.

### 1.1 Reliability engineering — FMEA / FMECA `[x]`

- [x] **Severity (S)** from symptom severity labels (worst-case)
- [x] **Occurrence (O)** from observed field evidence count (claims + resolutions)
- [x] **Detection (D)** from diagnostic-step / error-code coverage
- [x] **RPN = S × O × D** (classic continuity)
- [x] **Action Priority** High/Medium/Low (AIAG-VDA-style; severity-led — avoids ordinal rank-reversal of raw RPN)
- [x] Pure module `graph/reliability.py` (no I/O; unit-testable)
- [x] Standards awareness: MIL-STD-1629A, SAE J1739, AIAG-VDA 2019; Kmenta & Ishii RPN caveat

**Rebuild note:** Map your domain’s “how bad / how often / how detectable” signals onto graph fields.

### 1.2 Bayesian diagnostic inference `[x]`

- [x] Naive Bayes: `P(fm|S) ∝ P(fm) · ∏ P(sᵢ|fm)`, then **normalize** across candidates
- [x] Prior from occurrence rating (`occurrence_prior`)
- [x] Likelihood from graph edge `INDICATES.confidence`
- [x] **Miss likelihood** ≠ 0 (default `0.15`) so one unmatched symptom cannot wipe a candidate
- [x] Only **strong** symptom matches feed Bayes (weak matches UI-only)
- [x] References: Pearl (1988); Russell & Norvig *AIMA*
- [x] Tests: `tests/test_reliability.py`

### 1.3 Confidence presentation `[x]`

- [x] Separate signals: **posterior**, **graph-edge strength**, **language match**
- [x] **Dominance boost** when top FM clearly leads second (ratio threshold)
- [x] **Recommendation strength** labels: Strong / Moderate / Weak / Insufficient data
- [x] Escalation on critical severity, low confidence, weak language, **ambiguity margin** (posterior gap)

### 1.4 Ontology vs knowledge graph vs topology `[x]` (documented)

- [x] **Ontology** = allowed types + relationships (schema / TBox)
- [x] **Knowledge graph** = ontology + instances (Neo4j ABox)
- [x] **Product structure / “topology”** = BOM Component chain **inside** ontology — **not** a separate Topology product
- [x] Industrial alignment: ISO 14224-style hierarchy + failure taxonomy ideas; ISO/IEC 81346 product aspect
- [x] W3C BOT (building topology) explicitly **out of scope** for appliance diagnosis
- [x] Docs: `docs/15`, multi-volume Vol 04

### 1.5 GraphRAG pattern `[x]`

- [x] Retrieve multi-hop **typed** graph evidence, then assemble answer
- [x] Not “vector RAG on PDFs only” as primary path
- [x] Hybrid **lexical + TF-IDF** for free-text → symptom matching (no embedding infra required)
- [x] Cypher path-bounded queries from known product (not whole-graph scan)

### 1.6 Provenance / lineage `[x]`

- [x] W3C **PROV-O**-aligned fields (`source_system`, record id, document URI, batch, simulated)
- [x] ETL batch lineage JSONL (`utils/lineage_store.py`)
- [x] Honest demo labeling (simulated fixtures, not fake live SAP)

### 1.7 LLMOps disciplines (platform) `[x]` / `[~]`

- [x] PromptOps — versioned prompts under `prompts/`
- [x] EvalOps — golden + safety suites + thresholds (`evals/`)
- [x] Guardrails — input/output/action/rate limit
- [x] FinOps — daily budget circuit breaker
- [x] Model gateway — alias → provider, retry/fallback (inactive by default)
- [x] Observability — JSON logs, Prometheus metrics, optional OTEL
- [x] ADR + handbook + runbooks + model card
- [~] Full production OIDC multi-tenant SaaS auth — **not** productized

### 1.8 Systems theory (scale) `[x]`

- [x] TTL caching for stable reads (schema/subgraphs)
- [x] Bounded parallel I/O (connector extract)
- [x] Serial deterministic transform
- [x] Admission control (max concurrent diagnoses)
- [x] Sliding-window rate limit (memory or Redis)
- [x] Logical partition keys (tenant/product/batch)
- [x] Connection pool sizing for Neo4j driver

---

## 2. Domain knowledge model (ontology in Neo4j)

### 2.1 Entity types (node labels) `[x]`

- [x] Product, Model, SKU, Asset
- [x] Symptom, ErrorCode, FailureMode
- [x] DiagnosticStep, Component, Part
- [x] Claim, HistoricalResolution, WarrantyPolicy

### 2.2 Relationship types `[x]`

- [x] HAS_MODEL, HAS_SKU, INSTANCE_OF, BOUND_TO_SKU
- [x] HAS_SYMPTOM, HAS_ERROR_CODE, CAN_HAVE
- [x] INDICATES (confidence), CONFIRMS, RULES_OUT, NEXT_STEP
- [x] IMPACTS_COMPONENT, REALIZED_BY, REQUIRES_PART (qty, probability)
- [x] COMPATIBLE_WITH, CONFIRMED, USED_PART, FOR_PRODUCT, COVERED_BY

### 2.3 Operational chain (business) `[x]`

```text
Asset/Serial → Product/Model/SKU
  → Symptom + ErrorCode
  → FailureMode (diagnosis)
  → DiagnosticStep (troubleshoot)
  → Component (BOM) → Part
  → Claim / HistoricalResolution
```

### 2.4 Formal export RDF/OWL `[x]`

- [x] Turtle schema + instances (`graph/rdf_ontology_export.py`)
- [x] RDF/XML OWL sample
- [x] Artifacts under `docs/ontology/`
- [x] CLI: `python -m graph.rdf_ontology_export`
- [ ] Full OWL reasoner / SHACL validation pipeline — **not** built

### 2.5 Rebuild checklist — redefine for new domain

- [ ] List **entity types** (what can be a node?)
- [ ] List **relationship types** with properties (confidence, probability, order…)
- [ ] Define **identity keys** (unique per type)
- [ ] Define **diagnosis chain** (evidence → hypothesis → action → spare)
- [ ] Map sources of S/O/D-like signals and likelihoods
- [ ] Export RDF optional for governance

---

## 3. Indexes, constraints & lookup performance `[x]`

Doc: `docs/19-Indexes-Constraints-and-Lookup-Performance.md`

### 3.1 Neo4j uniqueness constraints (= unique indexes)

- [x] Created in `populate_graph.create_constraints()` **before** MERGE
- [x] Applied on every graph load / ETL load / staging promote
- [x] UNIQUE on: product_id, symptom_id, failure_mode_id, step_id, part_id, resolution_id, model_id, sku_id, component_id, error_code_id, asset_id, policy_id, claim_id
- [x] Enables `MATCH (p:Product {product_id:$pid})` index seek + safe `MERGE`

### 3.2 SQLite ops indexes

- [x] PRIMARY KEY on case_id / claim_id
- [x] `idx_escalations_status`, `idx_ccaas_status`, `idx_claims_status`
- [x] `utils/persistence.py` → `data/diagnostics.db`

### 3.3 Not built (by design today)

- [ ] Neo4j full-text index on symptom text
- [ ] Vector / embedding index
- [ ] Composite secondary indexes
- [ ] Relationship property indexes on confidence

**Rebuild note:** Always define unique natural keys first; add full-text/vector only if product-scoped text matching does not scale.

---

## 4. Knowledge authoring & catalog (Phase 0–1)

- [x] OEM product blueprints (`graph/oem_product_catalog.py`) — 10 OEM builders
- [x] Legacy demo products `wm-001`, `dw-001`, `mw-001`
- [x] Warranty extensions: model/SKU/BOM/components/error codes/assets/claims (`warranty_catalog_extensions.py`)
- [x] Synthetic catalog generator + authoritative catalog path (`synthetic_data_generator.py`)
- [x] PIM blueprint sync → fixtures (`pim_blueprint_sync.py`)
- [x] Public-doc-pattern data; representative parts (not secret OEM SKUs)
- [x] Provenance manifest defaults (`data/provenance_manifest.json`)
- [~] Multi-language service manual ingestion at scale — **not** full production pipeline
- [ ] LLM-assisted canonical symptom normalization at scale — **gap**

### Rebuild checklist

- [ ] Author 1 “golden product” end-to-end (symptoms, FMs, steps, parts, links)
- [ ] Scale to N products with same schema
- [ ] Tag simulated vs real sources

---

## 5. Enterprise ETL & promotion (Phase 2–3)

### 5.1 Connectors `[x]`

- [x] Abstract `EnterpriseConnector` + `ConnectorResult` (`connectors/base.py`)
- [x] PIM, CRM, FSM, Claims connectors
- [x] HTTP to mock API **or** fixture fallback (`allow_fixture_fallback` / demo mode)
- [x] HTTP helper (`http_client.py`)

### 5.2 Transform `[x]`

- [x] `OntologyBuilder` merges PIM + FSM resolutions + claims into catalog
- [x] Raises INDICATES confidence from field co-occurrence
- [x] Merges historical resolutions
- [x] Attaches provenance + `etl_batch_id`
- [x] Enterprise catalog payload (assets, policies, claims)

### 5.3 Pipelines `[x]`

- [x] **Pipeline 1** `knowledge_etl` — parallel extract (`runtime.parallel_map`), serial transform, write JSON, optional Neo4j
- [x] **Pipeline 2** `smoke_validation` — scenario gate before promote
- [x] **Pipeline 3** `staging_promotion` — `populate_graph` only if smoke passed
- [x] Orchestrator CLI: `python -m graph.enterprise_pipeline.orchestrator`
- [x] Admin API triggers: dry-run, validate, review, promote, onboard, status
- [x] Lineage log `data/lineage/etl_batches.jsonl`
- [x] Cache invalidation after successful Neo4j load

### 5.4 Graph load `[x]`

- [x] Uniqueness constraints
- [x] MERGE all entity types + relationships
- [x] Provenance properties on entities when enabled
- [x] Shared Bolt driver + connection pool (`neo4j_client.py`)

### 5.5 Gaps for production rebuild

- [ ] Real SAP/Salesforce/Guidewire connectors (pattern ready; mock by default)
- [ ] Async job queue / worker for long ETL
- [ ] Multi-region Neo4j HA / read replicas
- [ ] Automated approval workflow beyond admin token
- [ ] Continuous learning: closed claims → refresh INDICATES weights

---

## 6. Online diagnosis path (Phase 4)

### 6.1 API surface `[x]`

- [x] `POST /diagnose` — primary path
- [x] `GET /products`, `/health`, `/metrics`
- [x] `GET /graph/ontology`, `/graph/product/{id}`, `/graph/diagnosis-subgraph`
- [x] Claims CRUD-ish: list, get, submit, patch status
- [x] Lineage batches, integrations status
- [x] Admin pipeline endpoints (optional `X-Admin-Token`)
- [x] CORS for Next.js, request-id middleware, global 500 handler
- [x] Rate limit on `/diagnose` (tenant-aware key)
- [x] Concurrency admission control for diagnoses
- [x] Pydantic request/response schemas

### 6.2 Service & agent `[x]`

- [x] Shared `services/diagnosis_service.run_full_diagnosis` (warranty gate + diagnose + case handoff)
- [x] Domain models `DiagnosisOutcome`, `WarrantyDecision`
- [x] LangGraph: detect_product → run_diagnosis → format_response → handle_escalation
- [x] Agent tools wrapping GraphRAG (`agents/tools.py`)
- [x] Works **without** external LLM

### 6.3 GraphRAG / intelligence `[x]`

- [x] Product resolution (message / product_id / asset conflict handling)
- [x] Symptom match (lexical + hybrid TF-IDF)
- [x] Error code match
- [x] Rank failure modes (Cypher + FMEA + Bayes)
- [x] Diagnostic tree traversal (`diagnostic_engine.py`)
- [x] Parts prediction multi-source (`parts_predictor.py`)
- [x] Impacted components, claim precedents, historical resolutions
- [x] Formatted response + provenance trail + graph subgraph
- [x] Escalation rules (critical / low conf / weak language / ambiguity)

### 6.4 Integrations `[x]`

- [x] CRM enrichment (asset → product/SKU/warranty)
- [x] Warranty eligibility gate
- [x] Claims workflow (JSON + optional Neo4j Claim)
- [x] Case management on escalation (simulated CCaaS)

### 6.5 Rebuild checklist — online path

- [ ] Define request DTO (message + optional entity keys)
- [ ] Product/asset binding rules
- [ ] Matching strategy (lexical / hybrid / embeddings)
- [ ] Ranking formula + escalation policy
- [ ] Side effects (tickets, claims) behind action guardrails

---

## 7. Frontend experience `[x]`

### 7.1 Next.js primary UI (`frontend/`)

- [x] Diagnosis chat (natural language)
- [x] Recommendation strength badge
- [x] 3-tile confidence (posterior / graph / language)
- [x] Ranked failure modes, parts, provenance
- [x] Knowledge Explorer (React Flow, hierarchical layout)
- [x] Diagnosis path highlight on full graph
- [x] Node inspection / keyboard pan / dark-light theme
- [x] Agent cases / claims
- [x] Enterprise ops (lineage, connector status)
- [x] Admin pipeline actions via API client
- [x] `lib/api.ts` client for all backend routes
- [x] React Query providers

### 7.2 Archived Streamlit UI

- [x] Full enterprise demo UI archived under `ui-streamlit-archive/`
- [x] Cached loaders pattern documented in archive

### 7.3 Rebuild checklist

- [ ] Chat surface for free text
- [ ] Explainability panel (why this rank?)
- [ ] Graph explorer for trust-building demos
- [ ] Ops views for ETL health

---

## 8. Simulation & fixtures `[x]`

- [x] Mock enterprise FastAPI (PIM/CRM/FSM/Claims/Cases) on `:8090`
- [x] Fixture JSON under `data/enterprise_sources/`
- [x] Demo CRM customers/assets for walkthroughs
- [x] Enterprise test scenarios JSON
- [x] Simulated flags in provenance / fixtures

---

## 9. Runtime platform package (`runtime/`) `[x]`

- [x] `TtlCache` / `RedisTtlCache` + named registry + stats
- [x] `parallel_map` bounded thread pool
- [x] `ConcurrencyLimiter` (memory/Redis)
- [x] Partition key helpers (tenant/product/batch) + `batch_items`
- [x] Redis client factory + health (`redis_url` empty → memory)
- [x] Wired: ETL parallel extract, ontology/product caches, rate keys, diagnose admission, post-load invalidate
- [x] Docker compose for Redis (`docker/docker-compose.redis.yaml`)
- [x] Settings: cache TTLs, workers, pool size, max concurrent diagnoses, tenant id

---

## 10. Guardrails, FinOps, Gateway, Observability `[x]`

### Guardrails

- [x] Input: sanitize, injection/jailbreak blocks
- [x] Output: max length, PII redaction
- [x] Action allowlist / HITL hooks
- [x] Rate limiter (memory or Redis Lua sliding window)

### FinOps

- [x] Daily LLM budget ceiling + circuit breaker
- [x] Redis-backed option for multi-replica

### Gateway (optional LLM)

- [x] Model registry YAML aliases → pinned models
- [x] Providers: OpenAI, Azure Foundry adapters
- [x] Retry + ordered fallback
- [x] Meter tokens/cost; budget check before call
- [x] **Default disabled** (`LLM_ENABLED=false`)

### Observability

- [x] Structured JSON logging + request_id
- [x] Prometheus metrics (`/metrics`)
- [x] Optional OpenTelemetry tracing
- [x] PII redaction for logs/telemetry
- [x] Monitoring alerts, Grafana dashboard, SLO rules, OTEL collector configs
- [x] Runbooks: cost, latency, PII, injection, provider outage, quality, RAG stale

---

## 11. Security & governance `[x]` / `[~]` / `[ ]`

- [x] Threat model document
- [x] OWASP LLM mapping
- [x] Data classification / retention / DPIA notes
- [x] System model card
- [x] Admin token for pipeline mutations (optional)
- [x] Fail-fast default Neo4j password outside demo_mode
- [x] Input validation on diagnose/claims
- [~] Demo open without end-user OIDC — **residual**
- [ ] Production SSO/OIDC/JWT tenant isolation — **gap**
- [ ] Encrypted Bolt + cert management as default demo — **partial**

---

## 12. Persistence & ops data `[x]`

- [x] SQLite OperationalStore (escalations, CCaaS cases, claims)
- [x] Escalation store API
- [x] Lineage batch store
- [x] Diagnosis display helpers (executive formatting, mermaid journeys)
- [x] Connector status aggregation
- [~] JSON file fallbacks for some paths (demo convenience)
- [ ] Postgres multi-writer ops DB — **gap**

---

## 13. Deploy, CI/CD, infra `[x]` / `[~]`

- [x] Dockerfiles: api, etl, frontend, mock, ui
- [x] Compose: observability, redis
- [x] K8s base: API, UI, mock, Neo4j StatefulSet, ETL CronJob, ingress, PVC, configmap
- [x] Overlays staging / prod
- [x] Progressive delivery manifests (Argo Rollouts, Flagger canary)
- [x] Image verify policy sample
- [x] Terraform module placeholders/README
- [x] GitHub Actions: CI, CD, nightly eval
- [x] Pre-commit (ruff, large-file check, etc.) + pre-push pytest
- [~] Multi-region active-active — extension point only
- [ ] Full greenfield cloud landing zone — out of scope of demo

---

## 14. Testing & quality gates `[x]`

- [x] Reliability pure unit tests
- [x] Symptom retrieval / hybrid scoring tests
- [x] Product resolution conflict tests
- [x] Warranty ontology / BOM chain tests
- [x] OEM catalog tests
- [x] Guardrails + rate limit tests
- [x] Observability + budget + registry tests
- [x] Persistence tests
- [x] Pipeline integration (fixture ETL)
- [x] Enterprise scenarios suite
- [x] Graph visualization tests
- [x] Runtime + Redis mock tests
- [x] RDF export tests
- [x] API smoke + admin token tests
- [x] E2E diagnosis flow (Neo4j optional skip)
- [x] Services / diagnosis evaluation harnesses
- [x] Eval gate script + golden + safety injection + thresholds
- [ ] Load/perf test suite at scale — **gap**
- [ ] Contract tests against real enterprise APIs — **gap** (mock only)

---

## 15. Documentation corpus `[x]`

### Architecture & product

- [x] README quick start + stack
- [x] PIPELINE-AND-MODULE-GUIDE (phases 0–5)
- [x] Docs 01–14 (docx series: architecture, GraphRAG, Cypher, roadmaps, demos…)
- [x] Docs 15 ontology/RDF/topology decision
- [x] Docs 16 enterprise runtime capabilities
- [x] Docs 17 landscape + pipeline + topology diagrams + code wiring
- [x] Docs 18 full codebase encyclopedia
- [x] Docs 19 indexes & constraints WWWH
- [x] C4 workspace + diagrams
- [x] Graphviz 01–41 (+ renders tracked for safekeeping)
- [x] Multi-volume PDFs 00–05 (theory, code, RDF, pipelines)
- [x] Full-project encyclopedia PDF
- [x] Interview mastery guide (MD + PDF) with persona Q&A
- [x] LLMOps handbook 00–21 + playbook + ADRs
- [x] Governance, model card, runbooks, security docs

### Rebuild note

For a new vertical, clone this **doc skeleton**: encyclopedia + WWWH indexes doc + multi-volume theory/code + runbooks + threat model.

---

## 16. Historical hardening phases (original plan — all critical done)

These remain for history; they are part of the product.

### Phase A — Reliability engine (CLIENT-CRITICAL) `[x]`

- [x] A1–A6 reliability module, wire-in, confidence rewrite, parts grounding, tests, UI surface

### Phase B — Provenance honesty `[x]`

- [x] B1–B2 simulated labeling + PROV-O fields

### Phase C — Single source of truth `[x]`

- [x] C1–C3 catalog authority + import cycle break

### Phase D — Domain + service layer `[x]`

- [x] D1–D2 models + shared diagnosis service

### Phase E — Security/robustness `[x]`

- [x] E1–E3 password guard, validation, driver lifespan

### Phase F — Diagrams/docs `[x]` / `[ ]`

- [x] F1–F3 reliability diagrams + pipeline guide
- [ ] F4 Reflect reliability/services/domain in C4 `workspace.dsl` + diagram 23 *(nicety)*

### Phase G — Verification `[x]`

- [x] G1 suite green / imports / UI path verified (at time of phase)

---

## 17. Feature matrix by package (do not miss)

| Package / area | Features built |
|----------------|----------------|
| **api/** | Diagnose, graph, claims, lineage, integrations, admin pipelines, health/metrics, middleware |
| **services/** | Single diagnosis orchestration |
| **agents/** | LangGraph workflow + tools |
| **graph/** | GraphRAG, reliability, trees, parts, hybrid match, viz, lineage profile, provenance, OEM catalog, extensions, synthetic gen, RDF export, populate, neo4j client |
| **enterprise_pipeline/** | Connectors, OntologyBuilder, sync, ETL, smoke, promote, orchestrator |
| **integrations/** | CRM, warranty, claims, cases |
| **simulation/** | Mock enterprise API |
| **domain/** | Typed outcomes |
| **config/** | Full settings surface |
| **runtime/** | Cache, Redis, concurrency, partitions, admission |
| **guardrails/** | Input/output/action/rate |
| **observability/** | Log/metric/trace/redact |
| **gateway/** + **models/** + **promptops/** | Optional LLM path |
| **finops/** | Budget breaker |
| **utils/** | SQLite, escalation, lineage, display, status |
| **frontend/** | Full agent + explorer + ops UI |
| **evals/** + **tests/** | Gates + broad coverage |
| **docker/k8s/deploy/monitoring/security** | Prod-shaped delivery |
| **docs/** | Architecture through multi-volume + interview |

---

## 18. “Rebuild for another use case” playbook

Copy this section into a new repo’s `todo.md` and re-check boxes as you implement.

### Step 0 — Scope

- [ ] Name the vertical and primary user
- [ ] Define success metrics (accuracy, MTTR, wrong-part rate, auditability)
- [ ] Decide LLM posture (off by default recommended)

### Step 1 — Theory binding

- [ ] Choose ranking theory (FMEA+Bayes or domain equivalent)
- [ ] Define evidence sources for priors/likelihoods
- [ ] Define escalation / human-in-the-loop policy

### Step 2 — Ontology

- [ ] Entities + relationships + unique keys
- [ ] Blueprint one golden product
- [ ] Optional RDF export contract

### Step 3 — Knowledge platform

- [ ] Connectors (or fixtures)
- [ ] ETL transform + lineage
- [ ] Smoke scenarios
- [ ] Graph load with constraints
- [ ] Indexes/constraints on day one

### Step 4 — Online path

- [ ] API diagnose endpoint
- [ ] Matching + ranking + trees + parts
- [ ] Shared service layer
- [ ] Optional agent workflow graph

### Step 5 — Experience

- [ ] Chat + explainability + graph explorer
- [ ] Ops/admin for knowledge promote

### Step 6 — Platform

- [ ] Guardrails, rate limit, admission control
- [ ] Observability + runbooks
- [ ] Eval gate + golden/safety sets
- [ ] Optional Redis for multi-replica
- [ ] Optional model gateway

### Step 7 — Delivery

- [ ] Docker + k8s (or target platform)
- [ ] CI/CD + progressive delivery hooks
- [ ] Threat model + data governance notes

### Step 8 — Honesty

- [ ] Label simulated data
- [ ] Document residual risks (auth, HA, live connectors)

---

## 19. Open / next work (realistic, not vapor)

Use this as the **true backlog** if continuing this product:

| Priority | Item | Status |
|----------|------|--------|
| P0 | End-user AuthN/Z (OIDC/JWT) + real tenant ACL | `[ ]` |
| P0 | Enforce approval gate on promote in all envs | `[~]` admin token only |
| P1 | Real enterprise connectors (not mock) | `[ ]` pattern only |
| P1 | Async ETL workers / job queue | `[ ]` |
| P1 | Neo4j HA / read replicas | `[ ]` |
| P1 | Postgres for ops data | `[ ]` SQLite today |
| P2 | Claim closed-loop learning into INDICATES | `[ ]` |
| P2 | Part supersession chains (`SUPERSEDES`) | `[ ]` |
| P2 | Richer conditional NEXT_STEP trees | `[~]` basic trees exist |
| P2 | Multi-language manuals at scale | `[ ]` |
| P2 | LLM semantic response cache (if LLM primary) | `[ ]` |
| P3 | C4 workspace reflect reliability/services/domain | `[ ]` F4 nicety |
| P3 | Graph fabric / multi-DB by OEM | `[ ]` |
| P3 | Full-text / vector indexes if scale demands | `[ ]` |

---

## 20. How to use this document day-to-day

1. **Planning a feature** — find the section, add a checkbox, keep WWWH (What/Where/When/How/Why).
2. **Starting a new vertical** — copy §18 playbook + §1 theory + §2 ontology template.
3. **Onboarding engineers** — walk §17 matrix + package encyclopedia (`docs/18`).
4. **Interviews / design reviews** — multi-volume Vol 02 theory + Vol 03 code + this §1–3.
5. **Don’t lie to future you** — keep `[ ]` items honest; demos must stay labeled.

---

## 21. Companion deep dives (do not duplicate here)

| Doc | Use for |
|-----|---------|
| `docs/18-FULL-PROJECT-CODEBASE-ENCYCLOPEDIA.md` | Every package inventory |
| `docs/19-Indexes-…md` | Constraints/indexes WWWH |
| `docs/15`–`17` | Ontology, runtime, landscape |
| `docs/multi-volume/*` | Theory + annotated code + RDF PDFs |
| `docs/interview/*` | Persona Q&A |
| `docs/PIPELINE-AND-MODULE-GUIDE.md` | Phase 0–5 operational guide |
| `docs/llmops-handbook/*` | LLMOps disciplines depth |
| `README.md` | Quick start |

---

**Legend recap:** `[x]` done in this repo · `[~]` partial/demo · `[ ]` gap / future

*Last expanded to cover all major building sessions: graph core, warranty ontology, ETL, GraphRAG/reliability, Next.js UI, LLMOps, runtime/Redis, RDF export, multi-volume docs, indexes, and residual production gaps.*
