# Delta stepping, partitioning, concurrency & sharding

**Status:** Code-true implementation guide for WarrantyGraph / remote diagnostics
**Audience:** engineers, architects, operators
**Rule:** Prefer this document + `docs/sdd/AS_BUILT.md` over marketing claims.
**Last verified against tree:** 2026-07-15

---

## 0. Short answers (read this first)

| Capability | In this repo? | What exists | What does **not** exist |
|------------|---------------|-------------|-------------------------|
| **Delta / incremental knowledge updates** | **Partial — yes for ABox delta ops** | Change preview, entity-level delta (catalog ↔ Neo4j), selection-scoped materialize/promote, `MERGE` upserts, `incremental_sync` pipeline **mode** | CDC from live SAP/SFDC, watermark consumers, Kafka event bus, true “only changed edges” streaming writers |
| **Partitioning** | **Logical — yes** | Tenant/product key helpers, rate-limit/cache key partitioning, selection by `product_ids`, dual env (staging/prod) | Hard multi-tenant ACL isolation, physical data partition by brand/region |
| **Multi-threading / concurrency** | **Yes (bounded)** | `parallel_map` for connector I/O, diagnose admission limiter, rate limits, Neo4j connection pool | Unbounded workers, parallel ranking of a single diagnosis, async job queue |
| **Sharding (Neo4j Fabric / composite DBs)** | **No** | Documented as non-claim / roadmap | Fabric, composite DB query fan-out, product-line physical shards |
| **Neo4j HA / read replicas (cluster)** | **No** | Single-node Docker prod + staging | Causal cluster primaries/secondaries (Enterprise) |

**Bottom line:** You have **operator-facing delta stepping** for knowledge packs and **runtime concurrency/partition keys** suitable for a multi-pod API demo. You do **not** have full enterprise graph sharding or cluster HA. That is intentional for the current phase (see `AS_BUILT` explicit non-claims).

---

## 1. Authoritative sources (read these, then the code)

These sources define industry vocabulary. Implementation steps later cite them.

| Topic | Source | What to take away |
|-------|--------|-------------------|
| Neo4j **clustering** (HA, primaries/secondaries, causal consistency) | [Neo4j Ops Manual — Clustering introduction](https://neo4j.com/docs/operations-manual/current/clustering/introduction/) | Primaries for writes + fault tolerance; secondaries for read scale; bookmarks for read-your-writes |
| Neo4j **composite DBs / Fabric-style sharding** | [Composite databases — concepts](https://neo4j.com/docs/operations-manual/current/scalability/composite-databases/concepts/) | Shards = separate graphs with same or different models; relationships do not span shards; query via composite DB |
| Graph sharding hardness | Neo4j Fabric / LDBC discussions (cross-shard edges need proxy nodes / correlated ids) | Partition key must match **query shape** (here: product-scoped diagnosis) |
| Cypher **MERGE** / upserts | [Neo4j Cypher Manual — MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/) | Idempotent load; pair with uniqueness constraints |
| Uniqueness → indexes | [Cypher constraints](https://neo4j.com/docs/cypher-manual/current/constraints/) | `REQUIRE … IS UNIQUE` creates unique index; used on load + seek |
| CDC / incremental enterprise loads | Industry ETL practice (Kimball-style deltas; CDC streams) | Incremental = process **changed records only**, not full dump every time |
| Bounded concurrency | [Python `concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html); SRE bulkheads ([Google SRE — overload](https://sre.google/sre-book/handling-overload/)) | Cap workers; admit expensive work; fail closed under load |
| CAP / consistency | Gilbert & Lynch (Brewer’s CAP); prefer consistency for diagnostic truth | Wrong diagnosis worse than temporary unavailability |

**Repo truth tables:** `docs/sdd/AS_BUILT.md`, `docs/sdd/08-GAPS.md`, `docs/16-Enterprise-Runtime-Capabilities.md`, `docs/19-Indexes-Constraints-and-Lookup-Performance.md`, `docs/20-Enterprise-KG-Ingestion-Pipeline-Architecture.md`.

---

## 1.5 Indexing — as-built code (apply with every load)

Delta, partition, and concurrency all assume **identity seeks** on business keys. Indexing is not optional scaffolding; it is the first beat of graph ops.

### 1.5.1 5W+H

| | |
|--|--|
| **What** | Unique constraints that create unique indexes on business keys (`product_id`, `symptom_id`, …) |
| **How** | Neo4j 5: `CREATE CONSTRAINT IF NOT EXISTS FOR (n:Label) REQUIRE n.key IS UNIQUE` then `MERGE`/`MATCH` on that key with `$parameters` |
| **Where** | `graph/populate_graph.py` → `create_constraints(tx)`; verified with Browser `SHOW CONSTRAINTS` / `SHOW INDEXES` |
| **When** | On every `populate_graph` / promote materialize **before** entity MERGEs; used on every diagnose product resolve |
| **Who** | ETL loader creates; GraphRAG and Admin promote paths consume |
| **Why** | Fast seek (not label scan); prevents duplicate Products/Symptoms on re-load; pairs with MERGE upserts |

**Beyond 5W+H — mental model:** Index = phone book to the house; relationships = roads between houses. Indexes do not replace multi-hop meaning; they find the starting node.

**Authoritative sources:** [Neo4j constraints](https://neo4j.com/docs/cypher-manual/current/constraints/), [MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/), [query tuning](https://neo4j.com/docs/cypher-manual/current/query-tuning/), repo `docs/19-Indexes-Constraints-and-Lookup-Performance.md`.

### 1.5.2 Code (source of truth)

```python
# graph/populate_graph.py
def create_constraints(tx) -> None:
    for query in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (fm:FailureMode) REQUIRE fm.failure_mode_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ds:DiagnosticStep) REQUIRE ds.step_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Part) REQUIRE p.part_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:HistoricalResolution) REQUIRE r.resolution_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Model) REQUIRE m.model_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sku:SKU) REQUIRE sku.sku_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.component_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ec:ErrorCode) REQUIRE ec.error_code_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wp:WarrantyPolicy) REQUIRE wp.policy_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (cl:Claim) REQUIRE cl.claim_id IS UNIQUE",
    ]:
        tx.run(query)


def populate_graph(driver, data, *, etl_batch_id=None):
    with driver.session() as session:
        session.execute_write(create_constraints)  # indexes first
        # then MERGE products, symptoms, failure modes, …
        session.run(
            """
            MERGE (p:Product {product_id: $product_id})
            SET p.name = $name, p.category = $category, …
            """,
            product_id=…, name=…,
        )
```

### 1.5.3 Run & verify

```bash
# Bootstrap full catalog (constraints + MERGE)
python -m graph.populate_graph
```

In Neo4j Browser (`http://localhost:7474`, password from compose):

```cypher
SHOW CONSTRAINTS;
SHOW INDEXES;

PROFILE
MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
RETURN fm LIMIT 5
```

Expect unique constraints on the keys above. In the PROFILE plan, the product step should be a **unique index seek**, not a full label scan.

### 1.5.4 How indexing couples to delta / partition / concurrency

```text
create_constraints  →  unique seek on product_id
entity_delta        →  compares catalog vs Neo4j by those same keys
selection promote   →  MERGE only selected product_ids (index-backed upserts)
partition keys      →  tenant|product for cache/rate (logical; not a Neo4j index)
admission + threads →  protect Bolt pool while seeks stay O(log n) on keys
future Fabric       →  still requires unique keys *inside* each shard
```

### 1.5.5 Study Lab

- **Flashcards hub:** cards `fc-unique-constraint-index`, `fc-show-indexes-profile`, `fc-cypher-merge`, `fc-entity-delta`, …
- **Masters tab:** *Master This Code: Graph Ops — Indexes, Delta, Partition, Concurrency, Sharding* (`mc-03-graph-ops-index-delta-scale`) — Flashcards + Test drills with 5W+H (Turtle ontology guide is **unchanged**).

---

## 2. What “delta stepping” means here

Two different meanings exist in literature:

| Term | Meaning | Relevant to this app? |
|------|---------|------------------------|
| **Delta-stepping (graph algorithm)** | Parallel SSSP shortest-path algorithm (Meyer/Sanders) | **No** — not implemented; we do not run that algorithm |
| **Delta / incremental stepping (data)** | Advance knowledge graph by applying only **changes** (NEW/UPDATE packs, entity diffs) in ordered steps | **Yes** — this is what the Admin control plane does |

This document uses **delta stepping** = **incremental ABox change application**: detect delta → select products → validate → materialize → promote staging → smoke → promote production → invalidate caches.

---

## 3. Delta stepping — as-built design

### 3.1 Mental model

```text
Source packs / fixtures / mock SoR
        │
        ▼
  change_preview   ← NEW / UPDATE / IN_SYNC vs production Neo4j
        │
        ▼
  entity_delta     ← per-product: which symptoms/FMs/steps/parts are NEW
        │
        ▼
  selection (product_ids)  ← work partition: only these products
        │
        ▼
  validate ABox (shapes)
        │
        ▼
  materialize (catalog upsert for selection)
        │
        ▼
  promote_graph staging  (:7688)  MERGE (index-backed keys)
        │
        ▼
  smoke_validate
        │
        ▼
  promote_graph production (:7687)
        │
        ▼
  invalidate_all_named_caches()
```

### 3.2 Components (code map)

| Piece | Path | Role |
|-------|------|------|
| Change preview | `graph/enterprise_pipeline/change_preview.py` | Fleet-level NEW/UPDATE/IN_SYNC vs live graph |
| Entity delta | `graph/enterprise_pipeline/entity_delta.py` | Per-product entity lists: catalog vs staging/production |
| Selection | Admin API + ingest plan | Scopes materialize/promote to `product_ids` |
| Incremental pipeline id | `incremental_sync` in control-plane registry | Chain intended for live delta (same functions, different mode/trigger) |
| Load | `graph/populate_graph.py` | Constraints then `MERGE` by business keys |
| Promote | control plane `promote_graph` | Writes staging and/or production |
| Cache drop | `runtime/cache.py` `invalidate_all_named_caches` | After successful load |

### 3.3 What is “delta” exactly?

**Entity delta** (`compute_product_entity_delta` / `build_selection_entity_deltas`):

- Compares **catalog ABox** for a product to **Neo4j** (counts and ids for symptoms, failure modes, steps, parts, components, error codes, resolutions).
- Classifies roughly: **missing_catalog**, **needs work** (core entities to add), **in_sync**.
- Optional RDF highlight of **NEW ABox triples only** (TBox unchanged).

**Change preview**:

- Operator-facing view: which products are NEW vs UPDATE vs already in production.
- Drives selection so you do not re-promote the whole fleet.

**MERGE load**:

- Not “delete graph and reload.”
- `MERGE (n:Label {business_id: $id})` + `SET` properties → **upsert** semantics (Cypher MERGE manual).

### 3.4 What is **not** full enterprise CDC delta

| Missing | Why it matters |
|---------|----------------|
| Live connector CDC / watermarks | Continuous SoR change capture |
| Async job queue | Long ETL off the API request thread |
| Edge-level “only changed relationships” export | Finer grain than product selection |
| Automatic confidence Bayesian update from claims stream | Closed-loop learning gap (P2) |

`AS_BUILT` non-claims: live SAP/SFDC, async ETL queue, Kafka streaming write path.

---

## 4. Partitioning — as-built vs full

### 4.1 Industry levels (authoritative framing)

| Level | Definition | Neo4j / platform mapping |
|-------|------------|---------------------------|
| **Logical partition** | Same DB; keys isolate tenants/products for cache, limits, batch work | **Implemented** |
| **Environment partition** | Staging vs production graphs | **Implemented** (dual Bolt) |
| **Physical partition / shard** | Separate databases/servers; composite query | **Not implemented** |
| **Cluster role partition** | Primaries write / secondaries read | **Not implemented** (single-node) |

Neo4j official clustering doc: databases can have independent primary/secondary topologies; secondaries scale **reads** asynchronously ([clustering introduction](https://neo4j.com/docs/operations-manual/current/clustering/introduction/)).
Composite DBs: shards are separate graphs; cross-shard relationships are not first-class ([composite concepts](https://neo4j.com/docs/operations-manual/current/scalability/composite-databases/concepts/)).

### 4.2 What this repo implements

| Mechanism | Code | Purpose |
|-----------|------|---------|
| `PartitionKey` / `partition_for_rate_limit` / `partition_for_request` | `runtime/partitioning.py` | Tenant (+ product) in rate-limit and cache namespaces |
| Selection `product_ids` | Admin + pipelines | **Work partition** — only selected products materialize/promote |
| Dual Neo4j env | `neo4j_client` env + compose | **Environment partition** for safe promote |
| Diagnose product scope | `graph_rag` Cypher `Product {product_id:$id}` | Query partition by product neighborhood |

### 4.3 What is **not** implemented

| Gap | Impact |
|-----|--------|
| OIDC tenant ACL forcing Cypher filters | Demo open / optional admin token only |
| Neo4j multi-database per tenant | Single graph per env |
| Fabric / composite product-line shards | No fan-out Cypher across shards |
| Kafka partition keys for ingest | No event bus |

---

## 5. Multi-threading & concurrency — as-built

### 5.1 Design rules (aligned with Python + SRE practice)

| Do | Don’t |
|----|-------|
| Parallelize **independent I/O** (PIM/FSM/Claims/CRM fetch) | Parallelize single-request Bayes ranking (correctness first) |
| Bound `max_workers` | Spawn unbounded threads per request |
| Admit only N concurrent diagnoses | Let spikes open unbounded Bolt sessions |
| Share rate/budget via Redis when multi-pod | Assume in-process counters are global |

### 5.2 Code map

| Capability | Module | Default |
|------------|--------|---------|
| Parallel map | `runtime/concurrency.py` → `parallel_map` | `max_workers` typically 4 (settings `etl_connector_max_workers`) |
| Diagnose admission | `runtime/concurrency_limit.py` → `ConcurrencyLimiter` | max concurrent diagnoses **32** |
| Rate limit | `guardrails/rate_limit.py` | **60/min** (partitioned by tenant/client/route) |
| Neo4j pool | driver settings | pool size **50** |
| Caches | `runtime/cache.py` | thread-safe memory or Redis |

### 5.3 Where concurrency runs in the pipeline

```text
structured_extract
  → parallel_map(fetch connectors)     ← threads HERE (I/O)
  → OntologyBuilder.build              ← serial (deterministic ABox)
  → validate                           ← serial
  → populate_graph MERGE               ← serial sessions / ordered writes
diagnose
  → rate limit check
  → admission acquire
  → GraphRAG Cypher + Bayes            ← one request path, not fan-out ranked
  → admission release
```

### 5.4 Gaps

| Gap | Status |
|-----|--------|
| Async ETL worker pool / queue (Celery/RQ/Arq) | **Not built** — promote often sync in API |
| Product-chunked parallel transform at huge scale | Partial / not primary path |
| Redis **required** multi-pod | Code ready; default memory if no `REDIS_URL` |

---

## 6. Sharding — as-built vs provisioned

### 6.1 Honest status

**Neo4j Fabric / composite multi-shard: NOT built.**
Listed under `AS_BUILT` explicit non-claims: *“Neo4j Fabric multi-shard”*.

What you **do** have that *prepares* for product-based sharding later:

1. **Natural partition key:** `product_id` (diagnosis never needs whole-graph scan if scoped).
2. **Selection-scoped promote:** batch by product list.
3. **Logical tenant keys:** ready to include in Cypher when ACL lands.
4. **Dual env:** not a shard, but separates write risk.

### 6.2 Authoritative Neo4j sharding notes (for future design)

From Neo4j composite/Fabric concepts:

- **Data sharding:** same model, different data subsets on different databases/servers.
- Relationships typically **do not cross shards**; cross-shard links use **proxy nodes + correlating ids**.
- For warranty diagnosis, the natural shard key is **product line / brand / region** such that almost all `INDICATES` / `CONFIRMS` edges stay **inside** one shard.
- Cross-shard use cases (global analytics) go through composite queries or offline ETL, not the chat hot path.

### 6.3 Cluster HA (also not as-built)

Official clustering:

- **Primaries:** write quorum, fault tolerance (`M = 2F + 1`).
- **Secondaries:** async read scale.
- Drivers + **bookmarks** for causal consistency (read your writes).

This demo: **one** production container + **one** staging container (not a Raft cluster).

---

## 7. Capability matrix (everything in one place)

| Capability | As-built | Partial | Missing |
|------------|----------|---------|---------|
| Entity delta (catalog vs Neo4j) | ● | | |
| Change preview NEW/UPDATE | ● | | |
| Selection-scoped materialize/promote | ● | | |
| MERGE upsert load | ● | | |
| Unique constraints / indexes | ● | | |
| Pipeline mode `incremental_sync` | ● | watermark empty | |
| Dual staging/prod | ● | | |
| Logical partition keys | ● | | |
| Parallel connector extract | ● | | |
| Diagnose admission + rate limit | ● | | |
| Redis multi-pod backends | ● code | default memory | |
| Live CDC / Kafka | | | ● |
| Async job queue | | | ● |
| Neo4j Fabric shards | | | ● |
| Neo4j causal cluster HA | | | ● |
| Hard tenant isolation | | logical only | ● ACL |

---

## 8. How to **run** what already works (step by step)

### 8.1 Prerequisites

```bash
# From repo root
docker info   # Docker Desktop running
source venv/bin/activate
pip install -r requirements.txt   # once
```

### 8.2 Start infra

```bash
docker compose -f docker/docker-compose.infra.yaml up -d
# Expect: Neo4j prod :7687/:7474, staging :7688/:7475, Redis :6379
```

Optional observability:

```bash
docker compose -f docker/docker-compose.observability.yaml up -d
```

### 8.3 Start API + UI + mock SoR

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_STAGING_URI=bolt://localhost:7688
export NEO4J_PASSWORD=password
export REDIS_URL=redis://localhost:6379/0   # multi-pod realism

# API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8080

# Mock enterprise systems (optional)
python -m simulation.mock_enterprise_apps   # :8090

# Frontend
cd frontend && npm run dev -- --port 3000
```

Or use project `./restart-all.sh` if preferred.

### 8.4 Prove runtime concurrency settings

```bash
curl -s http://localhost:8080/health | python -m json.tool
# Look under runtime: caches, redis mode, rate, concurrency
```

### 8.5 Bootstrap graph (full load) — not delta

```bash
python -m graph.populate_graph
# Creates UNIQUE constraints then MERGEs catalog
```

### 8.6 Delta stepping operator path (UI)

1. Open http://localhost:3000 → **Admin**
2. **Fetch** (dry extract / change preview)
3. Review **NEW / UPDATE / IN SYNC**
4. **Select** only products that need work
5. **Validate ABox** (shapes)
6. **Materialize** (selection-scoped catalog upsert)
7. **Smoke**
8. **Approve**
9. **Promote staging** → inspect :7475
10. **Promote production** → chat uses :7687
11. Confirm caches invalidated (subgraph/diagnose recompute)

### 8.7 Delta via API (tools)

```bash
# Change preview
curl -s 'http://localhost:8080/admin/pipeline/change-preview?refresh=true' \
  -H "X-Admin-Token: $ADMIN_TOKEN" | python -m json.tool | head

# Entity delta for selection
curl -s 'http://localhost:8080/admin/pipeline/entity-delta?product_ids=esp-001,hmd-001' \
  -H "X-Admin-Token: $ADMIN_TOKEN" | python -m json.tool | head

# Run pipeline (example ids from registry)
curl -s -X POST 'http://localhost:8080/admin/kg-pipelines/incremental_sync/run' \
  -H 'Content-Type: application/json' \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -d '{"mode":"incremental","dry_run":true,"target_env":"staging","product_ids":["esp-001"]}'
```

*(Admin token required if configured; demo may allow open admin — check settings.)*

### 8.8 Verify indexes after load

In Neo4j Browser (`http://localhost:7474`):

```cypher
SHOW CONSTRAINTS;
SHOW INDEXES;
```

Expect unique constraints on `product_id`, `symptom_id`, `failure_mode_id`, etc.

### 8.9 Profile index use on retrieval

```cypher
PROFILE
MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
WHERE s.symptom_id IN $symptom_ids
RETURN fm.failure_mode_id, sum(coalesce(ind.confidence, 0)) AS score
ORDER BY score DESC
```

Look for **NodeUniqueIndexSeek** (or equivalent) on `Product`, not `NodeByLabelScan` for the product step.

---

## 9. Step-by-step: implement **stronger** delta stepping (roadmap)

Use when fixtures are no longer enough. Order matters.

### Phase D1 — Watermarked incremental extract (P1)

1. **Define watermark store** (Redis or Postgres): last successful extract timestamp per source system.
2. **Connector contract:** each connector accepts `since: datetime` and returns only changed records.
3. **Wire `incremental_sync`:**
   - read watermarks → extract deltas → preprocess → materialize selection inferred from delta product ids → validate → promote staging.
4. **Advance watermark only after successful promote** (or after staging smoke — choose one policy and document it).
5. **Tests:** fixture “clock” + two extracts; second extract empty if no changes.

**Tools:** Python connectors, Redis/Postgres, pytest with frozen time.

**Authoritative idea:** CDC/incremental ETL loads only changed rows (warehouse delta loads), not full snapshots every night.

### Phase D2 — Async control plane (P1)

1. Add job queue (e.g. **Arq / RQ / Celery** + Redis).
2. Admin “Run pipeline” enqueues job id; UI polls `GET /admin/kg-pipelines/runs/{id}`.
3. Worker process runs `run_pipeline(...)` off the API thread.
4. Keep **admission** separate from ETL workers (different pools).

**Tools:** Redis, worker process in `docker-compose`, CI job for worker image.

### Phase D3 — Optional edge-level patch files (P2)

1. Emit `product_id + entity_type + entity_id + op(add|update|remove)` JSON patches from entity_delta.
2. Apply patches with targeted Cypher `MERGE`/`DETACH DELETE` instead of re-merging entire product when safe.
3. Keep full product MERGE as fallback for corrupt state repair.

---

## 10. Step-by-step: implement **sharding** (only when scale forces it)

Do **not** shard early. Neo4j and industry guidance: shard when a single DB’s storage/CPU cannot meet SLOs **and** query pattern allows disjoint graphs.

### Phase S0 — Prove you need it

1. Measure: disk, heap, p99 diagnose Cypher, concurrent users.
2. Confirm hot path is **product-scoped** (already true).
3. If yes, product-line / brand is the shard key.

### Phase S1 — Logical readiness (mostly done)

1. Keep all business keys globally unique **or** namespaced per shard (`brand:product_id`).
2. Ensure no diagnose Cypher requires full-fleet scans.
3. Enforce tenant/product filters at API once ACL lands.

### Phase S2 — Physical shards (Neo4j composite / Fabric family)

Per [Neo4j composite database concepts](https://neo4j.com/docs/operations-manual/current/scalability/composite-databases/concepts/):

1. Deploy N Neo4j databases (e.g. `shard_appliance`, `shard_hvac`).
2. Route promote by product catalog → shard map service.
3. Diagnose: resolve shard from product_id → open driver to that DB only.
4. Composite DB only for cross-shard analytics (not chat hot path).
5. Model rare cross-shard links as **proxy nodes + shared ids**, not native cross-DB relationships.

**Tools:** Neo4j Enterprise (for production clustering/composite as licensed), routing table in config/Postgres, ops runbooks.

### Phase S3 — Cluster HA (orthogonal to sharding)

Per [clustering introduction](https://neo4j.com/docs/operations-manual/current/clustering/introduction/):

1. Production graph: **3 primaries** minimum for one-fault write tolerance.
2. Add **secondaries** for read scale of diagnose/explorer.
3. App drivers: use neo4j:// routing URI; pass **bookmarks** after writes if reading secondaries.
4. Staging can remain smaller topology.

---

## 11. Step-by-step: harden concurrency (production multi-pod)

### Already present — turn on for real

```bash
export REDIS_URL=redis://redis:6379/0
export RATE_LIMIT_PER_MINUTE=60          # or settings name in use
# ensure diagnose limiter max_in_flight from settings
```

1. Run **≥2 API replicas** with same `REDIS_URL`.
2. Verify `GET /health` shows redis mode for cache/rate/admission.
3. Load test diagnose; confirm 429 under rate limit and admission errors under concurrency cap.
4. Tune pool size vs Neo4j max connections.

### Next increments

| Step | Action |
|------|--------|
| Separate ETL worker concurrency | Don’t share diagnose admission slots with promote jobs |
| Bulkhead Neo4j | Dedicated pool size for read vs write if needed |
| Timeouts | Bolt + HTTP timeouts on connectors |
| Circuit breakers | On mock/live SoR failures (fail soft, don’t cascade) |

**References:** Python ThreadPoolExecutor bounds; Google SRE overload / load shedding.

---

## 12. Code & config cheat sheet

| Concern | File / setting |
|---------|----------------|
| Unique indexes | `graph/populate_graph.py` `create_constraints` |
| Entity delta | `graph/enterprise_pipeline/entity_delta.py` |
| Change preview | `graph/enterprise_pipeline/change_preview.py` |
| Parallel extract | `runtime/concurrency.py` `parallel_map` |
| Diagnose admission | `runtime/concurrency_limit.py` |
| Partition keys | `runtime/partitioning.py` |
| Rate limit | `guardrails/rate_limit.py` |
| Caches | `runtime/cache.py` |
| Dual env | `graph/neo4j_client.py`, compose ports 7687/7688 |
| Pipeline registry | `graph/enterprise_pipeline/control_plane/registry.py` |
| As-built / gaps | `docs/sdd/AS_BUILT.md`, `08-GAPS.md` |

### Defaults (from AS_BUILT)

| Knob | Default |
|------|---------|
| Connector workers | 4 |
| Max concurrent diagnoses | 32 |
| Rate limit | 60/min |
| Neo4j pool | 50 |
| Ontology cache TTL | 300s |
| Subgraph cache TTL | 60s |
| Diagnose cache | ON, 90s |

---

## 13. How retrieval interacts with all of the above

```text
Request
  → partition rate-limit key (tenant|client|route)
  → admission slot
  → (optional) diagnose cache get
  → resolve Product/Asset by UNIQUE index seek
  → expand product-local edges (no shard hop today)
  → hybrid match + Bayes in process (serial per request)
  → response + release admission
```

| Layer | Role |
|-------|------|
| Unique index | Fast id seek |
| Product scope | Logical partition of graph walk |
| Threads | Not used inside one ranking |
| Redis | Shared cache/limits across pods |
| Delta promote | Keeps production graph current without full rebuild |
| Sharding (future) | Route product to shard **before** Cypher |

---

## 14. Recommended adoption order (do not skip)

```text
1. Operate delta UI + entity-delta correctly on dual Neo4j     ← you are here
2. REDIS_URL multi-pod + load test admission/rate
3. Watermark incremental extract (D1)
4. Async ETL workers (D2)
5. Neo4j cluster HA for production (if uptime SLO)
6. Fabric/composite shards only if single DB cannot scale
```

---

## 15. Non-claims (do not say these in demos)

- “We have Neo4j Fabric sharding.”
- “We have full CDC delta from SAP.”
- “We have HA causal cluster.”
- “Delta-stepping shortest-path algorithm is in the product.”
- “Multi-threading speeds up Bayes ranking.”

Say instead:

> “We apply **selection-scoped ABox deltas** with MERGE into staging then production, **logical partitions** by tenant/product for limits and work, and **bounded concurrency** for connector I/O and diagnose admission. Physical graph sharding and cluster HA are designed against Neo4j’s composite/clustering model but not deployed in this demo.”

---

## 16. Related documents

| Doc | Role |
|-----|------|
| `docs/sdd/AS_BUILT.md` | Code-true checklist |
| `docs/sdd/08-GAPS.md` | Priority gaps |
| `docs/19-Indexes-Constraints-and-Lookup-Performance.md` | Indexes |
| `docs/16-Enterprise-Runtime-Capabilities.md` | Cache / concurrency / partition |
| `docs/20-Enterprise-KG-Ingestion-Pipeline-Architecture.md` | Bootstrap vs incremental |
| `docs/21-KG-Ingestion-Step-by-Step-Runbook.md` | Operator runbook |
| `docs/22-TBox-ABox-Multi-Source-Onboard-Mechanism.md` | TBox/ABox onboard |
| Neo4j clustering intro | HA / secondaries |
| Neo4j composite databases | Sharding model |

---

*This document describes the system as implemented and the authoritative path to grow it. Prefer implementing D1–D2 before any Fabric work.*
