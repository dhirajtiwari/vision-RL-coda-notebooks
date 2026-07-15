# TBox/ABox origin, sparse data, and enterprise-scale patterns

**Status:** Canonical reference for theory + **as-built vs target** honesty
**Audience:** architects, interview prep, knowledge stewards
**Code truth:** [`sdd/AS_BUILT.md`](sdd/AS_BUILT.md) · **Operator TBox/ABox:** [`22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`](22-TBox-ABox-Multi-Source-Onboard-Mechanism.md)
**Interview narrative:** [`interview/Master-This-Codebase.md`](interview/Master-This-Codebase.md)

> **Rule:** Every section below has a **Status** badge:
> - **AS-BUILT** — implemented in this repo
> - **LITE** — same idea, reduced form
> - **ROADMAP** — documented target, not production code
> - **OUT-OF-SCOPE** — deliberate non-goal for current product

Older `docs/01`–`14` `.docx` files may predate this language. Prefer **this file + SDD + docs/15–23**.

---

## 1. TBox / ABox — origin and universality

### 1.1 Not a project invention **[theory]**

| Term | Full name | Formal origin | This repo equivalent |
|------|-----------|---------------|----------------------|
| **TBox** | Terminological Box | Description Logic (DL, 1980s); W3C **OWL** (2004+) formalizes DL-style TBox | Shared classes/properties: `graph/rdf_ontology_export.py` (`CLASSES`, `OBJECT_PROPERTIES`), `docs/ontology/warranty-diagnosis-schema.ttl` |
| **ABox** | Assertional Box | Same tradition: individuals and facts | Product packs + catalog instances → Neo4j nodes/edges; sample TTL in `docs/ontology/warranty-diagnosis.ttl` |

**Analogy every engineer already knows:**

| Database | Knowledge representation |
|----------|---------------------------|
| `CREATE TABLE` / schema | **TBox** |
| `INSERT` rows | **ABox** |
| CHECK constraints / foreign keys | **SHACL-style shapes** (closed-world quality) |
| Query engine | Neo4j Cypher + GraphRAG (operational) |

W3C OWL is built on Description Logic. Large knowledge systems (Wikidata, enterprise KGs, clinical ontologies) use the same **schema vs instance** split even when they never say “TBox/ABox” out loud.

### 1.2 Universality across industries **[theory]**

| Domain | Schema (TBox-like) | Instances (ABox-like) |
|--------|--------------------|------------------------|
| Healthcare | SNOMED CT, FHIR resource models | Patient observations, conditions |
| Manufacturing / reliability | ISO **14224** hierarchy + failure taxonomy; IEC **81346** product aspect | Equipment tree, failure events |
| Finance | FIBO | Legal entities, instruments |
| Law | Akoma Ntoso | Specific acts/cases |
| **This product** | Product, Symptom, FailureMode, Part, … | `wm-001` symptoms, INDICATES links, assets |

We **align by modeling inspiration** (ISO 14224-style hierarchy, FMEA signals). We do **not** claim certified ISO 14224 or full SNOMED mapping.

### 1.3 How *this* platform enforces the split **[AS-BUILT]**

| Rule | Where |
|------|--------|
| Shared TBox once | `rdf_ontology_export`, `docs/ontology/*` |
| New product = ABox only | Multi-source packs under `data/pipeline_sources/` |
| Never auto-extend TBox from a pack | `scan_tbox_extension_candidates` + Admin gate |
| Shape-check before promote | `ontology_validate.py` |
| Chat reads production only | Promote dual Neo4j (`:7688` staging → `:7687` prod) |

**Sources on disk ≠ ontology built.** Sources feed instances; schema lives in the platform TBox module.

---

## 2. Sparse data — when ABox is thin

Real warranty graphs are never complete. Three industry strategies, mapped to us:

### 2.1 Deductive completion from the TBox (OWL reasoners)

**Idea:** Rules in the TBox invent new facts (e.g. `StrongIndicator ≡ Restriction on confidence ≥ 0.8`). Reasoners: HermiT, Pellet, ELK.

| Aspect | Status |
|--------|--------|
| Full OWL reasoner in diagnose path | **OUT-OF-SCOPE** (determinism + auditability) |
| SHACL / closed-world completeness | **LITE AS-BUILT** — `ontology_validate.py` (min symptoms, FMs, INDICATES, link integrity) |
| External `pyshacl` in CI | **ROADMAP (P2)** |

**Why not HermiT at runtime:** open-world inference can surprise operators; warranty answers must be **reproducible and attributable** to stored edges and scores.

### 2.2 Probabilistic graph completion (KGE embeddings)

**Idea:** TransE / RotatE / ComplEx (e.g. `pykeen`) predict missing edges:

```text
(sym_wm_s04, INDICATES, ?) → fm_wm_fm01  p=0.91
```

| Aspect | Status |
|--------|--------|
| KGE training / edge imputation | **OUT-OF-SCOPE / research** for v1 |
| Why deferred | Hard to explain to field techs; risk of silent wrong INDICATES; needs governance + evals |

**What we do instead (AS-BUILT sparse toolkit):**

| Technique | Role when data is thin |
|-----------|------------------------|
| FMEA **occurrence → prior** | Soft mass even with few claims |
| Naive **Bayes** on INDICATES likelihoods | Rank FMs from partial symptom sets |
| **Miss likelihood** for absent edges | Avoids zeroing a candidate for missing link |
| Hybrid **lexical / TF-IDF** symptom match | Customer language ≠ canonical labels |
| **Insufficient data / escalate** | Refuse confident answers when evidence is weak |
| Multi-source ABox growth | Bulletins, claims, FSM add edges over time |

### 2.3 Transfer via ontology alignment

**Idea:** Map our TBox to external standards so we inherit relations.

| External | Status |
|----------|--------|
| ISO 14224 hierarchy / failure ideas | **LITE** — modeling inspiration (Product→Component, FailureMode) |
| IEC 81346 product aspect | **LITE** — BOM/product structure |
| FMEA S/O/D + Action Priority | **AS-BUILT** — `graph/reliability.py` |
| SAREF / BFO / DOLCE / Schema.org / ISO 13584 PLIB | **ROADMAP** interoperability map only |
| `owl:equivalentClass` bridges in Turtle | **LITE** — possible in export; not runtime |

Example **target** alignment (not required for demo):

```turtle
# ROADMAP illustration — not loaded by diagnose path
wd:FailureMode owl:equivalentClass fmea:FailureMode .
```

### 2.4 Sparse-data decision table (interview one-liner)

| If interviewer asks… | Answer |
|----------------------|--------|
| “How do you fill missing edges?” | Prefer **human/SME + multi-source ETL**, not silent KGE |
| “Do you use an OWL reasoner?” | **No at runtime**; SHACL-style shapes pre-promote |
| “What if only one symptom matches?” | Bayes + miss likelihood + escalate if confidence weak |
| “How do you grow coverage?” | New ABox packs / bulletins under **same TBox** |

---

## 3. Production at scale — full enterprise architecture

### 3.1 Target landscape (industry) vs this repo

```text
┌─────────────────────────────────────────────────────────────┐
│  Customer / Field tech / Agent portal / Mobile              │  AS-BUILT: Next.js :3000
└──────────────────────────┬──────────────────────────────────┘
                           │ REST
┌──────────────────────────▼──────────────────────────────────┐
│  Diagnostic API + Admin control plane                       │  AS-BUILT: FastAPI :8080
│  LangGraph · GraphRAG · Escalation · Guardrails             │
└──────────┬───────────────────┬────────────────┬─────────────┘
           │                   │                │
    ┌──────▼──────┐     ┌──────▼──────┐  ┌──────▼──────┐
    │ L1 cache    │     │ L2 static   │  │ Graph read  │
    │ Redis/memory│     │ CDN         │  │ Neo4j prod  │
    │ AS-BUILT    │     │ ROADMAP     │  │ AS-BUILT    │
    └─────────────┘     └─────────────┘  └──────┬──────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │ Write / promote     │
                                     │ Neo4j staging       │  AS-BUILT dual graph
                                     └──────────┬──────────┘
                                                │
                          ROADMAP: Kafka → Flink → ABox writer
                          ROADMAP: analytics (DuckDB/Spark)
```

### 3.2 Layer status table

| Layer | This demo / platform | Enterprise target |
|-------|----------------------|-------------------|
| **Ontology** | Turtle export + code TBox + shape validate | Same + semver TBox + external SHACL CI |
| **Graph DB** | Neo4j Docker dual (prod 7687 / staging 7688) | Aura / causal cluster, read replicas |
| **Search** | Parameterized Cypher + hybrid TF-IDF | + fulltext + optional vector index |
| **Agent** | LangGraph fixed nodes; GraphRAG tools | Same skeleton; optional LLM rewrite only |
| **Caching** | Named TTL caches; Redis optional | Redis L1 multi-pod; CDN for static assets |
| **Ingest** | Control-plane pipelines + fixtures | Live SoR connectors + Kafka CDC |
| **Sparse data** | Bayes + shapes + multi-source ABox | + optional KGE offline + alignment |
| **Scale** | Connection pool, admission, rate limit | Replicas, Fabric/shards, multi-region |

### 3.3 Sharding and partitioning **[LITE AS-BUILT / ROADMAP]**

Neo4j does not shard like Postgres. Industry options:

| Strategy | How | This repo |
|----------|-----|-----------|
| **Vertical** | TBox rare-change store vs high-volume ABox | Logical only (code TBox + Neo4j ABox) |
| **Product-based** | Shard by product line / brand | **Logical keys** (`product_id`, tenant prefix) — **LITE** |
| **Read replicas** | Primary write, N read | **ROADMAP P1** |
| **Fabric / federation** | Route Cypher across subgraphs | **ROADMAP P3** |

Demo dual graph is **environment promotion** (staging vs production), not multi-region HA.

### 3.4 Caching — three-tier model

| Tier | Industry | This repo |
|------|----------|-----------|
| **1 Application** | Redis key = `diag:{product}:{symptoms}` | **AS-BUILT** `runtime/cache.py` — ontology 300s, subgraph 60s, diagnose ~90s; Redis when `REDIS_URL` set |
| **2 Query plan** | Parameterized Cypher so plans reuse | **AS-BUILT** — use `$params`, never string-build ids into Cypher |
| **3 Embeddings** | Precompute symptom vectors | **OUT-OF-SCOPE** today (lexical hybrid only) |

```python
# AS-BUILT policy (conceptual)
GOOD = "MATCH (p:Product {product_id: $id}) RETURN p"
BAD  = f"MATCH (p:Product {{product_id: '{id}'}}) RETURN p"  # recompile + injection risk
```

### 3.5 Fast retrieval — GraphRAG hybrid

**Industry GraphRAG:** embed query → vector candidates → graph walk → rank.

**This repo GraphRAG (AS-BUILT):**

```text
Customer text
  → resolve Product / Asset (context gates)
  → match symptoms / error codes (lexical + TF-IDF hybrid)
  → Cypher: (Symptom)-[:INDICATES]->(FailureMode)  [parameterized]
  → FMEA S/O/D + Bayesian posterior
  → DiagnosticStep CONFIRMS / parts / claims
  → provenance + optional escalate
```

LLM is **not** required for ranking. Optional LLM is wording/gateway only (`llm_enabled=false` by default).

---

## 4. Industry-wide adopted patterns

### 4.1 Index strategy

| Index type | Industry “must” | This repo |
|------------|-----------------|-----------|
| Uniqueness on business ids | Yes | **AS-BUILT** — `populate_graph` constraints on product/symptom/FM/part ids |
| Fulltext on symptom text | Common | **ROADMAP** — matching is Python hybrid after product scope |
| Vector index | Optional hybrid | **ROADMAP P3** |
| Composite product+brand | Sometimes | **ROADMAP** |

Authoritative detail: [`19-Indexes-Constraints-and-Lookup-Performance.md`](19-Indexes-Constraints-and-Lookup-Performance.md).

### 4.2 Event-driven graph updates

```text
Industry:  IoT/SoR → Kafka → stream processor → TBox validate → ABox write → confidence update
This repo: batch/control-plane ETL → OntologyBuilder → shapes → promote → invalidate caches
```

| Piece | Status |
|-------|--------|
| Multi-pipeline control plane | **AS-BUILT** |
| Live Kafka / Flink | **ROADMAP** |
| Bayesian online update of INDICATES | **ROADMAP** (claims feedback loop) |

### 4.3 Observability and ontology drift

| Risk | Mitigation | Status |
|------|------------|--------|
| Unknown entity kinds in packs | `tbox_extension` candidates + ack | **AS-BUILT** |
| Incomplete ABox | Min evidence shapes | **AS-BUILT** |
| Bad promote | Smoke scenarios + dual graph | **AS-BUILT** |
| Formal SHACL engine | `pyshacl` CI | **ROADMAP P2** |
| TBox semantic versioning | Git + export; formal semver process | **LITE** (git history) |
| Runtime quality drift | Eval smoke + nightly | **AS-BUILT** (`evals/`) |
| Ops signals | Prometheus / OTEL / runbooks | **AS-BUILT** (LLMOps pack) |

### 4.4 CAP tradeoff for diagnostic graphs

| Property | Neo4j-style enterprise | Our choice |
|----------|------------------------|------------|
| Consistency | ACID on primary writes | **Prefer consistency** of diagnostic knowledge |
| Availability | Read replicas during failover | Single-node demo; replicas **ROADMAP** |
| Partition tolerance | Causal clustering / Raft | Not multi-region yet |

**One-liner:** a **wrong diagnosis is worse than a slow one** → promote is fail-closed; chat does not read staging.

---

## 5. Demo / notebook vs enterprise production (canonical table)

| Layer | This repository (as-built) | Enterprise production target |
|-------|----------------------------|------------------------------|
| **Ontology** | Shared TBox in code + TTL export; SHACL-style Python shapes | Same TBox, versioned; external SHACL; rare TBox ADRs |
| **Graph DB** | Dual local Neo4j (staging/prod) | Cluster / Aura; read replicas; optional Fabric |
| **Search** | Cypher + hybrid TF-IDF | Cypher + fulltext + optional vectors |
| **Agent** | LangGraph fixed workflow; deterministic GraphRAG tools | Same; LLM rewrite optional behind gateway |
| **Caching** | Memory or Redis TTL named caches | Redis required multi-pod; CDN static |
| **Ingest** | Fixtures + mock connectors + Admin wizard | Live SoR + CDC/Kafka |
| **Scale** | Pool, rate limit, admission control | HA, multi-region, partitioned products |
| **Sparse data** | Bayes + priors + escalate + multi-source ABox | + offline KGE / alignment if governed |
| **Security** | Guardrails, rate limit, redaction | OIDC, tenant ACL, ZDR contracts |
| **LLMOps** | Obs, evals, guardrails active; gateway ready-inactive | Same + progressive delivery |

**Invariant across both columns:** TBox is the rare-change **contract**; ABox is the high-volume **variable**. That split is what makes caching, promote, and multi-source onboarding possible.

---

## 6. Code and doc map

| Concern | Primary path |
|---------|----------------|
| TBox classes | `graph/rdf_ontology_export.py` |
| ABox build | `graph/enterprise_pipeline/transformers/ontology_builder.py` |
| Shapes | `graph/enterprise_pipeline/ontology_validate.py` |
| Promote / dual graph | control plane `promote_graph` + `populate_graph.py` |
| GraphRAG | `graph/graph_rag.py` |
| Bayes / FMEA | `graph/reliability.py` |
| LangGraph | `agents/diagnosis_graph.py` |
| Tools | `agents/tools.py` |
| Cache / Redis | `runtime/cache.py`, `runtime/redis_client.py` |
| Operator TBox/ABox | `docs/22-…` |
| Runtime scale | `docs/16-…` |
| Indexes | `docs/19-…` |
| Ingest architecture | `docs/20-…` |
| SDD kit | `docs/sdd/*` |
| Interview story style | `docs/interview/Master-This-Codebase.md` |

---

## 7. Non-claims (do not say these are done)

- Full OWL reasoner (HermiT/Pellet) on the diagnose path
- KGE / pykeen production edge imputation
- Certified ISO 14224 / full BFO-SAREF alignment
- Neo4j Fabric multi-shard or multi-region HA
- Kafka streaming write path
- Vector index as primary retrieval
- Per-product OWL/TBox files (by design **forbidden**)
- LLM as primary diagnostic reasoner

---

## 8. Related documents

| Doc | Role |
|-----|------|
| [`22-TBox-ABox-Multi-Source-Onboard-Mechanism.md`](22-TBox-ABox-Multi-Source-Onboard-Mechanism.md) | Operator mechanism |
| [`15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md`](15-Ontology-Build-Pipeline-RDF-and-Topology-Decision.md) | Build pipeline + RDF export |
| [`16-Enterprise-Runtime-Capabilities.md`](16-Enterprise-Runtime-Capabilities.md) | Cache, concurrency, partition |
| [`17-Enterprise-Landscape-Pipeline-and-Topology.md`](17-Enterprise-Landscape-Pipeline-and-Topology.md) | End-to-end landscape |
| [`19-Indexes-Constraints-and-Lookup-Performance.md`](19-Indexes-Constraints-and-Lookup-Performance.md) | Indexes honesty |
| [`sdd/08-GAPS.md`](sdd/08-GAPS.md) | Priority roadmap |
| [`sdd/AS_BUILT.md`](sdd/AS_BUILT.md) | Code-true checklist |

*Last updated: 2026-07-15 — canonical patterns + sparse/scale honesty for WarrantyGraph / remote diagnostics.*
