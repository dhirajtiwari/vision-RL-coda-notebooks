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
| **Core loop** | Customer/asset bind → free text → graph evidence → ranked diagnosis → parts/steps → claim/escalate | Same shape |
| **Truth store** | Neo4j property graph | Graph or equivalent multi-hop store |
| **LLM role** | Optional phrasing only; **off by default** | Prefer same unless domain needs generative planning |
| **Demo vs prod** | Demo that behaves like production (fixtures + mock enterprise) | Same: honest simulation labels |

### Ports / entrypoints (as built)

| Service | Port / command |
|---------|----------------|
| Next.js UI | `:3000` — `frontend/` (`next dev --webpack`) |
| FastAPI | `:8080` — `uvicorn api.main:app` |
| Neo4j **production** | Bolt `:7687` (Browser `:7474`) — diagnose + explorer read path |
| Neo4j **staging** | Bolt `:7688` (Browser `:7475`) — promote-first MERGE target |
| Mock enterprise | `:8090` — `simulation.mock_enterprise_apps` (optional; fixtures used if down) |
| Redis | `:6379` — `REDIS_URL` (diagnose cache, rate limit, admission) |
| Infra compose | `docker/docker-compose.infra.yaml` — prod Neo4j + staging Neo4j + Redis |
| Stack helper | `./restart-all.sh` — infra + API + UI env wiring |
| ETL / KG control plane | Admin UI + `/admin/kg-pipelines/*` + `python -m graph.enterprise_pipeline.orchestrator` |
| RDF/OWL export CLI | `python -m graph.rdf_ontology_export` |

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

### 2.4 Formal export RDF/OWL `[x]` + interactive definitions `[x]`

- [x] Turtle schema + instances (`graph/rdf_ontology_export.py`)
- [x] RDF/XML OWL sample
- [x] Artifacts under `docs/ontology/` (`warranty-diagnosis-schema.ttl`, `.ttl`, `.owl`)
- [x] CLI: `python -m graph.rdf_ontology_export` (`--schema-only`, `--product-id`, formats)
- [x] **W3C purpose alignment (in code + UI copy):**
  - RDF 1.1 = triple data model (ABox facts)
  - RDFS = labels / domain / range
  - OWL 2 = formal TBox classes & properties
  - Neo4j = runtime knowledge graph for GraphRAG (not an OWL reasoner)
- [x] **API:** `GET /graph/rdf/schema`, `/graph/rdf/product/{id}`, `/graph/rdf/entity?label=&entity_id=`
- [x] **Helpers:** `class_definition_ttl`, `entity_instance_ttl`, `describe_entity_rdf`, `product_full_turtle`
- [x] **Explorer:** node click → OWL class + RDF instance Turtle; full product `.ttl` modal; copy
- [ ] Full OWL reasoner / SHACL validation pipeline — **not** built
- [ ] RDF as system-of-record / RDF→Neo4j import — **not** built

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

### 5.5 Multi-source control plane (structured / semi / unstructured) `[x]`

- [x] Architecture: `docs/20-Enterprise-KG-Ingestion-Pipeline-Architecture.md`
- [x] **Step-by-step runbook:** `docs/21-KG-Ingestion-Step-by-Step-Runbook.md`
- [x] **Dedicated todo:** `docs/todo-kg-ingestion-pipelines.md`
- [x] Pipeline registry: structured, semi, unstructured, preprocess, materialize, smoke, promote, bootstrap_all, incremental_sync
- [x] Run modes: bootstrap | incremental | on_demand
- [x] Extractors + preprocess quality gate
- [x] Fixture packs under `data/pipeline_sources/` (bootstrap + incremental semi/unstructured)
- [x] Staging artifacts under `data/pipeline_staging/`
- [x] API: `/admin/kg-pipelines/*` (list, run, runs, artifacts, sources inventory/preview)
- [x] UI: Knowledge Pipeline Control Room (Admin tab) + tooltips + pre-run source inventory
- [x] Tests: `tests/test_kg_ingestion_pipelines.py`
- [x] Run history store under `data/lineage/pipeline_runs/`
- [x] Dry-run bootstrap does not fail when Neo4j smoke is skipped

### 5.6 Dual Neo4j + promote target env `[x]`

- [x] Settings: `neo4j_uri` (prod), `neo4j_staging_uri` (default `:7688`), optional staging password
- [x] `graph/neo4j_client.py`: dual drivers, `neo4j_env("staging"|"production")` contextvar, `neo4j_health()`
- [x] Promote MERGE into **staging first** then production (`target_env` on `promote_graph`)
- [x] `docker/docker-compose.infra.yaml`: neo4j + neo4j-staging + redis
- [x] `restart-all.sh` exports `NEO4J_STAGING_URI`, starts staging container
- [x] `/health` exposes `neo4j_detail` (prod + staging + `same_as_production`)
- [x] Tests: `tests/test_staging_and_diagnose_cache.py`

### 5.7 Product ops & warranty registration APIs `[x]`

- [x] `graph/enterprise_pipeline/product_ops.py`
  - [x] `bulk_upsert_products` — catalog merge + optional Neo4j promote (staging/prod)
  - [x] `register_warranty_asset` — CRM fixture + Neo4j `Asset-[:INSTANCE_OF]->Product`
- [x] `POST /admin/products/bulk-upsert`
- [x] `POST /admin/warranty/register-asset`
- [x] Cache invalidation after promote/register

### 5.8 Guided onboard + audit + entity delta (2026-07-11) `[x]`

- [x] Selection-scoped materialize/promote (fail-closed empty selection)
- [x] Ingest plan: NEW / pending UPDATE / in sync + recommended actions
- [x] Durable admin audit JSONL + `/admin/audit/history`
- [x] Entity-level ABox delta + Neo4j verify (staging + production)
- [x] RDF NEW-only highlight + ontology map (TBox unchanged vs ABox growth)
- [x] Catalog-authoritative fleet diff (PIM must not re-flag promoted products)
- [x] `repair_confirms_links` for DiagnosticStep CONFIRMS integrity
- [x] See §22.20–22.27, §23 pitfalls, §5.9 glossary

### 5.9 Gaps for production rebuild

- [ ] Real SAP/Salesforce/Guidewire connectors (pattern ready; mock by default)
- [ ] Async job queue / worker for long ETL (Airflow/Dagster/Prefect wire-up)
- [ ] Multi-region Neo4j HA / read replicas
- [ ] Automated approval workflow beyond admin token
- [ ] Continuous learning: closed claims → refresh INDICATES weights
- [ ] Full LLM/NLP NER for unstructured (hook ready; rule extractor today)
- [ ] Live CDC / event bus (POS “warranty sold” → auto-register) — API pattern only
- [ ] pyshacl / external OWL reasoner in CI before promote
- [ ] Pre-push suite must not dirty tracked catalog/staging fixtures

---

## 6. Online diagnosis path (Phase 4)

### 6.1 API surface `[x]`

- [x] `POST /diagnose` — primary path (`force_keep_context` for soft appliance mismatch)
- [x] `GET /products`, `/health` (dual Neo4j + diagnose cache flags), `/metrics`
- [x] `GET /graph/ontology`, `/graph/product/{id}`, `/graph/diagnosis-subgraph` (+ cypher/traversal)
- [x] `GET /graph/rdf/schema`, `/graph/rdf/product/{id}`, `/graph/rdf/entity`
- [x] CRM session APIs: `/crm/customers`, `/crm/customers/{id}/assets`, `/crm/assets/{id}`
- [x] Claims CRUD-ish: list, get, submit, patch status
- [x] Lineage batches, integrations status (expanded platform capabilities)
- [x] Admin pipeline + KG control plane + bulk product + warranty register
- [x] CORS for Next.js, request-id middleware, global 500 handler
- [x] Rate limit on `/diagnose` (tenant-aware key)
- [x] Concurrency admission control for diagnoses
- [x] Pydantic request/response schemas (incl. optional path explain fields)

### 6.2 Service & agent `[x]`

- [x] Shared `services/diagnosis_service.run_full_diagnosis` (warranty gate + diagnose + case handoff)
- [x] Asset-first: when CRM asset bound, product from asset; warranty only on that asset
- [x] Soft mismatch: message vs asset product → **warning when asset-bound** (diagnose continues); force_keep for explicit confirm; hard block only on product_id ≠ asset product (API invariant)
- [x] Do not open escalation cases / cache blocked conflict outcomes incorrectly
- [x] Domain models `DiagnosisOutcome`, `WarrantyDecision`
- [x] LangGraph: detect_product → run_diagnosis → format_response → handle_escalation
- [x] Agent tools wrapping GraphRAG (`agents/tools.py`) + context_blocked / resolution_meta
- [x] Works **without** external LLM

### 6.3 GraphRAG / intelligence `[x]`

- [x] **Asset-first product resolution** (`resolve_product_for_diagnosis`)
  - [x] Identified session: product from CRM/asset (never free-text override)
  - [x] Anonymous session: product pick or message detect
  - [x] Soft appliance mismatch (`soft_appliance_mismatch`) vs hard API invariant (`product_asset_conflict`)
  - [x] **Asset-bound: soft mismatch is warning-only** (bound product remains source of truth)
  - [x] Settings: `strict_context_consistency`, `product_message_signal_min_hits`
- [x] Symptom match (lexical + hybrid TF-IDF)
  - [x] Stricter admission: `symptom_match_min_score` + relative secondary floor (no floor-noise secondaries)
  - [x] Evidence-only Bayes: only FMs with INDICATES `link_count > 0` (no prior-only impeller noise)
  - [x] Word-boundary short codes (no `oe` inside “does”)
- [x] Error code match
- [x] Rank failure modes (Cypher + FMEA + Bayes)
- [x] Diagnostic tree traversal (`diagnostic_engine.py`)
  - [x] **FM-targeted steps**: CONFIRMS(top FM) + order≤1 entry; never other-FM checks
  - [x] Prefer CONFIRMS over linear NEXT_STEP dump
  - [x] `repair_confirms_links` for missing bulletin d05→fm04 style links
- [x] Parts prediction multi-source (`parts_predictor.py`)
- [x] Impacted components, claim precedents, historical resolutions
- [x] Formatted response + provenance trail + graph subgraph
  - [x] Provenance prefers steps with `targets_top_fm`
  - [x] UI: diagnostic steps + historical resolutions cards
- [x] Escalation rules (critical / low conf / weak language / ambiguity)
- [x] **Diagnose read-path cache** (`runtime/diagnose_cache.py`): tenant|product|asset|norm message|catalog version, TTL 90s, bust on promote
- [x] Diagnosis path explain: `cypher_queries` + `traversal` on diagnosis subgraph
  - [x] Explore Exact Path: CONFIRMS-filtered steps + highlighted path edges

### 6.4 Integrations `[x]`

- [x] CRM enrichment (asset → product/SKU/warranty) + list customers/assets for UI
- [x] Fixture CRM under `data/enterprise_sources/crm_assets.json` (enriched sku/model fields)
- [x] Warranty eligibility gate (asset-scoped)
- [x] Claims workflow (JSON + optional Neo4j Claim)
- [x] Case management on escalation (simulated CCaaS); no case on context_blocked soft/hard mismatch

### 6.5 Rebuild checklist — online path

- [ ] Define request DTO (message + optional entity keys)
- [ ] Product/asset binding rules (**prefer asset-first**; message must not silently rebind product)
- [ ] Matching strategy (lexical / hybrid / embeddings)
- [ ] Ranking formula + escalation policy + evidence-only FM candidates
- [ ] Side effects (tickets, claims) behind action guardrails
- [ ] Soft vs hard conflict UX for multi-appliance accounts

---

## 7. Frontend experience `[x]`

### 7.1 Next.js primary UI (`frontend/`)

#### Diagnosis Chat — asset-first `[x]`

- [x] Natural language diagnosis + recommendation strength badge
- [x] 3-tile confidence (posterior / graph / language)
- [x] Ranked failure modes, parts, provenance
- [x] **Pinned composer** (messages scroll; input fixed — no sticky overlap)
- [x] **Customer session:** CRM customer → registered asset cards → product/warranty read-only from asset
- [x] **Anonymous demo:** product type pick only
- [x] Soft appliance mismatch panel: switch asset / keep appliance (`force_keep_context`)
- [x] Context-blocked UI (soft amber vs hard red)
- [x] **Explore Exact Path** → Knowledge Explorer with case path highlighted (+ Cypher/traversal)
- [x] Submit claim from diagnosis; escalation badge

#### Knowledge Explorer — full viewport + explainability `[x]`

- [x] React Flow full-viewport canvas (not fixed 560px box)
- [x] Dagre layout Top→Down / Left→Right; Fit all; zoom/pan; minimap; keyboard (F, +/-, arrows)
- [x] **Full ontology** default (Product, Symptom, FM, Step, Part, Component, ErrorCode, Model, SKU, Asset, WarrantyPolicy, …)
- [x] Persona presets optional (customer/agent/analyst type chips); “Show all”
- [x] Expanded product subgraph API (CONFIRMS, components, codes, assets, policies)
- [x] **Diagnosis path highlight** (glow on-path, dim off-path); race-safe open from chat
- [x] Path only toggle; Clear path
- [x] **Cypher & traversal panel** for the active case (hops + named Cypher plan + params + copy)
- [x] Node inspector: neighbors + **OWL class / RDF instance / combined Turtle** + copy
- [x] Full product OWL/RDF `.ttl` modal
- [x] Search nodes; edge label toggle

#### Admin — Knowledge Base / Control Room `[x]`

- [x] Guided onboarding wizard (sources → fetch/preview delta vs graph → ingest → smoke → approve → promote → customer test)
- [x] Change-preview API: new/updated products vs production Neo4j + journey change log
- [x] Classic staged gate: onboard, dry-run ETL, smoke, human approve, promote
- [x] **Knowledge Pipeline Control Room** (bootstrap, incremental, promote, per-pipeline cards)
- [x] Mode / target env / dry-run; run history; source & staging artifacts
- [x] **Tooltips** with step-by-step “what happens on click” + write paths
- [x] **Pre-run source inventory** (file list, samples, how-to-add, click-to-preview)
- [x] Review state smoke/human flags fixed (true/false)

#### Enterprise Ops — platform dashboard `[x]`

- [x] Dual Neo4j + Redis + diagnose-cache KPIs (not raw JSON only)
- [x] Connector cards with **fixture** mode (expected when `:8090` down)
- [x] Capability chips (built vs gap: OWL import, CDC)
- [x] KG pipeline catalog + recent control-plane runs + ETL lineage
- [x] Runtime cache stats; operate playbook + jump links
- [x] Expanded `/integrations/status` (`utils/connector_status.py`)

#### Agent cases / shared chrome `[x]`

- [x] Agent cases / claims list
- [x] Role switcher Customer / Agent / Analyst
- [x] Dark/light theme; system healthy indicator
- [x] `lib/api.ts` client for backend routes (CRM, RDF, diagnose, claims, …)
- [x] React Query providers

### 7.2 Archived Streamlit UI

- [x] Full enterprise demo UI archived under `ui-streamlit-archive/`
- [x] Cached loaders pattern documented in archive

### 7.3 Rebuild checklist

- [ ] Chat surface for free text **after** identity/asset bind when CRM exists
- [ ] Explainability panel (why this rank?) + path + Cypher
- [ ] Graph explorer for trust-building demos (full ontology + path highlight)
- [ ] Ops views for ETL + runtime health (not raw dumps)
- [ ] Admin control room with pre-run inventory + human gates

---

## 8. Simulation & fixtures `[x]`

- [x] Mock enterprise FastAPI (PIM/CRM/FSM/Claims/Cases) on `:8090`
- [x] Fixture JSON under `data/enterprise_sources/`
- [x] Demo CRM customers/assets for walkthroughs (multi-asset customers e.g. Jane / Robert)
- [x] Pipeline source fixtures `data/pipeline_sources/**`
- [x] Enterprise test scenarios JSON
- [x] Simulated flags in provenance / fixtures
- [x] Fixture fallback labeled in ops/status when mock host unreachable

---

## 9. Runtime platform package (`runtime/`) `[x]`

- [x] `TtlCache` / `RedisTtlCache` + named registry + stats
- [x] **Diagnose read-path cache** `runtime/diagnose_cache.py` (short TTL, catalog-version key, promote bust)
- [x] `parallel_map` bounded thread pool
- [x] `ConcurrencyLimiter` (memory/Redis)
- [x] Partition key helpers (tenant/product/batch) + `batch_items`
- [x] Redis client factory + health (`redis_url` empty → memory)
- [x] Wired: ETL parallel extract, ontology/product caches, rate keys, diagnose admission, post-load invalidate
- [x] Docker compose Redis + infra compose (`docker/docker-compose.infra.yaml`, `docker-compose.redis.yaml`)
- [x] Settings: cache TTLs, diagnose cache flags, workers, pool size, max concurrent diagnoses, tenant id, dual Neo4j, strict context

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
- [x] Docs 20 Enterprise KG ingestion architecture
- [x] Docs 21 KG ingestion step-by-step runbook
- [x] Docs **22 TBox/ABox multi-source onboard mechanism** (sources → ABox; no per-product TBox)
- [x] C4 workspace + diagrams
- [x] Graphviz 01–41 (+ renders tracked for safekeeping)
- [x] Multi-volume PDFs 00–05 (theory, code, RDF, pipelines)
- [x] Full-project encyclopedia PDF
- [x] Interview mastery guide (MD + PDF) with persona Q&A — updated multi-source / TBox-ABox
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
| P1 | Neo4j HA / read replicas | `[ ]` dual env local only |
| P1 | Postgres for ops data | `[ ]` SQLite today |
| P1 | Live CDC / event bus (warranty sold → register-asset) | `[ ]` API exists |
| P2 | OWL reasoner / SHACL validation pipeline | `[ ]` export + UI only |
| P2 | RDF → Neo4j import as alternate SoR | `[ ]` |
| P2 | Claim closed-loop learning into INDICATES | `[ ]` |
| P2 | Part supersession chains (`SUPERSEDES`) | `[ ]` |
| P2 | Richer conditional NEXT_STEP trees | `[~]` basic trees exist |
| P2 | Multi-language manuals at scale | `[ ]` |
| P2 | LLM semantic response cache (if LLM primary) | `[ ]` |
| P2 | Full LLM NER for unstructured extract | `[~]` regex/heuristics |
| P3 | C4 workspace reflect reliability/services/domain | `[ ]` F4 nicety |
| P3 | Graph fabric / multi-DB by OEM | `[ ]` |
| P3 | Full-text / vector indexes if scale demands | `[ ]` |

---

## 20. How to use this document day-to-day

1. **Planning a feature** — find the section, add a checkbox, keep WWWH (What/Where/When/How/Why).
2. **After every feature/change lands** — **update this file the same session** (append or tick boxes). Do not ship code without tracking it here.
3. **Before removing or rewriting UX/logic** — search this file for related `[x]` items so useful behavior is not dropped (path highlight, asset-first, dual Neo4j, RDF, etc.).
4. **Starting a new vertical** — copy §18 playbook + §1 theory + §2 ontology template.
5. **Onboarding engineers** — walk §17 matrix + package encyclopedia (`docs/18`) + **§22 session log**.
6. **Interviews / design reviews** — multi-volume Vol 02 theory + Vol 03 code + this §1–3.
7. **Don’t lie to future you** — keep `[ ]` items honest; demos must stay labeled; fixture vs live called out.

---

## 21. Companion deep dives (do not duplicate here)

| Doc | Use for |
|-----|---------|
| `docs/18-FULL-PROJECT-CODEBASE-ENCYCLOPEDIA.md` | Every package inventory |
| `docs/19-Indexes-…md` | Constraints/indexes WWWH |
| `docs/15`–`17` | Ontology, runtime, landscape |
| `docs/20-Enterprise-KG-Ingestion-Pipeline-Architecture.md` | Multi-source KG control plane architecture |
| `docs/21-KG-Ingestion-Step-by-Step-Runbook.md` | How to run bootstrap / incremental / promote |
| `docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md` | **TBox vs ABox**, multi-source NEW packs, no per-product schema |
| `docs/todo-kg-ingestion-pipelines.md` | KG pipeline checklist detail |
| `docs/multi-volume/*` | Theory + annotated code + RDF PDFs |
| `docs/ontology/*` | Generated Turtle / OWL artifacts |
| `docs/interview/*` | Persona Q&A |
| `docs/PIPELINE-AND-MODULE-GUIDE.md` | Phase 0–5 operational guide |
| `docs/llmops-handbook/*` | LLMOps disciplines depth |
| `README.md` | Quick start |
| `docker/docker-compose.infra.yaml` | Prod Neo4j + staging Neo4j + Redis |
| `restart-all.sh` | Local full stack start |

---

## 22. Session log — recent features (track every addition)

> **Mandate:** Whenever we add/change a feature in WarrantyGraph, **append or update** this section (and the matching § above) **in the same change set**. Prefer WWWH: What / Where / When / How / Why. Mark status `[x]` / `[~]` / `[ ]`. Never delete prior session entries without consolidating into the main sections first.

### 22.1 Dual Neo4j staging + diagnose read cache `[x]`

| | |
|--|--|
| **What** | Production Bolt `:7687` + staging `:7688`; promote target_env; diagnose Redis cache |
| **Where** | `graph/neo4j_client.py`, `config/settings.py`, `runtime/diagnose_cache.py`, `services/diagnosis_service.py`, `docker/docker-compose.infra.yaml`, `restart-all.sh`, control plane `runner.py` promote, `/health` |
| **When** | Before/after catalog promote; every diagnose (optional TTL) |
| **How** | `neo4j_env()` contextvar routes drivers; cache key = hash(tenant, product, asset, norm message, catalog version); invalidate on promote |
| **Why** | Enterprise promote-first + hot-path latency without stale graph after MERGE |
| **Tests** | `tests/test_staging_and_diagnose_cache.py` |

### 22.2 Multi-source KG control plane + Admin Control Room `[x]`

| | |
|--|--|
| **What** | Registry of pipelines (structured/semi/unstructured/preprocess/materialize/smoke/promote/bootstrap/incremental); Admin UI Control Room |
| **Where** | `graph/enterprise_pipeline/control_plane/*`, extractors, preprocess, Admin tab `frontend/app/page.tsx`, `/admin/kg-pipelines/*` |
| **When** | Bootstrap project build, incremental live, on-demand admin |
| **How** | `run_pipeline(id, mode, dry_run, target_env)`; staging JSON artifacts; lineage under `data/lineage/pipeline_runs/` |
| **Why** | Realistic multi-source ingestion with human gates |
| **Tests** | `tests/test_kg_ingestion_pipelines.py` |
| **Docs** | `docs/20`, `docs/21`, `docs/todo-kg-ingestion-pipelines.md` |

### 22.3 Admin tooltips + pre-run source inventory `[x]`

| | |
|--|--|
| **What** | Hover help on every Admin/pipeline action; inventory API parses sources before Run |
| **Where** | `frontend` HelpTip + inventory panel; `GET /admin/kg-pipelines/sources/inventory`, `/preview` |
| **When** | Operator opens Admin; after adding files under `data/pipeline_sources/` |
| **How** | Schema-on-read samples for JSONL/CSV/txt; no pipeline execution required for preview |
| **Why** | Discover → preview → extract → gate → promote (not blind Run) |

### 22.4 Asset-first diagnosis + soft product mismatch `[x]`

| | |
|--|--|
| **What** | Customer → assets → diagnose; product from CRM asset; soft mismatch confirm; hard product≠asset API invariant |
| **Where** | `resolve_product_for_diagnosis`, `diagnosis_service`, diagnose request `force_keep_context`, CRM list APIs, Chat UI session modes |
| **When** | Every customer-facing diagnose; anonymous demo still product-pick |
| **How** | Message must not silently rebind product when asset bound; soft block then force or switch asset |
| **Why** | Production CRM reality; washer text on dishwasher asset is a UX error, not “smart override” |
| **Tests** | `tests/test_product_resolution.py` (fail-closed + soft + force + aligned) |

### 22.5 Evidence-only ranking hygiene `[x]`

| | |
|--|--|
| **What** | Higher symptom min score + relative floor; drop FMs with zero INDICATES from Bayes set |
| **Where** | `graph/graph_rag.py` `match_symptoms`, `rank_failure_modes` / posteriors |
| **Why** | Prevent weak secondary symptoms and prior-only FMs (e.g. impeller @ 10%) from faking differentials |

### 22.6 Product bulk upsert + warranty asset register `[x]`

| | |
|--|--|
| **What** | Bulk catalog product add/update; register customer warranty unit |
| **Where** | `graph/enterprise_pipeline/product_ops.py`; `POST /admin/products/bulk-upsert`; `POST /admin/warranty/register-asset` |
| **How** | Catalog JSON write + optional Neo4j MERGE / Asset INSTANCE_OF; cache invalidate |
| **Why** | Realistic ops without full CDC yet |

### 22.7 Knowledge Explorer overhaul `[x]`

| | |
|--|--|
| **What** | Full-viewport graph; full ontology neighborhood; persona as optional preset; pan/zoom/fit; path highlight restored; OWL/RDF on click; Cypher + traversal for case |
| **Where** | `frontend/app/page.tsx` explorer; `graph/graph_visualization.py` expanded subgraph + `build_diagnosis_cypher_plan` / `build_diagnosis_traversal`; RDF APIs |
| **When** | Browse product; Explore Exact Path from chat; inspect node |
| **How** | Product subgraph v3 includes steps/parts/components/codes/assets/policies; path overlay race-guarded; diagnosis-subgraph returns cypher_queries + traversal |
| **Why** | Trust + audit: see true Neo4j ontology, formal RDF/OWL, and the exact Cypher hops for a case |
| **Must not regress** | Explore Exact Path highlight; full ontology types; RDF inspector; dual-env promote |

### 22.8 Enterprise Ops dashboard refresh `[x]`

| | |
|--|--|
| **What** | Replace raw connector dump with platform KPIs, dual Neo4j, Redis, capabilities, KG runs, lineage, operate playbook |
| **Where** | Enterprise Ops view; `utils/connector_status.integration_status()` |
| **Why** | Ops page must track real architecture (not pre–control-plane UI) |

### 22.9 Chat layout UX `[x]`

| | |
|--|--|
| **What** | Diagnosis chat flex layout: scrollable transcript + pinned composer |
| **Where** | `frontend/app/page.tsx` chat column; `globals.css` `.chat-composer` |
| **Why** | Input no longer sticky-overlaps diagnosis cards |

### 22.10 Tests added/updated (this era) `[x]`

- [x] `tests/test_staging_and_diagnose_cache.py`
- [x] `tests/test_kg_ingestion_pipelines.py`
- [x] `tests/test_product_resolution.py` (asset-first / soft mismatch / force)
- [x] Staging cache mock accepts `crm_product_id` / `force_keep_context`

### 22.11 Standing process for future changes

```text
1. Reason: which existing [x] features must remain (path, asset-first, dual Neo4j, RDF, cache, …)?
2. Implement without silent removal of those behaviors.
3. Update matching § in this todo.md (and append a 22.x entry if multi-session feature).
4. Note tests + docs + residual gaps honestly.
```

### 22.12 End-to-end new product `ice-001` (multi-source demo) `[x]`

| | |
|--|--|
| **What** | Full walkthrough product **FrostBite Compact Ice Maker 12kg (`ice-001`)** via structured + semi + unstructured sources → catalog/ontology → Neo4j KG → RDF → customer diagnose |
| **Where** | `data/pipeline_sources/**/ice-001*`, `data/enterprise_sources/pim_catalog.json`, semi work_orders/parts, CRM `AST-ICE-2201`, `docs/ontology/ice-001-product.ttl` |
| **Pipeline path** | structured_extract → semi_structured_ingest → unstructured_extract → preprocess → knowledge_materialize → bulk_upsert/promote_graph → register_warranty_asset |
| **KG result** | 4 symptoms, 3 FMs, 3 parts, 4 steps, 6 INDICATES, asset INSTANCE_OF |
| **Diagnose sample** | Asset-bound Jane `AST-ICE-2201`: “not producing ice / E07” → **Water Inlet Valve Failure** (~72% posterior, Strong) |
| **Fixes along the way** | `populate_graph` defaults for SKU revision/model_year, component impact_severity, step/error-code confidence (safe for new product packs) |
| **UI how-to** | See operator runbook in chat response / `docs/21` + Admin Control Room |

### 22.13 Guided Admin product onboarding wizard + change-preview `[x]`

| | |
|--|--|
| **What** | Reorganized Admin so operators can **see new/updated products vs live Neo4j** after fetch, walk steps 1→6 with progress, and keep a **change log** of completed actions before customer persona tests |
| **Where** | `graph/enterprise_pipeline/change_preview.py`; `GET /admin/pipeline/change-preview`; enhanced dry-run / status / review / promote / kg-pipeline run journey; `frontend/app/page.tsx` Admin wizard |
| **When** | Operator opens Admin → Inspect sources → Fetch & show changes → Ingest → Smoke → Approve → Promote → Customer chat test |
| **How** | Diff catalog/PIM/incoming product summaries vs production (and staging) graph; store `change_preview` + `journey` in `ADMIN_REVIEW_STATE`; UI stepper + “What’s coming” panel + collapsible inventory/Control Room |
| **Keeps** | Classic gates, Control Room pipelines, source inventory/preview, tooltips, dual-env promote, dry-run modes, **partitioning** (`product_id_from_record`, ETL/rate-limit partition keys) |
| **Why** | Prior Admin stacked dual panels (classic gate + Control Room) without a clear delta or progress trail — hard to follow for new product onboard |
| **Must not regress** | bootstrap_all / incremental_sync / promote_graph; smoke + human approve gates; inventory previews; partitioning helpers |

### 22.14 Nine new multi-source product test packs + change-set selection `[x]`

| | |
|--|--|
| **What** | **9 brand-new products** as multi-source test artifacts (structured + semi + unstructured + CRM/FSM/claims) **without running pipelines**; Admin **select/deselect** which NEW vs UPDATE products enter promote scope |
| **Product IDs** | `vac-001`, `ac-001`, `oven-001`, `dry-001`, `ref-001`, `grill-001`, `hob-001`, `fan-001`, `pur-001` |
| **Artifacts** | PIM catalog (+9); `structured/new_products_9_pack.json` + notes; semi `new_products_9_parts.csv` / work orders + delta; unstructured manuals+tickets; CRM assets + FSM WOs + 3 claims; `NEW_PRODUCTS_9_MANIFEST.json` |
| **Selection API** | `GET/POST /admin/pipeline/selection` — per product + bulk new/update; defaults **new=on**, **updates=opt-in** |
| **Distinction** | UI: **NEW PRODUCT** (not in live graph) vs **UPDATE EXISTING** (field diffs) |
| **Promote filter** | Selected `product_ids` → `run_staging_promotion` (filter via `product_id_from_record` — partitioning retained) |
| **Pipeline** | Artifacts only — no pipeline run for this pack |

### 22.15 Admin button failures (Load failed) — root cause fix `[x]`

| | |
|--|--|
| **Cause** | 9-product test pack `historical_resolutions` used wrong keys (`summary`/`failure_mode_id`) → Pydantic `HistoricalResolution` validation error → dry-run ETL / bootstrap 500 → browser toast **Load failed** |
| **Fix** | Corrected PIM + structured pack resolution fields; hardened `OntologyBuilder._merge_resolutions` with alias normalize + skip bad rows; claims/FSM missing FM no longer KeyError; frontend `adminFetch` surfaces HTTP/network errors clearly |
| **Verified** | dry-run, validate, approve, bootstrap_all dry-run, selection, inventory all HTTP 200 |

### 22.16 W3C ontology-first gate + Admin last-action UI `[x]`

| | |
|--|--|
| **W3C recommendation (research)** | **TBox first** (OWL 2 / RDFS rule book: classes + properties) → **ABox** product instances as RDF facts → **SHACL-style shapes** for closed-world validation before load → operational graph. OWL = meaning/inference; SHACL = data quality. Sources: [OWL 2 Primer](https://www.w3.org/TR/owl2-primer/), [RDF 1.1](https://www.w3.org/TR/rdf11-concepts/), [SHACL](https://www.w3.org/TR/shacl/) |
| **New product vs ontology (authoritative)** | OWL Primer: ontology has **terminological** knowledge (classes/properties) + **assertional** knowledge (individuals). A new product is almost always **new individuals (ABox)** under the **same domain TBox**. You only extend the ontology when you need new *kinds* of classes/relations. Product packs (pur-001, …) are ABox builds + shape validation — not a new TBox per SKU. |
| **Critical gap (honest)** | Historically this app was **Neo4j property-graph first** with OWL/RDF as **export** after load — not full reasoner + SHACL pipeline. That risked accepting incomplete product packs into diagnosis. |
| **What we added** | `ontology_validate.py`; tbox/validate APIs; dry-run ontology report; Admin preview-first redesign (single Fetch preview panel, workflow bar, collapsible advanced) |
| **Still not full W3C stack** | No external OWL reasoner; no pyshacl; Neo4j remains runtime GraphRAG store |

### 22.17 Admin UX critical redesign — preview-first `[x]`

| | |
|--|--|
| **Problem** | Fetch showed toast only; long redundant wizard + W3C banners + dual control rooms hid the actual change-set |
| **Fix** | One **Fetch preview** card (sources table, NEW vs UPDATE lists, selection, ABox validation); compact workflow 1–7; TBox/ABox one-liner; sources / log / advanced **collapsed** |
| **Copy** | Explicit: new product = ABox under existing TBox; TBox extension only for new entity *types* |

### 22.18 pur-001 insufficient data + Admin “dead” buttons `[x]`

| | |
|--|--|
| **Diagnosis root cause** | CRM asset + Product node existed, but ABox symptoms were “filter light / F02 / intermittent” — user said “not starting” → **no symptom match** → posterior/graph/text 0% / Insufficient data. Pipeline not empty; **evidence mismatch**. Provenance steps still listed as product neighborhood, not ranked FM evidence. |
| **Fix** | Expanded pur-001 ABox (start/power symptoms + Power Supply FM + INDICATES); MERGE production; query phrase rewrite for “not starting”; Admin dry-run default **off**; gate tooltips; Validate ABox works with zero selection (all new) |
| **Lesson** | Onboard completeness = symptoms customers actually say, not only lab FMEA labels |

### 22.19 soft_appliance_mismatch false positive on “purifier does not start” `[x]`

| | |
|--|--|
| **Bug** | Substring match of error code `oe` inside English **“does”** scored LG WM4000; bound `pur-001` had no keywords → soft mismatch + blocked ranking |
| **Fix** | Word-boundary matching for short keywords; remove bare `oe`/`de`; keywords for 9 new products; soft mismatch requires ≥2 hits and clear lead over bound product; name/brand boost from live product list |
| **Tests** | `tests/test_product_resolution.py` still pass |

### 22.24 Ingest plan: extract → detect → recommend next steps `[x]`

| | |
|--|--|
| **What** | Closed-loop **ingest plan** after Fetch: detect `new_product` / `product_update` / `tbox_extension` / `sources_changed`; ordered `recommended_actions`; `wizard_unlocks`; fail-closed `gates.allow_materialize` |
| **Module** | `graph/enterprise_pipeline/ingest_plan.py` |
| **APIs** | `GET /admin/pipeline/plan`; `POST .../plan/lock-selection`; `POST .../plan/acknowledge-tbox`; plan on dry-run, status, validate, materialize |
| **UI** | Admin **Ingest plan** card (next action, checklist, NEW/UPDATE counts, materialize OK, TBox acknowledge) |
| **Policy** | Materialize blocked until selection + ABox validate (+ TBox ack if needed); selection-scoped write/promote |

### 22.23 bootstrap_all “failed” was smoke ENT-001 + selection UI loss `[x]`

| | |
|--|--|
| **Reality** | `knowledge_materialize` for `ac-001` **succeeded**; chain failed only on **smoke_validate** |
| **Smoke root** | ENT-001 expected `expect_escalate=true` but diagnosis now Strong 92% without escalate — scenario updated |
| **UI** | Materialize uses `knowledge_materialize` (not bootstrap_all); locked selection IDs survive refresh; materialize ✓ only when step explicitly completed |
| **API check** | smoke 3/3 pass; materialize `ac-001` success |

### 22.22 Change-preview detects ABox/bulletin growth as UPDATES `[x]`

| | |
|--|--|
| **Bug** | Fetch reported “no new or updated” after OEM bulletins because IDs/names matched; only name-level fields were diffed |
| **Fix** | Compare per-product **symptom/FM/step/component/error_code counts** (source vs live Neo4j) + bulletin_id; flag as UPDATE when source ABox is richer; UI copy for UPDATE opt-in selection |

### 22.21 OEM bulletin 2026-Q3 UPDATE artifacts for existing products `[x]`

| | |
|--|--|
| **What** | ABox **update** pack for all **23** existing products (OEM bulletins + tech resolutions + new symptoms/FMs/parts/steps) |
| **change_type** | `product_update` (not new product onboard) |
| **Sources** | PIM in-place; `structured/oem_bulletins_2026q3_pack.json` + per-pid notes; semi incremental parts/WOs; unstructured incremental bulletins + tech notes; FSM WOs; sample claims |
| **Manifest** | `data/pipeline_sources/OEM_BULLETINS_2026Q3_MANIFEST.json` |
| **Pipeline** | **Not run** — operator uses Admin selection → materialize/promote |

### 22.20 Selection-enforced materialize + strict 1-by-1 Admin wizard `[x]`

| | |
|--|--|
| **Bug** | Admin selection was cosmetic for bootstrap/materialize/promote_graph — ETL rewrote **full** PIM catalog and promoted all products; dry-run + unlocked steps looked “stuck/silent” |
| **Backend** | `run_knowledge_etl(product_ids=)` merges **only selected** into existing catalog; `run_pipeline(..., product_ids=)` filters materialize + promote; API fails closed if selection empty on bootstrap/materialize/promote |
| **Frontend** | Strict steps 1→8: only active step expands; next unlocks after completion; Materialize/Promote send `product_ids` query param |
| **Chat** | New products appear as CRM assets after promote of that product_id; diagnose uses asset product_id |

### 22.25 Operator-grade onboard: audit, entity delta, fleet vs batch, promote UX `[x]`

*(Consolidates work previously sketched as 22.21 / 5.9 — authoritative for rebuild.)*

| Area | Built |
|------|--------|
| **Ingest plan** | `ingest_plan.py` + `GET /admin/pipeline/plan`, lock-selection, acknowledge-tbox; wizard unlocks; fail-closed `allow_materialize` |
| **Durable audit** | `utils/admin_audit.py` → `data/lineage/admin_audit.jsonl` (gitignored runtime); `_admin_journey` dual-writes; `GET /admin/audit/history` |
| **Entity delta** | `entity_delta.py` — catalog vs Neo4j per selection; staging+prod presence; **exact** part ids (never `oem-` prefix); neo4j-verify |
| **RDF highlight** | NEW ABox Turtle only; TBox vs ABox callout; ontology map (class → instance IRI → Neo4j rel) |
| **Fleet vs batch** | Catalog wins over PIM for promote-path diff; **Pending UPDATE** / **Already in sync** / **NEW**; batch-complete banner |
| **Promote UX** | One button + target env; success disables; step action locks; Start next product batch |
| **Refresh plan** | Re-diff + recompute checklist + toast (not silent); does **not** re-fetch sources or write Neo4j |
| **Chat** | Renders `diagnostic_steps` + historical resolutions (were API-only) |

### 22.26 Diagnostic steps, CONFIRMS integrity, explorer path accuracy `[x]`

| | |
|--|--|
| **Bug (chat)** | For top FM “Defrost heater”, UI listed ice-maker + evaporator steps (d01–d04). Operators lost trust in “targeted” steps |
| **Root cause A** | `get_diagnostic_steps_for_failure_mode` used `order ≤ max(confirming order)` — linear dump of unrelated FMs |
| **Root cause B** | `resolve_dynamic_steps` walked linear `NEXT_STEP` chains and ignored CONFIRMS targeting |
| **Root cause C** | Many products (all `*-d05` bulletins) had **no** `diagnostic_step_failure_links` → no CONFIRMS for bulletin FM |
| **Root cause D** | Explore Exact Path subgraph loaded first N product steps, not FM-confirming steps |
| **Root cause E** | Soft appliance mismatch **blocked** asset-bound sessions (e.g. RF28 bulletin phrase → false “washer”) |
| **Fix engine** | `diagnostic_engine.py`: CONFIRMS(top FM) + order≤1 entry steps only; never other-FM confirms; CONFIRMS preferred over linear tree |
| **Fix data** | `repair_confirms_links.py` — keyword + order repair of catalog links; replace Neo4j CONFIRMS per product |
| **Fix explorer** | `graph_visualization.py` diagnosis subgraph filters steps by CONFIRMS + highlights path |
| **Fix session** | Asset-bound soft mismatch → **warning**, not hard block (asset is source of truth) |
| **Verified** | Frost → d01+d04 + heater part; bulletin phrase → fm04 + d05 + polarized connector |

### 22.27 Day log — 2026-07-11 (this application session cluster) `[x]`

Chronological capability delivered **today** (Admin onboard through diagnosis accuracy):

1. **Selection-scoped ETL/promote** — fail-closed empty selection; materialize only locked products
2. **OEM bulletin 2026-Q3 ABox packs** — 23 product_updates (not new TBox)
3. **Strict 1–8 wizard** — Sources → Fetch → Select → Validate ABox → Materialize → Smoke → Approve → Promote
4. **Ingest plan** — recommended next actions, gates, TBox-ack path
5. **Durable admin audit** — JSONL + UI panel
6. **Entity delta + Neo4j verify** — catalog/staging/prod matrix; Docker bolt awareness
7. **RDF/OWL NEW-only highlight** — stop showing schema-only dump as “the change”
8. **Fleet vs batch UX** — pending UPDATE is fleet-wide; batch complete is selection-scoped
9. **Single promote path** — staging :7688 then production :7687; Diagnosis Chat = production only
10. **Chat diagnostic steps UI** — render graph steps + past resolutions
11. **CONFIRMS repair + FM-targeted steps** — diagnosis + Explore Exact Path + RDF confirms edges
12. **Pushed branch** — `feature/llmops-for-remote-diagnostics` (`0fce795`, `4e572df`)

### 22.28 Multi-source NEW packs + ontology discipline + Admin idle reset `[x]`

**Date:** 2026-07-11 (continued session)

#### A. Multi-source NEW product packs (ABox sources — not TBox)

| Product | Name | Role |
|---------|------|------|
| **`hmd-001`** | DryZone Compact Dehumidifier 30pt | Full multi-source NEW; promoted + diagnose verified |
| **`esp-001`** | BrewBar Espresso Machine 15bar | Multi-source NEW; operator-promoted; chat verified (“machine is not heating”) |

**Source layout (both packs):**

- Enterprise: `pim_catalog.json`, `fsm_work_orders.json`, `claims_history.json`, `crm_assets.json`
- Pipeline structured / semi-structured / unstructured bootstrap+incremental
- Manifests: `HMD_001_MULTI_SOURCE_MANIFEST.json`, `ESP_001_MULTI_SOURCE_MANIFEST.json`

**Ontology rule (critical):**

- Dropping source files does **not** invent OWL schema.
- **TBox** = shared domain classes in `rdf_ontology_export` + `docs/ontology/*`.
- **ABox** = OntologyBuilder builds instances **in the pipeline** from sources → catalog → validate → promote.
- `scan_tbox_extension_candidates` detects unknown *keys/types*; does **not** auto-extend TBox.
- Authoritative doc: **`docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`**

#### B. Engineering fixes for multi-source fidelity

| Gap | Fix |
|-----|-----|
| Rich PIM keys lost after Pydantic dump | OntologyBuilder re-attaches model/SKU/components/error_codes/CONFIRMS (`_RICH_KEYS`) |
| `ParameterMissing: model_number` on promote | `populate_graph` defaults model_number from name / SKU / model_id |
| CRM assets / claims ignored on selection materialize | Merge CRM+Claims into catalog; selection upsert keeps assets/claims for selected products |
| Fetch re-flagged promoted OEM as UPDATE | Fleet preview: catalog+PIM merge (catalog wins); no bulletin-only UPDATE |
| Toast ≠ plan headline | Toast uses `plan.headline`; stale selection cleared when batch done |
| Drop IN SYNC disabled after Confirm | Button stays enabled; scopes entity-delta product list |
| Idle fleet still shows finished wizard | `POST /admin/pipeline/session/reset-for-next-cycle` + UI “Reset wizard for next plan” / auto-reset after production promote when 0 NEW/UPDATE |

#### C. Diagnosis learning (esp-001)

| Observation | Learning |
|-------------|----------|
| Phrase “machine is not heating” → 67% text match | **Expected** lexical partial match to “will not heat or brew…” |
| Top FM Boiler NTC 75% + step d02 + NTC part + claims/HR | **Correct** — symptom s01 in KG; multi-source ABox live |
| Do not confuse low-ish text % with “not in graph” | Posterior / graph link / STRONG label matter more |
| Entry steps | CONFIRMS(top FM) only; d01 may not show if it targets another FM |

#### D. Current application state (as of this entry)

| Area | State |
|------|--------|
| Fleet vs production | Core ABox largely **in sync** after hmd/esp + 9-pack/bulletin promotes (re-Fetch for live counts) |
| Dual Neo4j | Staging `:7688` + production `:7687` operational |
| Chat | Production graph; asset-first CRM (e.g. AST-ESP001-2200, AST-HMD001-4100) |
| Admin | Selection-scoped materialize/promote; entity delta; audit; idle session reset |
| TBox | Unchanged by NEW packs; shared warranty-diagnosis schema |
| Demo honesty | Fixtures = connector stand-ins; not live SAP; keywords optional for free-text product hit |

### 22.29 Operator pitfalls learned this session (append to §23) `[x]`

- [x] **Sources ≠ ontology build** — sources feed ABox; TBox is shared and governance-gated
- [x] **Hand-shaped multi-source packs** are valid *demo* inputs; real enterprise uses connectors; still validate as ABox under TBox
- [x] **FailureMode Pydantic fields** required (`estimated_repair_time_minutes`, `safety_notes`) or Fetch/ETL crashes
- [x] **Diagnostic steps** use `description` / `expected_outcome` not `instruction` / `expected_result`
- [x] **Fleet UPDATE vs entity-delta IN SYNC** — different comparisons; Drop IN SYNC keeps batch honest
- [x] **Materialize OK false with idle fleet** after complete batch is gate state — reset session for next plan
- [x] **67% text match can still be STRONG diagnosis** if Bayesian + INDICATES align

### 5.10 Guided onboard operator model (glossary) `[x]`

- [x] **Pending UPDATE** = product exists in production, catalog still has more **core ABox** → promote still needed for that product
- [x] **Already in sync** = catalog core ABox matches production (typical post-promote) — **not** “deleted”; stays in Neo4j
- [x] **NEW** = product_id missing from production
- [x] **Refresh plan** = re-diff catalog↔production + recompute checklist (**no** source re-scan, **no** Neo4j write)
- [x] **Fetch** = dry-run ETL / source preview; resets wizard selection gates; **does not undo promotes**
- [x] **This batch** = locked selection only; fleet counts can still show other pending UPDATEs
- [x] **Materialize** = catalog write (selection); **Promote** = MERGE Neo4j target_env
- [x] Selection-scoped materialize/promote only (fail-closed)

---

## 23. Mistakes, pitfalls & anti-patterns (MUST NOT REPEAT)

> These are **authoritative operational lessons** from building and debugging this app. Rebuilds that ignore them will re-ship the same defects.

### 23.1 Ontology / knowledge graph discipline

| Pitfall | Wrong instinct | Correct practice | Sources |
|---------|----------------|------------------|---------|
| Treat every new SKU as “new ontology” | Create new OWL classes per product | New product = **ABox individuals** under shared **TBox** classes | [OWL 2 Primer](https://www.w3.org/TR/owl2-primer/) (TBox vs ABox); [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/) |
| Validate only after Neo4j load | “Graph has nodes ⇒ valid” | Shape-check ABox against TBox **before** materialize/promote | [SHACL](https://www.w3.org/TR/shacl/) (closed-world data quality); OWL ≠ SHACL |
| Confuse PROV export with governance | Turtle export alone | Lineage batches + audit events + batch ids on entities | [PROV-O](https://www.w3.org/TR/prov-o/) |
| Show TBox schema dump as “the delta” | Full OWL file = change | Highlight **NEW ABox triples** + class→instance map | OWL Primer: assertional knowledge |

### 23.2 Ingest / promote / dual graph

| Pitfall | What broke | Correct practice |
|---------|------------|------------------|
| **Selection is cosmetic** | Checked 2 products, promoted all 23 | Fail-closed: empty selection rejected; ETL merge **only** selected IDs into catalog |
| **Staging success = chat ready** | Promote staging, chat unchanged | Diagnosis Chat reads **production** `:7687` only; staging `:7688` is preview |
| **Fleet UPDATE count = this batch failed** | After promote still “15 UPDATE” | Split **fleet pending** vs **selection in sync** |
| **PIM over catalog in diff** | Promoted products still “UPDATE” forever | Promote-path diff: **catalog wins** on id collision |
| **Part id prefix `oem-`** | One product counted 36 parts | Match **exact catalog part_ids** only |
| **bootstrap_all as Materialize** | Smoke failure marked materialize failed | Materialize step = `knowledge_materialize` only; smoke is separate step |
| **Silent admin buttons** | Toast-only / swallowed errors | Always-visible last action; HTTP error body; busy + success disabled states |
| **Refresh plan silent** | Click does nothing visible | Toast + banner + re-diff counts; explain no-op when plan unchanged |
| **Index-pair CONFIRMS naively** | d03↔defrost wrongly | Keyword score then order; replace Neo4j CONFIRMS set, don’t double-link |

### 23.3 Diagnosis / ranking / UX

| Pitfall | What broke | Correct practice | Sources |
|---------|------------|------------------|---------|
| **Steps = all orders ≤ confirming** | Frost FM showed ice + fan checks | CONFIRMS(top FM) + entry-only prerequisites | Graph decision trees: only edges that **confirm** the ranked hypothesis |
| **Linear NEXT_STEP as targeting** | Same wrong step list | Prefer CONFIRMS; tree walk only if it lands on confirming step | — |
| **Missing CONFIRMS for bulletin d05** | Bulletin FM had no confirming step | Repair + require links at ABox validate | Ontology shapes on link tables |
| **Soft mismatch hard-blocks asset** | Bound RF28 + “fridge 22E…” → blocked as washer | Asset-bound: warn, still diagnose bound product | Asset-first CRM sessions |
| **Substring OE in “does”** | purifier → LG washer | Word boundaries; no bare 2-letter OE/DE | — |
| **Lab FMEA symptoms only** | “not starting” → insufficient data | Author customer-language symptoms | Field service / FMEA practice: detection must match customer narrative |
| **Provenance shows neighborhood** | Steps not related to top FM | Provenance prefers `targets_top_fm` steps | Explainability: evidence for **ranked** conclusion |
| **Explore path dumps all steps** | Graph noise | Subgraph filter CONFIRMS + highlight | Cypher path-bounded retrieval |

### 23.4 Scoring & reliability (do not invent)

| Topic | Practice in this app | Authoritative / standard references |
|-------|----------------------|-------------------------------------|
| Bayesian ranking | Naive Bayes over INDICATES likelihoods + occurrence prior; normalize; miss likelihood > 0 | Pearl, *Probabilistic Reasoning* (1988); Russell & Norvig *AIMA* (Bayes nets) |
| RPN / AP | S×O×D retained; Action Priority severity-led | AIAG-VDA FMEA Handbook (2019); SAE J1739; MIL-STD-1629A; Kmenta & Ishii on RPN misuse |
| GraphRAG | Typed multi-hop Cypher from product, not whole-graph scan | Enterprise GraphRAG practice: schema-constrained retrieval before generation |
| Ontology | TBox shared; ABox per product; RDF export optional | W3C OWL 2, RDF 1.1; ISO 14224-style hierarchy **as modeling inspiration** (not full certification claim) |

### 23.5 Engineering / process pitfalls

| Pitfall | Mitigation |
|---------|------------|
| Pre-push pytest mutates catalog/staging fixtures | Restore fixtures after suite; don’t treat dirty tree as test failure of assertions |
| Hook SIM105 / trailing whitespace fails large commits | Fix ruff before push; prefer small commits for data packs |
| Session journey lost on API restart | Durable `admin_audit.jsonl` + pipeline_runs — not memory alone |
| Dual promote buttons | One control-plane promote with `target_env` |
| Completing wizard still shows active actions | Disable primary actions after success; “Change selection” / “Start next batch” explicit |
| **Finished batch + all in sync still “locked green”** | Session **reset-for-next-cycle**; auto after production promote when fleet idle |
| **Drop IN SYNC gray after Confirm** | Keep prune enabled; pass entity-delta product ids |
| **Toast “10 UPDATE” vs UI “0 UPDATE”** | Single source of truth = plan.headline; prune stale selection of already-synced ids |
| **Author new OWL per SKU when adding sources** | Only ABox pack; TBox shared; unknown keys → tbox_extension review |
| **Treat 60–70% text match as failure** | Match strength ≠ missing KG; check posterior + matched symptom id |

### 23.6 Operator test matrix (bulletin push + multi-source NEW)

| Intent | Example product | Phrase | Expect |
|--------|-----------------|--------|--------|
| Baseline (not bulletin) | `oem-sam-rf28` | “Excessive frost in freezer” | fm03 defrost; steps d01+d04; heater part |
| Bulletin ABox | `oem-sam-rf28` | “Samsung fridge 22E after ice room fan bulletin kit” | fm04 polarity; d05; IF-CONN-RF28-B |
| Prior bulletin dry | `dry-001` | “E66 after cold garage install” | Ambient Below Spec; baffle kit |
| Prior bulletin DW | `dw-001` | “beeps won’t start dry cycle after latch kit” | Latch switch drift |
| Multi-source NEW hmd | `hmd-001` / AST-HMD001-4100 | “tank never fills” / “H3 frost” | Frost FM + CONFIRMS steps + HRs |
| Multi-source NEW espresso | `esp-001` / AST-ESP001-2200 | “machine is not heating” | s01 match; Boiler NTC top; d02; NTC part; claims |

---

## 25. Current state snapshot (post multi-source + idle reset)

> **Use this section as the “where are we now?” brief.** Re-run Fetch for live fleet counts.

### 25.1 Product / graph

- [x] Dual Neo4j (staging + production) with selection-scoped promote
- [x] Multi-source NEW packs: **hmd-001**, **esp-001** (+ earlier 9-pack / OEM / bulletins)
- [x] OntologyBuilder preserves rich ABox (model/SKU/CONFIRMS/components/error_codes)
- [x] CRM asset + Claims merge on materialize/promote path
- [x] Espresso diagnose verified on production for customer-language no-heat

### 25.2 Admin control plane

- [x] 1–8 wizard, ingest plan, audit, entity delta, Neo4j verify
- [x] Drop IN SYNC, lock-selection prune, session **reset-for-next-cycle**
- [x] Fleet vs batch / toast alignment

### 25.3 Documentation

- [x] `docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md` — mechanism + next phases A–E
- [x] Interview guide + doc 15/21 pointers updated for TBox/ABox multi-source truth

### 25.4 Honest gaps / next (see docs/22 §9)

- [ ] Phase B: reduce PRODUCT_KEYWORDS dependence; source-pack contract only
- [ ] Phase C: connector/mock HTTP as primary extract vs static JSON edits
- [ ] Phase D: formal TBox ADR when unknown keys appear
- [ ] Phase E: CI tests for pack-vs-TBox + tbox_extension detection

---

## 24. Authoritative sources checklist (validate claims before demo)

Use this list when stakeholders ask “why this design?” — **cite only what we actually implement**.

| Claim we make | Status | Source to cite | Honesty bound |
|---------------|--------|----------------|---------------|
| Diagnosis is Bayesian over graph likelihoods | `[x]` | Pearl; AIMA; our `reliability.py` / graph_rag | Naive Bayes assumption (conditional independence) |
| FMEA-aligned RPN + Action Priority | `[x]` | AIAG-VDA 2019; SAE J1739 | Demo ratings are authored, not live plant data |
| W3C OWL/RDF ontology | `[x]` export + shapes-lite validate | OWL 2 Primer; RDF 1.1 | No external DL reasoner; Neo4j is runtime |
| SHACL-level governance | `[~]` | SHACL TR | In-repo shape checks, not pyshacl CI gate |
| PROV lineage | `[x]` fields + batch JSONL | PROV-O | Demo fixtures labeled simulated |
| ISO 14224 / IEC 81346 | `[~]` modeling inspiration | ISO 14224; IEC 81346 | **Not** certified implementation |
| Graph-native no LLM required | `[x]` | Architecture | LLM optional for phrasing only |
| Staging then production promote | `[x]` | Enterprise change-management pattern | Local Docker dual Neo4j, not full HA |

**Do not claim:** full OWL reasoner in the diagnose path; live SAP/Salesforce; certified ISO 14224; automatic SHACL in CI unless wired.

---

**Legend recap:** `[x]` done in this repo · `[~]` partial/demo · `[ ]` gap / future

*Last expanded: **2026-07-11 continued** — multi-source **hmd-001** / **esp-001**, OntologyBuilder rich ABox + CRM/Claims merge, fleet/selection UX, Drop IN SYNC, session reset-for-next-cycle, docs/22 TBox·ABox mechanism, interview/doc refresh, pitfalls §22.28–22.29 + §25 state. Process: update this file every feature session. Never remove partitioning or dual-Neo4j promote discipline. **Never invent per-product TBox when adding source packs.***
