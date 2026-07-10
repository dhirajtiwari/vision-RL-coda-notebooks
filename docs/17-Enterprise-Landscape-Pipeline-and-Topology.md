# Enterprise Landscape: Complete Pipeline, Network Topology & Graph Traversal

**Purpose:** One place to see how the **whole system is connected as built**, how it sits on a **network**, and how **ETL → staging → Neo4j** enables **fast multi-hop diagnosis**.
**Diagrams (Graphviz):** `39`, `40`, `41` under `docs/graphviz/` · PNG/SVG after `bash docs/graphviz/render_all.sh`.

| Diagram | File | What it answers |
|---------|------|-----------------|
| **39** Complete pipeline | `39-complete-enterprise-system-pipeline.dot` | End-to-end: sources → ETL → gates → graph → API/UI → claims |
| **40** Network topology | `40-enterprise-network-topology.dot` | Ports, tiers, ingress, data, enterprise zone, ops |
| **41** ETL → graph traversal | `41-etl-staging-graph-traversal.dot` | How catalog becomes adjacency walks for accurate answers |

Related: [`PIPELINE-AND-MODULE-GUIDE.md`](PIPELINE-AND-MODULE-GUIDE.md) · [`15-…RDF…`](15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md) · [`16-…Runtime…`](16-Enterprise-Runtime-Capabilities.md)

---

## 1. Big picture (how the whole thing is connected)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  ENTERPRISE SOURCES                                                          │
│  PIM · CRM · FSM · Claims  (prod HTTPS)  or  Mock :8090 / JSON fixtures      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ parallel extract (runtime.parallel_map)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR  graph/enterprise_pipeline/orchestrator.py                     │
│  ① knowledge_etl → ② smoke_validation → ③ staging_promotion                  │
│         │                    │                      │                          │
│         ▼                    ▼                      ▼                          │
│   OntologyBuilder      scenario gates         populate_graph()                 │
│   catalog JSON +       (block promote)        MERGE into Neo4j                 │
│   provenance + lineage                                                         │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Bolt :7687  (unique constraints + edges)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  NEO4J KNOWLEDGE GRAPH                                                       │
│  Product→Symptom→FailureMode→Part/Component + DiagnosticStep trees           │
│  Optional Redis: shared cache / rate limit / budget / concurrent diagnose    │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Cypher multi-hop (not full scan)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RUNTIME                                                                     │
│  UI :3000 → API :8080 → diagnosis_service → LangGraph → graph_rag            │
│  + warranty gate + claims + guardrails + OTEL                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

Render diagram **39** for the full labeled Graphviz version of this story.

---

## 2. Network topology (enterprise landscape)

### 2.1 Tiers and ports (as built)

| Tier | Component | Port / protocol | Code / asset |
|------|-----------|-----------------|--------------|
| Client | Next.js UI | `:3000` HTTPS (prod) | `frontend/` |
| Edge | Ingress / local reverse proxy | TLS → UI/API | `k8s/`, demo: localhost |
| App | FastAPI diagnostics | `:8080` HTTP JSON | `api/main.py` |
| App | Mock enterprise apps | `:8090` HTTP | `simulation/mock_enterprise_apps.py` |
| Data | Neo4j | Bolt `:7687`, Browser `:7474` | `graph/neo4j_client.py` |
| Data | Redis (optional) | `:6379` | `runtime/redis_client.py` |
| Data | SQLite ops | file path | `utils/persistence.py` |
| Batch | ETL orchestrator | CronJob / admin API | `graph/enterprise_pipeline/orchestrator.py` |
| Ops | Prometheus metrics | `GET /metrics` | `observability/metrics.py` |
| Ops | OTEL | OTLP when enabled | `observability/tracing.py` |

### 2.2 Trust boundaries (production-shaped)

1. **Public / agent network** → Ingress only (UI + API).
2. **App subnet** — API talks Bolt to Neo4j, optional Redis, SQLite/PVC.
3. **Integration zone** — outbound HTTPS to PIM/CRM/Claims/FSM (or mock).
4. **Admin plane** — `X-Admin-Token` on `/admin/pipeline/*` when configured.
5. **Multi-replica shared state** — set `REDIS_URL` or remain single-node memory.

Render diagram **40** for the visual topology.

### 2.3 Demo vs production mapping

| Concern | Demo default | Enterprise target |
|---------|--------------|-------------------|
| Enterprise systems | Mock `:8090` + JSON fixtures | Real connector URLs in settings |
| Neo4j | Single local container | StatefulSet + PVC (+ replicas later) |
| Shared rate/cache | In-process | Redis |
| UI | Next.js dev `:3000` | Ingress + CDN |
| ETL | Manual / admin POST | K8s CronJob + lineage alerts |
| Auth | Open demo / admin token | OIDC/JWT + tenant claims (**remaining**) |

---

## 3. ETL → staging → graph store → fast traversal

### 3.1 Stage machine

| Stage | Function | Success criteria |
|-------|----------|------------------|
| **Extract** | Parallel connector `fetch()` | PIM/FSM/Claims OK (CRM optional) |
| **Transform** | `OntologyBuilder.build_catalog_payload` | Valid product trees + provenance |
| **Catalog** | Write dual JSON paths | Files on disk + `etl_batch_id` |
| **Smoke** | `run_smoke_validation` | Scenario suite passes |
| **Promote** | `run_staging_promotion` | `populate_graph` MERGE counts |
| **Serve** | Cypher from GraphRAG | Ranked FM + parts + tree |

If smoke fails, **promotion is blocked** (staging gate).

### 3.2 Why the graph is “really quick” to traverse

Neo4j stores **adjacency**, not join tables:

1. **Unique constraints** on entity ids → O(1)-ish node lookup by `product_id` / `symptom_id`.
2. **Pre-materialized edges** (`INDICATES`, `REQUIRES_PART`, `NEXT_STEP`, `IMPACTS_COMPONENT`) → multi-hop walks without recomputing ontology each request.
3. **Diagnosis is path-bounded**: start at product/symptoms, not whole-graph scan.
4. **Hot read caches**: ontology schema + product subgraphs (`runtime` TTL / Redis).
5. **Deterministic scoring** reads edge properties + counts already on the graph (`reliability.py`).

### 3.3 Accuracy chain (what the edges mean)

```text
Asset ─INSTANCE_OF→ Product
Product ─HAS_SYMPTOM→ Symptom ─INDICATES{confidence}→ FailureMode
Product ─HAS_ERROR_CODE→ ErrorCode ─INDICATES→ FailureMode
FailureMode ─REQUIRES_PART→ Part
FailureMode ─IMPACTS_COMPONENT→ Component ─REALIZED_BY→ Part
DiagnosticStep ─CONFIRMS|RULES_OUT→ FailureMode ; ─NEXT_STEP→ DiagnosticStep
Claim/HistoricalResolution ─CONFIRMED→ FailureMode  (precedent)
```

Render diagram **41** for ETL bands + stored topology + runtime walk.

---

## 4. How code connects the whole pipeline

This section is the “wiring diagram” in source form: **which snippets glue stages together**.

### 4.1 Orchestrator — batch spine

`graph/enterprise_pipeline/orchestrator.py` runs the three pipelines **in order**:

```python
# graph/enterprise_pipeline/orchestrator.py (conceptual)
from graph.enterprise_pipeline.pipelines.knowledge_etl import run_knowledge_etl
from graph.enterprise_pipeline.pipelines.smoke_validation import run_smoke_validation
from graph.enterprise_pipeline.pipelines.staging_promotion import run_staging_promotion

def run_all(*, load_neo4j: bool = True, promote: bool = True) -> int:
    etl = run_knowledge_etl(load_neo4j=load_neo4j)
    if etl.errors:
        return 1
    smoke = run_smoke_validation()
    if not smoke.ok:
        return 1  # promotion skipped
    if promote:
        promo = run_staging_promotion(smoke_passed=smoke.ok)
        if not promo.promoted:
            return 1
    return 0
```

**CLI:** `python -m graph.enterprise_pipeline.orchestrator`

### 4.2 Knowledge ETL — extract → transform → catalog → optional load

```python
# graph/enterprise_pipeline/pipelines/knowledge_etl.py (conceptual)
pairs = parallel_map(list(connectors.items()), _fetch_connector, max_workers=workers)
# ...
builder = OntologyBuilder(etl_batch_id=report.batch_id)
catalog = builder.build_catalog_payload(pim=..., fsm=..., claims=..., crm=...)
# write settings.enterprise_catalog_file + settings.data_file
if load_neo4j:
    populate_graph(driver, catalog, etl_batch_id=report.batch_id)
    invalidate_all_named_caches()
```

| Step | Module |
|------|--------|
| Parallel I/O | `runtime/concurrency.py` → `parallel_map` |
| Transform | `graph/enterprise_pipeline/transformers/ontology_builder.py` |
| Extensions | `graph/warranty_catalog_extensions.py` |
| Lineage | `utils/lineage_store.py` |
| Load | `graph/populate_graph.py` |

### 4.3 Staging promotion — gate then MERGE

```python
# graph/enterprise_pipeline/pipelines/staging_promotion.py (conceptual)
if require_smoke_pass and not smoke_passed:
    return blocked
catalog = json.loads(settings.enterprise_catalog_file.read_text())
report.entity_counts = populate_graph(driver, catalog, etl_batch_id=report.batch_id)
```

### 4.4 Graph load — materialize ontology for traversal

```python
# graph/populate_graph.py (conceptual)
def populate_graph(driver, data, *, etl_batch_id=None):
    session.execute_write(create_constraints)  # unique product_id, symptom_id, …
    for product_data in data["products"]:
        # MERGE Product, Symptom, FailureMode, Part, Component, …
        # MERGE HAS_SYMPTOM, INDICATES, REQUIRES_PART, IMPACTS_COMPONENT, …
```

Driver pool: `graph/neo4j_client.get_driver()` with `max_connection_pool_size` from settings.

### 4.5 API entry — request path to diagnosis

```python
# api/main.py (conceptual)
@app.post("/diagnose")
def diagnose(req: DiagnoseRequest) -> DiagnoseResponse:
    slot = _diagnose_limiter.try_acquire()   # concurrency admission
    try:
        return _diagnose_inner(req)
    finally:
        _diagnose_limiter.release(slot)

def _diagnose_inner(req):
    message = guard_request(req.message, ...)           # input guardrails
    crm = enrich_session_from_crm(...)                  # integrations/crm_enrichment.py
    warranty = check_warranty_eligibility(crm)          # integrations/warranty_eligibility.py
    outcome = run_full_diagnosis(message, product_id=..., asset_id=..., crm_context=crm, warranty=warranty)
    # ... format DiagnoseResponse + graph_subgraph
```

Admin can also trigger pipelines without shell access:

- `POST /admin/pipeline/dry-run-etl`
- `POST /admin/pipeline/run-smoke`
- `POST /admin/pipeline/promote-staging`

### 4.6 Shared service — one business path for API (and any UI)

```python
# services/diagnosis_service.py
def run_full_diagnosis(message, *, product_id=None, asset_id=None, crm_context=None, warranty=None):
    if active_warranty and not active_warranty.get("eligible"):
        return DiagnosisOutcome(..., warranty_blocked=True)
    result = run_diagnosis(message, product_id=product_id, asset_id=asset_id if enriched else None)
    # optional case_management on escalation
    return DiagnosisOutcome(...)
```

### 4.7 LangGraph — agent workflow nodes

```python
# agents/diagnosis_graph.py
graph.add_node("detect_product", node_detect_product)
graph.add_node("run_diagnosis", node_run_graph_diagnosis)  # → tool_diagnose → graph_rag
graph.add_node("format_response", node_format_response)
graph.add_node("handle_escalation", node_handle_escalation)
# edges: detect → diagnose → format → escalate → END
```

### 4.8 GraphRAG — where Neo4j is walked for the answer

```python
# agents/tools.py → graph.graph_rag.diagnose(...)
# Inside graph_rag (conceptual stages):
# 1. resolve product (message / product_id / asset)
# 2. match symptoms / error codes (lexical / hybrid)
# 3. Cypher: Symptom-[:INDICATES]->FailureMode  (confidence)
# 4. reliability.rank  (FMEA S/O/D + Bayesian posterior from graph)
# 5. diagnostic_engine.traverse NEXT_STEP / CONFIRMS
# 6. parts_predictor  REQUIRES_PART + BOM + SKU + claim precedent
# 7. assemble formatted_response + provenance_trail + graph_subgraph
```

### 4.9 Read API for explorers (cached)

```python
# api/main.py
@app.get("/graph/ontology") → get_ontology_schema()      # runtime named cache
@app.get("/graph/product/{id}") → get_product_subgraph()  # TTL cache, Neo4j neighborhood
```

Implementation: `graph/graph_visualization.py` + `runtime.cache.get_named_cache`.

### 4.10 Connection map (file → responsibility)

| File | Connects |
|------|----------|
| `graph/enterprise_pipeline/orchestrator.py` | ETL ↔ smoke ↔ promote |
| `graph/enterprise_pipeline/pipelines/knowledge_etl.py` | Connectors ↔ OntologyBuilder ↔ JSON ↔ Neo4j |
| `graph/enterprise_pipeline/transformers/ontology_builder.py` | Source records ↔ catalog ontology |
| `graph/populate_graph.py` | Catalog ↔ Neo4j edges |
| `graph/neo4j_client.py` | All Bolt sessions (pool) |
| `api/main.py` | HTTP ↔ service ↔ admin pipelines ↔ graph GETs |
| `services/diagnosis_service.py` | Warranty + diagnosis + escalation policy |
| `agents/diagnosis_graph.py` | LangGraph node chain |
| `agents/tools.py` | Agent ↔ `graph_rag.diagnose` |
| `graph/graph_rag.py` | Cypher + ranking assembly |
| `graph/reliability.py` | Graph signals ↔ FMEA/Bayes |
| `graph/diagnostic_engine.py` | NEXT_STEP tree |
| `graph/parts_predictor.py` | BOM / parts ranking |
| `integrations/*` | CRM · warranty · claims · cases |
| `runtime/*` | Cache · Redis · concurrency · partitions |
| `guardrails/*` | Rate limit · input/output safety |
| `config/settings.py` | URLs, paths, pools, Redis, tenants |

---

## 5. Request sequence (one diagnosis)

```text
Browser UI
  → POST /diagnose { message, product_id?, asset_id?, customer_id? }
  → middleware: X-Request-ID, tenant rate-limit key
  → ConcurrencyLimiter.try_acquire
  → guard_request(message)
  → enrich_session_from_crm
  → check_warranty_eligibility  (may short-circuit)
  → run_full_diagnosis
       → run_diagnosis (LangGraph)
            → resolve product
            → tool_diagnose → graph_rag.diagnose
                 → Neo4j Cypher multi-hop
                 → reliability + tree + parts
            → format_response
            → maybe save_escalation
  → validate_output (PII/length)
  → DiagnoseResponse JSON (+ optional graph_subgraph)
```

---

## 6. How to render and view the diagrams

```bash
# Requires Graphviz (`dot` on PATH)
bash docs/graphviz/render_all.sh

# Or single diagram:
dot -Tpng -Gdpi=150 docs/graphviz/39-complete-enterprise-system-pipeline.dot \
  -o docs/graphviz/rendered/png/39-complete-enterprise-system-pipeline.png
dot -Tsvg docs/graphviz/39-complete-enterprise-system-pipeline.dot \
  -o docs/graphviz/rendered/svg/39-complete-enterprise-system-pipeline.svg
# same for 40-… and 41-…
```

Then open:

- `docs/graphviz/rendered/png/39-complete-enterprise-system-pipeline.png`
- `docs/graphviz/rendered/png/40-enterprise-network-topology.png`
- `docs/graphviz/rendered/png/41-etl-staging-graph-traversal.png`

---

## 7. Mental model checklist

| Question | Answer |
|----------|--------|
| Where is “truth” for diagnosis? | **Neo4j graph** edges + properties after promote/load |
| Where is batch truth before graph? | **Catalog JSON** + lineage |
| What connects batch to graph? | `populate_graph` / staging promotion |
| What connects user to graph? | API → service → LangGraph → `graph_rag` Cypher |
| What makes multi-pod safe? | `REDIS_URL` for cache/rate/budget/admission |
| What is still enterprise-gap? | Real AuthN/Z, Neo4j HA, async ETL workers, Postgres ops |

---

## 8. Quick commands (reproduce the pipeline)

```bash
source venv/bin/activate

# Full batch spine
python -m graph.enterprise_pipeline.orchestrator

# ETL only dry-run
python -m graph.enterprise_pipeline.orchestrator --dry-run

# Load graph from current catalog
python graph/populate_graph.py

# Runtime API (separate terminals)
uvicorn api.main:app --port 8080
# frontend :3000

# Optional shared state
docker compose -f docker/docker-compose.redis.yaml up -d
export REDIS_URL=redis://localhost:6379/0
```
