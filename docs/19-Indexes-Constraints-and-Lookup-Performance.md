# Indexes, Constraints & Lookup Performance

**What this document is:** How uniqueness constraints, indexes, and related lookup structures are applied in WarrantyGraph — **what**, **where**, **when**, **how**, and **why**.

---

## 1. Overview

| Store | Mechanism | Purpose |
|-------|-----------|---------|
| **Neo4j** | Uniqueness **constraints** (create backing **indexes**) | Fast id lookup + no duplicate entities |
| **SQLite** | PRIMARY KEY + secondary indexes on `status` | Claims / escalations / cases lists |
| **App** | TTL caches (memory/Redis) | Not DB indexes — cached query results |
| **Redis** | Keyed ZSETs / strings | Rate limit, shared cache keys (not SQL indexes) |

**We do not use (today):** Neo4j full-text indexes, vector indexes, or explicit `CREATE INDEX` beyond uniqueness constraints.

**Industry “must have” list vs us (honest):** see [`24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md) §4.1 — uniqueness **AS-BUILT**; fulltext / vector **ROADMAP**.

---

## 2. Neo4j uniqueness constraints

### What

Cypher uniqueness constraints on natural keys for every major label:

```cypher
CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE
-- same pattern for Symptom, FailureMode, Part, Asset, Claim, …
```

In Neo4j 5, each uniqueness constraint implies a **unique index** on that property.

### Where (code)

| Item | Location |
|------|----------|
| Definition | `graph/populate_graph.py` → `create_constraints(tx)` |
| Call site | `populate_graph()` → `session.execute_write(create_constraints)` **before** MERGEs |

### When

| Event | Applied? |
|-------|----------|
| `python graph/populate_graph.py` | Yes, first step of load |
| ETL `run_knowledge_etl(load_neo4j=True)` | Yes |
| `run_staging_promotion()` | Yes (calls `populate_graph`) |
| Every diagnose request | **No** — constraints already exist; queries only **use** indexes |
| App startup alone (no load) | **No** — constraints appear only after a graph load |

`IF NOT EXISTS` makes re-runs safe (idempotent).

### How (what they look like)

```text
Label                 Property              Constraint type
─────────────────────────────────────────────────────────
Product               product_id            UNIQUE
Symptom               symptom_id            UNIQUE
FailureMode           failure_mode_id       UNIQUE
DiagnosticStep        step_id               UNIQUE
Part                  part_id               UNIQUE
HistoricalResolution  resolution_id         UNIQUE
Model                 model_id              UNIQUE
SKU                   sku_id                UNIQUE
Component             component_id          UNIQUE
ErrorCode             error_code_id         UNIQUE
Asset                 asset_id              UNIQUE
WarrantyPolicy        policy_id             UNIQUE
Claim                 claim_id              UNIQUE
```

In Neo4j Browser:

```cypher
SHOW CONSTRAINTS;
SHOW INDEXES;
```

### How diagnosis uses them

```cypher
-- Index seek on Product.product_id, then walk edges
MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)
```

Typical online path:

1. **Seek** product / asset / failure mode by unique id
2. **Expand** relationships (adjacency)
3. Score in Python (Bayes / TF-IDF) — not via a text index

### Why

| Without | With |
|---------|------|
| Duplicate products possible | One node per business id |
| Lookups may scan labels | Planner uses unique index |
| MERGE weaker for data quality | Safe upsert: `MERGE (p:Product {product_id: $id})` |

### Pairing with MERGE

```cypher
MERGE (p:Product {product_id: $product_id})
SET p.name = $name, ...
```

Constraints + MERGE = **idempotent ETL** and **fast runtime keys**.

---

## 3. SQLite operational indexes

### What

- **PRIMARY KEY** on `case_id` / `claim_id`
- Secondary indexes on `status` for list filters

### Where

`utils/persistence.py` → `OperationalStore._init_schema()`
DB file: `data/diagnostics.db`

### When

On **first construction** of `OperationalStore` (first escalation/claim/case write or list that opens the DB).

### How (what they look like)

```sql
CREATE TABLE escalations (
  case_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  ...
);
CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status);
CREATE INDEX IF NOT EXISTS idx_ccaas_status ON ccaas_cases(status);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claim_submissions(status);
```

### Why

Agent UI filters “open / approved / closed” without full table scans. **Not** used by GraphRAG.

---

## 4. Related: caches & Redis keys (not indexes)

| Mechanism | What | When | Why |
|-----------|------|------|-----|
| Named TTL cache | Ontology schema, product subgraphs | On GET `/graph/*`; invalidate after Neo4j load | Avoid re-querying Neo4j for hot reads |
| Redis keys | `diagnostics:cache:…`, rate-limit ZSETs | Multi-replica when `REDIS_URL` set | Shared state across API pods |

These are **application-level** lookups, not database indexes.

---

## 5. What we intentionally do *not* index

| Kind | Status | Why not (today) |
|------|--------|-----------------|
| Full-text on `Symptom.description` | Not created | Match after product is known; hybrid TF-IDF in Python |
| Vector / embedding index | Not created | Graph-first design; no embedding store |
| Rel property indexes (`confidence`) | Not created | Small graph; filter after expand |
| Composite (category + brand) | Not created | No query path that needs it yet |

If catalog scale grew large, candidates would include:

```cypher
CREATE FULLTEXT INDEX symptom_text IF NOT EXISTS
  FOR (s:Symptom) ON EACH [s.description];
```

(Not in repo today.)

---

## 6. End-to-end timeline

```text
T0  First populate_graph / promote
      → CREATE CONSTRAINT IF NOT EXISTS (×13)
      → MERGE all entities (index-backed keys)

T1  First ops DB use
      → SQLite tables + PKs + status indexes

T2  Runtime diagnose / graph GET
      → Cypher uses unique indexes for id seeks
      → Optional TTL cache hit for subgraphs

T3  Next ETL load
      → Constraints re-asserted (no-op if exist)
      → MERGE updates properties
      → invalidate_all_named_caches()
```

---

## 7. Code references

| Concern | File |
|---------|------|
| Neo4j constraints | `graph/populate_graph.py` `create_constraints` |
| Graph load | `populate_graph`, ETL, staging_promotion |
| Cypher id seeks | `graph/graph_rag.py`, `parts_predictor.py`, `graph_visualization.py` |
| SQLite indexes | `utils/persistence.py` |
| Cache invalidation | `runtime/cache.py`, knowledge_etl after load |

---

*Linked from full encyclopedia, multi-volume Vol 05/01, and interview guide.*
