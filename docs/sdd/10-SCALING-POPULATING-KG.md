# 10 — Scaling & Populating the Knowledge Graph

**Load when:** working on graph traversal/shortest-path, high-volume scale
(cache/cluster/shard), the structured/semi/unstructured ingestion pipeline
(strong/weak resolution, SHACL validation), or Docker/CI/Kubernetes for the
graph tier.

**Companion long-form:** `docs/25-Delta-Partitioning-Concurrency-Sharding-Implementation.md`,
`docs/19-Indexes-Constraints-and-Lookup-Performance.md`,
`docs/17-Enterprise-Landscape-Pipeline-and-Topology.md`. Study Lab masterclass:
`mc-04-scaling-populating-kg`.

**Honesty tags:** `[AS-BUILT]` runs in the repo · `[REFERENCE]` correct pattern,
not live here · `[NON-CLAIM]` do not tell a buyer it is done.

---

## 1. Traversal & shortest path

| Rule | Detail |
|------|--------|
| MUST decide **unweighted vs weighted** on purpose | `shortestPath()` = fewest hops (reachability); weighted = cheapest diagnostic route. Never "Dijkstra by default". |
| MUST create a **projection before any GDS call** | GDS runs on an in-memory projection, not the live store. |
| MUST keep the **diagnose hot path** bounded + product-scoped | Index-seek product → expand product-local edges → rank in Python. Not a path search. |

**[AS-BUILT]** `graph/diagnostic_path.py` — weighted "cheapest diagnostic route"
via **`apoc.algo.dijkstra`** (APOC is already installed; no GDS needed) over a
derived `cost` property, with an automatic native `shortestPath()` fallback.
Endpoint: `GET /graph/diagnostic-route?product_id=&symptom_id=&target=step|part`.
Cost model (`ensure_route_costs`): `INDICATES`/`CONFIRMS` cost = `1 - confidence`,
`NEXT_STEP` = 1.0, `REQUIRES_PART` = `1 - probability`; also persisted at load in
`populate_graph.py`.

```bash
curl "localhost:8080/graph/diagnostic-route?product_id=wm-001&symptom_id=wm-s05&target=step"
# → {"found": true, "method": "apoc.algo.dijkstra", "total_cost": 0.1, "route": [...]}
```

**[REFERENCE]** GDS Dijkstra / Delta-Stepping / A* / Yen's require the GDS
plugin. Add a projection step and switch algorithm (Delta-Stepping) for parallel
single-source shortest paths. **[NON-CLAIM]** GDS is not installed; do not claim
Delta-Stepping shortest-path in the product.

## 2. Scaling for high volume (apply in order)

| Step | Rule | Status |
|------|------|--------|
| 1 Vertical / page cache | MUST size page cache to the working set before clustering/sharding | `[AS-BUILT]` set in compose + StatefulSet + Helm values |
| 2 Read replicas | Core-Replica cluster, **odd** cores (Raft), replicas for reads, causal bookmarks | `[REFERENCE]` `k8s/cluster/` — Enterprise; demo is single prod + staging |
| 3 Three caching layers | page cache · replica-as-cache · cache sharding; + app TTL cache + parameterized-Cypher plan reuse | app layer `[AS-BUILT]` `runtime/cache.py`; cluster layers `[REFERENCE]` |
| 4 Partition / shard | MUST exhaust vertical + replicas before sharding; property sharding keeps structure local | logical keys `[AS-BUILT]` `runtime/partitioning.py`; property/composite `[NON-CLAIM]` |
| 5 Concurrency | inside-algorithm (Delta-Stepping) vs across-request (bounded pool + admission) | `[AS-BUILT]` `runtime/concurrency.py`, `concurrency_limit.py` |
| 6 Sized topology | 3 cores + 2 replicas/region; tx-log disk ≈ 3× peak writes; dedicated heartbeat network; read/write path split | `[REFERENCE]` `k8s/cluster/` |

- MUST NOT shard before vertical + replicas are genuinely exhausted.
- MUST NOT claim causal-cluster HA or Fabric/composite shards on the community single node.
- Page-cache config: `NEO4J_server_memory_pagecache_size` (compose + StatefulSet).

## 3. Structured / semi / unstructured → graph (5 steps per source)

| Step | Rule | Code |
|------|------|------|
| 1 Structured | MERGE strong nodes on business keys after unique constraints | `[AS-BUILT]` `populate_graph.py` |
| 2 Semi-structured | APOC JSON/XML / CSV-JSONL → normalized rows | `[AS-BUILT]` `extractors/semi_structured.py` |
| 3 Unstructured | MUST **bind the LLM to the TBox** (`allowed_nodes`/`allowed_relationships`) — never free-form; MUST use the **cheapest model**, read the key **from env only**, and **check the FinOps budget before spending** | `[AS-BUILT]` regex `extractors/unstructured_text.py`; schema-bound LLM `extractors/llm_graph_extract.py` (**off unless `LLM_ENABLED`**, ChatOpenAI structured output, `LLM_EXTRACT_MODEL`=gpt-4o-mini, budget-checked); admin trigger `POST /admin/pipeline/llm-extract` |
| 4 Strong/weak resolution | MUST resolve weak (LLM/unstructured) nodes into strong (system-of-record) nodes; flag, don't silently merge | `[AS-BUILT]` `entity_resolution.py` (difflib token-sort + stem); embedding similarity `[REFERENCE]` |
| 5 Validate | MUST shape-validate ABox before promote (min-cardinality, disjointness, link integrity); failures → review queue | `[AS-BUILT]` `ontology_validate.py` (SHACL-inspired); external SHACL engine `[NON-CLAIM]` |

- MUST NOT let an LLM invent node/relationship types — bind to the shared TBox.
- MUST NOT auto-merge near-duplicates — `find_near_duplicates` emits warnings + `duplicate_suggestions` for review.
- Weak nodes are untrusted until resolved **and** shape-validation passes.
- MUST keep the LLM extractor **off by default** (`LLM_ENABLED=false`), read `OPENAI_API_KEY` **from env only** (never committed), bind output to the TBox via **structured output** (schema enum) **and** filter out-of-allow-list results in code, use the **cheapest model** (`LLM_EXTRACT_MODEL`), and **call `DailyCostBudget.check()` before every spend + `record()` after** (fail closed on budget). Trigger: `POST /admin/pipeline/llm-extract` (admin-token gated).

## 4. Docker / GitHub Actions / Kubernetes

| Tool | Job | Status |
|------|-----|--------|
| Docker | package Neo4j + pipeline code | `[AS-BUILT]` `docker/` |
| GitHub Actions | **gate** every ontology/query/prompt change pre-merge | `[AS-BUILT]` `ci.yml`, `cd.yml`, `eval-nightly.yml`, **`ontology-validation.yml`** |
| Kubernetes | run core as StatefulSet + ingestion CronJob | `[AS-BUILT]` `k8s/base/` (single node); cluster `[REFERENCE]` `k8s/cluster/` |

- MUST run a **merge-blocking ontology gate**: `scripts/validate_ontology_ci.py`
  (TBox Turtle syntax via rdflib + TBox consistency + ABox shape validation) →
  `.github/workflows/ontology-validation.yml`.
- MUST deploy core Neo4j as a **StatefulSet** (stable identity + per-pod PVC for Raft), never a Deployment.
- MUST run scheduled ingestion as a **CronJob** (`k8s/base/etl-cronjob.yaml`), not a CI runner reaching into prod.
- SHOULD isolate the graph tier with a **NetworkPolicy** (`k8s/base/neo4j-networkpolicy.yaml`; cluster heartbeat variant in `k8s/cluster/`) — requires an enforcing CNI.
- Cluster path (`k8s/cluster/`): Neo4j **Enterprise license** + ≥3 nodes are hard blockers — prefer the official **Helm chart / Operator** (`values-neo4j-helm.yaml`).

## 5. Exit checklist

- [ ] Weighted route endpoint answers (APOC) with native fallback; `total_cost`/`route` returned
- [ ] `ensure_route_costs` idempotent; costs also set at load
- [ ] Entity resolver flags near-duplicates as review suggestions (no auto-merge)
- [ ] Shape validation runs before promote; LLM extractor bound to TBox and OFF by default
- [ ] LLM extractor uses cheapest model, key-from-env, structured-output + code allow-list filter, and **budget check before spend**; admin endpoint gated
- [ ] `ontology-validation.yml` gate green (Turtle + consistency + ABox)
- [ ] Page-cache configured; NetworkPolicy applied; cluster manifests tagged REFERENCE with blockers
- [ ] `AS_BUILT.md` updated; non-claims (GDS shortest-path, cluster HA, Fabric, embedding merge, external SHACL) preserved

## 6. Anti-patterns (see `NEVER.md`)

GDS call without a projection · shard-before-vertical · unbound LLM extraction ·
silent weak-node merge · claiming cluster HA / Fabric on community single node ·
calling `/metrics`-style "we have a NetworkPolicy" without an enforcing CNI ·
"Dijkstra by default" without choosing weighted vs unweighted.
