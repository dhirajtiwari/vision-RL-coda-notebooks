# Enterprise Runtime Capabilities: Caching, Concurrency, Partitioning

**Audience:** architects and engineers scaling warranty diagnosis beyond a single demo node
**Code:** `runtime/` · wired into ETL, graph reads, rate limits, Neo4j pool · settings in `config/settings.py`

---

## 1. How industry practice maps to *this* application

Warranty diagnosis platforms (contact-center AI, FSM + claims + PIM) typically apply classical enterprise patterns at three layers:

| Layer | Patterns | Our workload |
|-------|----------|--------------|
| **Experience / API** | Rate limits, request caches for stable GETs, connection pools | `POST /diagnose`, `GET /graph/*`, health |
| **Intelligence** | Deterministic scoring; optional LLM gateway with cache | GraphRAG + FMEA/Bayes (primary); LLM optional |
| **Data / ETL** | Parallel extract, serial transform, batch load, lineage partitions | PIM/FSM/Claims/CRM → ontology → Neo4j |

These are **not** the same as inventing a new domain model (ontology). They are **runtime scalability and isolation** concerns.

---

## 2. What we already had vs what we added

### 2.1 Already present (before this capability pack)

| Capability | Where | Scope |
|------------|-------|--------|
| **In-process rate limiting** | `guardrails/rate_limit.py` | Sliding window, thread lock; single node |
| **Cost circuit breaker** | `finops/budget.py` | Daily LLM spend; single node |
| **Neo4j driver singleton** | `graph/neo4j_client.py` | Shared Bolt driver (driver-internal pool) |
| **SQLite for ops stores** | `utils/persistence.py` | Concurrent-ish local durability for claims/escalations |
| **Streamlit UI cache** | archive UI `@st.cache_data` | UI only; not shared with API |
| **React Query** | Next.js frontend | Client-side request cache |
| **Gateway retries/fallback** | `gateway/router.py` | LLM path when enabled |
| **ETL batch lineage** | `utils/lineage_store.py` | Batch IDs, status audit |

### 2.2 Reusable capability pack (now)

| Module | Purpose |
|--------|---------|
| `runtime/cache.py` | **TTL cache** (memory **or Redis**) + named registry + stats |
| `runtime/redis_client.py` | Optional Redis connection, health, key namespacing |
| `runtime/concurrency.py` | **Bounded** `parallel_map` (thread pool) for I/O-bound work |
| `runtime/concurrency_limit.py` | **Admission control** for concurrent diagnoses (memory/Redis) |
| `runtime/partitioning.py` | Canonical **partition keys** + work **batching** helpers |
| `guardrails/rate_limit.py` | Sliding window — **Redis shared** when `REDIS_URL` set |
| `finops/budget.py` | Daily LLM budget — **Redis shared** when configured |

### 2.3 Wired into the product

| Integration | Behavior |
|-------------|----------|
| **Knowledge ETL extract** | Connectors fetch in parallel (`etl_connector_max_workers`) |
| **Ontology schema GET** | Cached 300s (Redis if configured, else memory) |
| **Product subgraph GET** | Cached 60s (shared across replicas with Redis) |
| **After Neo4j load** | `invalidate_all_named_caches()` (Redis SCAN delete by prefix) |
| **Rate limit key** | Tenant-aware + Redis atomic window when available |
| **Diagnose admission** | `max_concurrent_diagnoses` (503 + Retry-After when saturated) |
| **LLM gateway** | Budget check/record via `DailyCostBudget.from_settings` |
| **Neo4j pool** | Explicit `neo4j_max_connection_pool_size` (default 50) |
| **`GET /health`** | Cache stats, Redis mode, rate/concurrency backends |

### 2.4 Enable multi-replica shared state

```bash
# Optional Redis
docker compose -f docker/docker-compose.redis.yaml up -d
export REDIS_URL=redis://localhost:6379/0
# restart API — health.runtime.redis.mode should become "redis"
```

Empty `REDIS_URL` keeps full functionality on **in-process memory** (demo default).

### 2.4 Intentionally *not* multi-threaded

| Path | Why |
|------|-----|
| **Single diagnosis request** | Correctness and reproducibility first; Cypher path is already fast vs network; parallelizing ranking adds race/complexity without material gain at demo scale |
| **OntologyBuilder merge** | Deterministic serial transform after parallel extract |
| **Shared Neo4j writes in populate** | Sequential MERGE avoids deadlocks and partial graphs |

---

## 3. Caching — pros, cons, when to use

### Pros
- Cuts repeated Neo4j/CPU for **stable** reads (schema, product graphs).
- Improves dashboard / explorer latency.
- Low cost: in-process, no Redis required for single node.
- Stats enable FinOps-style “cache hit rate” observability (handbook ch09).

### Cons / risks
- **Stale data** after catalog load if invalidation is missed (we invalidate on successful ETL load).
- **Memory growth** without `maxsize` (we cap subgraph cache).
- **Wrong for free-text diagnosis**: caching `message → diagnosis` without full key (message, product, asset, policy version, graph batch) risks wrong parts/warranty answers and privacy leakage across customers.
- Multi-replica: in-process caches **diverge** → need Redis or sticky sessions for shared cache.

### Policy we follow

| Cache? | Resource |
|--------|----------|
| **Yes** | Ontology schema, product subgraphs, static config |
| **Maybe** | CRM asset lookup (short TTL; privacy-aware) |
| **No (default)** | Full diagnosis response for free-text messages |
| **Yes (LLM path)** | Prompt/response cache only when gateway enabled + eval-gated (handbook ch06) |

---

## 4. Multi-threading / concurrency — pros, cons, when to use

### Pros
- **Parallel connector extract** hides I/O latency (4 systems).
- Thread pool is simple and works with sync Neo4j/HTTP clients.
- Bounded workers protect upstream rate limits.

### Cons / risks
- GIL: little help for pure CPU; fine for I/O.
- Thread safety: shared mutable state needs locks (our caches/limiters use locks).
- Unbounded fan-out can DDoS Neo4j or SaaS APIs.
- Harder to debug flaky races if misused on diagnosis writes.

### Policy we follow

| Parallelize? | Work |
|--------------|------|
| **Yes** | Independent connector `fetch()` |
| **Yes (later)** | Warm many product subgraphs for admin dashboards |
| **No** | Core diagnosis ranking for one request |
| **Bounded always** | `max_workers` from settings |

Industry analogue: **parallel extract, serial transform, load** (classic ETL) — same pattern as warehouse pipelines.

---

## 5. Partitioning — pros, cons, when to use

### What “partitioning” means here

Not automatic Neo4j sharding. **Logical keys** that align:

1. Rate-limit buckets
2. Cache namespaces
3. ETL lineage slices
4. Future multi-tenant isolation

```
tenant=acme|region=us-east|product=wm-001
tenant=acme|route=/diagnose|client=cust-42
batch=etl-…|source=PIM
```

### Pros
- Prepares multi-tenant SaaS without rewriting handlers.
- Bounds blast radius (one OEM brand’s ETL vs all).
- Enables later physical sharding with **stable keys**.

### Cons / risks
- Over-partitioning fragments cache hit rates.
- Wrong key design causes cross-tenant data bleed if used as ACL (keys are **not** security by themselves — enforce auth separately).
- Neo4j Community single-DB still holds all data unless you multi-database / Fabric later.

### Policy we follow

| Now | Later (production scale) |
|-----|---------------------------|
| Tenant header + default_tenant_id | Real tenant auth + row-level / label security |
| Product-scoped subgraph cache keys | Neo4j database-per-tenant or Fabric |
| ETL lineage partition keys | Chunked load jobs per product line |
| Single graph for demo catalog | Region-based read replicas |

---

## 6. Configuration knobs

| Setting | Default | Meaning |
|---------|---------|---------|
| `cache_ttl_ontology_seconds` | 300 | Schema cache TTL |
| `cache_ttl_subgraph_seconds` | 60 | Product graph cache TTL |
| `cache_maxsize_subgraph` | 128 | Max product subgraphs in memory |
| `etl_connector_max_workers` | 4 | Parallel connector fetches |
| `etl_product_batch_size` | 0 | Logical product partition size for lineage (`0` = one partition) |
| `neo4j_max_connection_pool_size` | 50 | Bolt pool size |
| `neo4j_connection_acquisition_timeout` | 30 | Pool acquire timeout (s) |
| `default_tenant_id` | `default` | Tenant when `X-Tenant-Id` absent |
| `rate_limit_per_minute` | 60 | Diagnose limiter capacity |
| `redis_url` | `""` | e.g. `redis://localhost:6379/0` — empty = memory |
| `redis_key_prefix` | `diagnostics:` | Namespace for all Redis keys |
| `max_concurrent_diagnoses` | 32 | Admission control ceiling |
| `diagnose_lease_seconds` | 120 | Redis inflight key TTL safety |

---

## 7. How to use the reusable APIs

```python
from runtime import TtlCache, parallel_map, partition_for_request, batch_items
from runtime.cache import get_named_cache, invalidate_all_named_caches

# Named shared cache (invalidated after ETL load)
cache = get_named_cache("product_subgraph", ttl_seconds=60, maxsize=128)
data = cache.get_or_set("wm-001", lambda: expensive_load("wm-001"))

# Bounded parallel I/O
results = parallel_map(connectors, lambda c: c.fetch(), max_workers=4)

# Work partitioning
for chunk in batch_items(product_ids, size=50):
    process_chunk(chunk)

# Multi-tenant request scope (logging / rate / cache namespace)
key = partition_for_request(tenant_id="acme", product_id="wm-001", asset_id="AST-1")
```

---

## 8. What else is typically required (priority order)

Not everything must be built now. Recommended enterprise backlog:

| Priority | Capability | Why | Status |
|----------|------------|-----|--------|
| **P0** | AuthN/Z (OIDC/JWT) + tenant claim | Partition keys alone are not security | Still residual (threat model) |
| **P0** | Shared rate limit + budget store (Redis) | Multi-replica correctness | **Done** (optional `REDIS_URL`) |
| **P1** | Distributed cache (Redis) for subgraphs | Multi-pod API | **Done** (`RedisTtlCache`) |
| **P1** | Concurrent diagnosis admission | Protect Neo4j under load | **Done** (`ConcurrencyLimiter`) |
| **P1** | Async job queue for ETL / bulk claims | Long-running work off request path | Admin endpoints still sync |
| **P1** | Neo4j read replicas / bolt routing | Scale GraphRAG reads | Single URI today |
| **P2** | Message bus (Kafka) for claim events | Event-driven claim learning | Out of scope for demo |
| **P2** | DB partitioning for SQLite→Postgres | Multi-writer ops data | SQLite ops store |
| **P2** | LLM semantic cache | Only if LLM path is primary | Gateway mostly inactive |
| **P3** | Graph fabric / multi-DB by OEM | Very large multi-tenant catalogs | Logical keys only |

Also already covered elsewhere (keep investing): **eval gates, guardrails, observability (OTEL), progressive delivery, provenance** — often higher ROI than premature sharding.

---

## 9. Decision summary

| Question | Answer |
|----------|--------|
| Do industry practices of caching / threading / partitioning apply? | **Yes**, at API, ETL, and multi-tenant isolation layers. |
| Were they fully implemented before? | **Partially** (rate limit, locks, driver, UI caches). |
| Did we build a reusable capability? | **Yes** — `runtime/` + wiring for ETL, graph GETs, rate keys, pool, health. |
| Should we multi-thread diagnosis itself? | **No** for default path — correctness and simplicity win. |
| What’s still needed for true multi-region enterprise? | Auth, Redis-backed limits/cache, async ETL workers, Neo4j HA/replicas — **platform**, not ontology. |

---

## 10. Related docs

- `docs/15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md` — knowledge model (not runtime)
- `docs/PIPELINE-AND-MODULE-GUIDE.md` — ETL phases
- `docs/llmops-handbook/06-llm-finops.md` — cost caching guidance
- `docs/llmops-handbook/09-llm-metric-catalog.md` — cache hit / concurrency metrics
- `security/threat-model.md` — multi-replica rate limiter residual risk
