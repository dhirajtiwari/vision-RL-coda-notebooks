# Master This Codebase: WarrantyGraph Remote Diagnostics
### A Memorize-It, Write-It, Explain-It Guide

**Branch / product:** remote diagnostics · GraphRAG · multi-source TBox/ABox · dual Neo4j · LLMOps-ready
**Companion theory (status-tagged):** [`../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](../24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md)
**Q&A appendix (persona packs):** [`Interview-Mastery-Guide.md`](Interview-Mastery-Guide.md)
**Code truth:** [`../sdd/AS_BUILT.md`](../sdd/AS_BUILT.md)

---

## HOW TO USE THIS GUIDE

Same method as the small-agent series: **Story until you can retell it** → **annotated code once** → **Self-Quiz without looking** → **three Practice Levels** → **Final Boss**. Space it out. One module per study block.

| If you only have… | Do this |
|-------------------|---------|
| 20 minutes | Module 0 story + Module 1 elevator + lineage table |
| 1 hour | Modules 1–3 (story + TBox + ingest) |
| Half day | Modules 1–5 (add GraphRAG + LangGraph) |
| Full prep | All modules + Final Boss integrated test |

**Golden rule when speaking:** (1) plain English → (2) why it matters → (3) how *our* app does it → (4) file/path.

---

## PART 0 — THE STORY (your memory anchor)

> *"Imagine a huge parts warehouse that serves every brand of appliance. The warehouse has one printed rule book on the wall: what kinds of shelves exist — Product, Symptom, FailureMode, Part — and what kinds of arrows are allowed between them. That rule book almost never changes. Every night, trucks arrive with new facts about specific machines: this espresso model has symptom E05, it often means boiler NTC failure, here’s the part number. Workers never rewrite the rule book when a new SKU shows up — they only shelve new boxes under the existing labels. Before anything reaches the customer-facing aisle, a checker with a clipboard verifies the boxes aren’t missing links. Customers never walk into the staging aisle; they only shop the production floor. When a customer says ‘not heating,’ a specialist doesn’t invent a story — they walk the labeled paths, multiply likelihoods like a careful doctor, and only then speak."*

### One-sentence version

**“Shared TBox once; multi-source ABox in; shape-check; promote staging→production; deterministic GraphRAG + Bayes out.”**

### What this project is *not* (important lineage contrast)

Many tutorial agents evolve like this:

| Version | Tool behavior | Determinism |
|---------|---------------|-------------|
| Toy | Python `if` domain logic | Low |
| Graph-only | Hardcoded Cypher in one tool | High |
| “Smart Cypher” | Second LLM *writes* Cypher | Medium |

**This repo sits on a different engineering bet:**

| | Tutorial “smart Cypher” agent | **WarrantyGraph (this repo)** |
|--|-------------------------------|-------------------------------|
| Domain logic | LLM-generated Cypher | **Fixed, parameterized Cypher** + Python ranking |
| Flexibility | High | Medium (schema + packs grow ABox) |
| Determinism | Medium | **High** (same input → same ranking) |
| Audit | Hard (query invents labels) | **Provenance + typed edges** |
| LLM role | Writes queries | **Optional wording only** (`llm_enabled=false`) |
| Skeleton | State → nodes → compile | **Same idea:** LangGraph nodes wrap GraphRAG tools |

**Lock this in:** we upgraded *knowledge engineering and platform* (TBox/ABox, dual graph, control plane, LLMOps), not “let the LLM invent MATCH clauses.” If an interviewer confuses you with the smart-Cypher tutorial, correct them with this table.

### The one pattern that stays stable

| Stable outer skeleton | Evolving inner guts |
|-----------------------|---------------------|
| API → service → LangGraph nodes → tools | How packs are validated, caches, guardrails, connectors |
| GraphRAG Cypher templates + Bayes | Richer ABox, better priors, more products |
| Dual promote discipline | More pipelines, smoke scenarios |

---

# MODULE 1 — The whole system in one pass

## PART 1A — Story beats (memorize order)

| # | Beat | Plain English | Code / path |
|---|------|---------------|-------------|
| 1 | Sources | PIM, FSM, claims, CRM, bulletins, manuals | `data/`, connectors |
| 2 | Build ABox | Map fields → shared classes | `OntologyBuilder` |
| 3 | Validate | Clipboard check vs TBox shapes | `ontology_validate.py` |
| 4 | Materialize | Catalog JSON upsert (selection-scoped) | control plane |
| 5 | Promote | MERGE staging then production Neo4j | `promote_graph` |
| 6 | Diagnose | Resolve product → match → rank → steps/parts | `graph_rag.py` |
| 7 | Orchestrate | detect → diagnose → format → escalate | `diagnosis_graph.py` |
| 8 | Serve | FastAPI + Next UI; optional Redis | `api/`, `runtime/` |

## PART 1B — Self-quiz (no looking)

1. Say the one-sentence version three times out loud.
2. Name four things that are **ABox** and two that are **TBox**.
3. Why does chat never read the staging Bolt port?
4. Is the primary reasoner an LLM? Where does ranking live?
5. What stays stable when we add product `esp-001` — skeleton or schema language?

## PART 1C — Practice

**Level 1:** Fill blanks:
`Sources → ____ → Validate ____ → Materialize → Promote ____ → ____ → LangGraph → API`

**Level 2:** Draw the 8 beats from memory with one file name each.

**Level 3:** 90-second oral pitch using only the warehouse story metaphors.

## PART 1D — Common mistakes

- Calling every JSON file “the ontology” (sources ≠ TBox).
- Saying “we generate Cypher with GPT” (we do **not**).
- Forgetting dual graph when describing “how knowledge goes live.”

---

# MODULE 2 — TBox / ABox (the contract)

## PART 0 — Story

> *"The rule book on the wall is the TBox. The boxes on the shelves are the ABox. When BrewBar espresso arrives, nobody prints a new rule book titled ‘espresso ontology.’ They put espresso symptoms on the Symptom shelf and espresso failure modes on the FailureMode shelf."*

| Term | Full name | Origin | Our equivalent |
|------|-----------|--------|----------------|
| **TBox** | Terminological Box | Description Logic → OWL | `CLASSES` / properties / `warranty-diagnosis-schema.ttl` |
| **ABox** | Assertional Box | Individuals + facts | Catalog + Neo4j for `wm-001`, `esp-001`, … |

**Schema vs data** is the same split as SQL `CREATE TABLE` vs `INSERT`.

### What changed when multi-source onboarding landed

| # | Change | Why |
|---|--------|-----|
| 1 | Explicit **shared TBox** in code + export | One vocabulary for all products |
| 2 | Product packs = **ABox inputs** only | Scale to many SKUs without schema explosion |
| 3 | **Shape validation** before promote | Bad packs never hit production diagnosis |
| 4 | `tbox_extension` candidates | Unknown *kinds* need humans, not silent invent |
| 5 | CI `test_multi_source_tbox_abox` | Locks the contract |

## PART 1 — Annotated fragments (real repo)

```python
# ============================================================
# BEAT: TBox inventory (rule book summary for Admin / API)
# File: graph/enterprise_pipeline/ontology_validate.py
# ============================================================
def tbox_summary() -> dict[str, Any]:
    return {
        "build_order": [
            "1. Define / freeze domain TBox once",
            "2. Onboard NEW product = ABox under existing classes",
            "3. Only if NEW *types* → extend TBox (rare)",
            "4. Validate ABox against TBox + shapes",
            "5. Materialize → promote → optional RDF export",
        ],
        "new_vs_existing": {
            # A new SKU is almost never a new OWL language
            "new_product": "Build instance pack typed by domain TBox, then validate.",
            "tbox_extension": "Only when introducing a new class/property kind.",
        },
        # CLASSES / OBJECT_PROPERTIES imported from rdf_ontology_export
    }
```

```python
# ============================================================
# BEAT: shapes — closed-world quality (SHACL-inspired, not HermiT)
# Same file: ontology_validate.py
# ============================================================
ALLOWED_LIST_KEYS = {
    "symptoms": "Symptom",
    "failure_modes": "FailureMode",
    "diagnostic_steps": "DiagnosticStep",
    # ... parts, components, error_codes, claims, skus
}

MIN_SYMPTOMS = 1
MIN_FAILURE_MODES = 1
MIN_INDICATES_LINKS = 1  # need at least one symptom→FM evidence edge

# LINK_SPECS: every link row must point at ids that exist in the same pack
# (foreign-key style integrity — this is shapes, not open-world OWL inference)
```

```turtle
# ============================================================
# BEAT: formal export lives under docs/ontology/
# Runtime diagnose path does NOT require loading Turtle first.
# TBox ~ warranty-diagnosis-schema.ttl
# ABox sample ~ warranty-diagnosis.ttl
# Export: python -m graph.rdf_ontology_export
# ============================================================
```

### Industry sparse / formal tools (know the names; know our status)

| Tool / idea | Job | Our status |
|-------------|-----|------------|
| HermiT / Pellet / ELK | OWL reasoner | **Not in diagnose path** |
| SHACL / pyshacl | Closed-world shapes | **Lite Python shapes AS-BUILT** |
| TransE / pykeen KGE | Predict missing edges | **Out of scope v1** |
| ISO 14224 / FMEA | Reliability modeling | **Inspiration + FMEA scores AS-BUILT** |

Full status matrix: doc **24**.

## PART 2 — Self-quiz

1. Expand TBox and ABox; give one warehouse metaphor each.
2. Why is Description Logic / OWL mentioned if Neo4j is the runtime?
3. Name three checks shapes perform before promote.
4. When *would* TBox change? Give one example of something that is **not** a TBox change.
5. OWL open-world vs SHACL closed-world — which one blocks empty products?
6. Where are `CLASSES` defined in code?
7. Does adding `hmd-001` create `hmd-001.owl`? Why/why not?

## PART 3 — Progressive practice

**Level 1 — Fill blanks**

```text
TBox = ____ book; ABox = ____.
New product pack → validate with ____ → promote to ____ Neo4j.
Unknown list key → ____ candidates, never auto-merge into TBox.
```

**Level 2 — Headers only**
Write a half-page “TBox vs ABox in WarrantyGraph” using only: shared classes, packs, shapes, export, forbidden per-SKU OWL.

**Level 3 — Blank page**
From memory: table mapping Term | Origin | Our files.

## PART 4 — Common mistakes

- Treating RDF export as the thing the chat queries (chat queries **Neo4j**).
- Claiming full HermiT reasoning because we have Turtle files.
- Presenting the entire TBox dump as “what changed” after a NEW pack (highlight **ABox delta**).
- Inventing a new class per brand in an interview whiteboard.

## PART 5 — Final boss (module)

1. 60-second oral: DL origin → SQL analogy → our files → non-claims.
2. Whiteboard: pack flow with “TBox unchanged” label.
3. Adversarial: “Why not generate OWL per product?” — answer with scale + governance.

---

# MODULE 3 — Multi-source ingest & dual graph

## PART 0 — Story

> *"Trucks arrive from different cities: the catalog city (PIM), the field-service city (FSM), the claims city, the CRM city, plus messy envelopes (PDFs, CSVs). A single loading dock (OntologyBuilder) restickers everything into the warehouse language. The night shift fills the back room (staging). Only after a smoke test does a manager unlock the front room (production). Shoppers never enter the back room."*

| # | What the platform does | Why |
|---|------------------------|-----|
| 1 | Multiple **source types** | Enterprise knowledge is never one JSON |
| 2 | **Selection-scoped** materialize | Don’t rewrite the whole fleet for one SKU |
| 3 | **Validate ABox** gate | Fail closed |
| 4 | **Staging then production** | Blast-radius control |
| 5 | Cache invalidation after load | Stale subgraphs kill trust |

### Operator wizard (memorize the chant)

```text
Sources → Fetch → Select → Validate ABox → Materialize → Smoke → Approve
  → Promote staging → Promote production → (optional) reset session
```

### Pipeline registry IDs (as-built)

`structured_extract` · `semi_structured_ingest` · `unstructured_extract` · `preprocess_normalize` · `knowledge_materialize` · `smoke_validate` · `promote_graph` · `bootstrap_all` · `incremental_sync`

## PART 1 — Annotated flow (conceptual = real modules)

```text
# BEAT: control-plane spine
# graph/enterprise_pipeline/control_plane/

Connectors (PIM, FSM, Claims, CRM)
        │
        ▼
OntologyBuilder.build_catalog_payload()   # transformers/ontology_builder.py
  • Core ProductKnowledge (Pydantic)
  • Re-attach rich keys (model, SKU, CONFIRMS, components, error_codes)
  • Merge CRM assets + closed claims into ABox
        │
        ▼
enterprise_knowledge_catalog.json         # selection upsert when product_ids set
        │
        ▼
ontology_validate (shapes)                # fail closed
        │
        ▼
populate_graph MERGE → Neo4j
  staging  bolt://…:7688
  production bolt://…:7687   # diagnose + explorer READ HERE ONLY
        │
        ▼
invalidate_all_named_caches()
```

```python
# ============================================================
# BEAT: dual ports (as-built infra memory peg)
# docker/docker-compose.infra.yaml
# ============================================================
# Production Neo4j  :7687  (Browser 7474)  — chat / GraphRAG
# Staging Neo4j     :7688  (Browser 7475)  — promote-first MERGE
# Redis             :6379  — optional shared cache/rate/admission
# API               :8080
# Frontend          :3000
```

## PART 2 — Self-quiz

1. List the wizard steps in order.
2. What does “selection-scoped” protect you from?
3. Name three connector domains and one demo path under `data/`.
4. After promote, which port does `graph_rag.diagnose` use?
5. Why invalidate caches after load?
6. Fixture packs vs live SAP — what do we claim today?

## PART 3 — Practice

**Level 1:** Map each wizard step to one verb: discover / choose / check / write / test / publish.
**Level 2:** Explain staging vs production without saying port numbers, then add ports.
**Level 3:** Write a runbook paragraph for onboarding `esp-001` from cold start.

## PART 4 — Common mistakes

- “We write straight to production from the UI.” (staging exists for a reason)
- “Fetch builds the ontology schema.” (Fetch previews **ABox** delta)
- Ignoring smoke validate before approve.

## PART 5 — Final boss

Narrate a full promote of `hmd-001` including failure if shapes fail (what the operator sees conceptually).

---

# MODULE 4 — GraphRAG + FMEA + Bayesian ranking

## PART 0 — Story

> *"The specialist does not ask a poet to invent a repair. They: (1) identify the machine, (2) match the customer’s words to labeled symptoms, (3) follow INDICATES arrows, (4) weigh how common each failure is and how well steps detect it, (5) multiply likelihoods carefully, (6) hand back ranked causes, steps, and parts with a paper trail."*

| # | Stage | Mechanism |
|---|-------|-----------|
| 1 | Resolve product/asset | Context gates / CRM / message |
| 2 | Match symptoms & codes | Lexical + TF-IDF hybrid (`symptom_retrieval.py`) |
| 3 | Pull candidates | Parameterized Cypher INDICATES |
| 4 | Score | FMEA S/O/D + naive Bayes posterior |
| 5 | Act | Steps CONFIRMS, parts, claims, escalate |

**GraphRAG here means:** retrieve **typed graph evidence**, then generate the **answer structure** (LLM optional for prose only).

## PART 1 — Annotated code (real)

```python
# ============================================================
# BEAT: Cypher is FIXED and parameterized (not LLM-written)
# File: graph/graph_rag.py — rank_failure_modes
# ============================================================
result = session.run(
    """
    MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
    OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
    WHERE s.symptom_id IN $symptom_ids
    WITH fm,
         collect(DISTINCT {
           symptom_id: s.symptom_id,
           confidence: ind.confidence
         }) AS indications,
         sum(CASE WHEN ind.confidence IS NULL THEN 0 ELSE ind.confidence END)
           AS total_confidence,
         count(ind) AS link_count
    RETURN fm.failure_mode_id AS failure_mode_id,
           fm.name AS name,
           indications,
           total_confidence,
           link_count,
           [ (sv:Symptom)-[:INDICATES]->(fm) | sv.severity ] AS severities,
           size([ (fm)<-[:CONFIRMED]-(ev) | ev ]) AS evidence_count,
           size([ (ds:DiagnosticStep)-[:CONFIRMS]->(fm) | ds ]) AS step_count
    ORDER BY total_confidence DESC, link_count DESC
    """,
    product_id=product_id,
    symptom_ids=symptom_ids,
)
# NOTE: $product_id / $symptom_ids — plan-cache friendly, injection-safe
```

```python
# ============================================================
# BEAT: Bayes — domain logic in Python, grounded on graph edges
# File: graph/reliability.py
# ============================================================
def occurrence_prior(occurrence: int) -> float:
    """FMEA Occurrence 1–10 → soft prior P(fm). Relative order matters."""
    return max(int(occurrence), 1) / 10.0


def bayesian_posteriors(
    priors: Mapping[str, float],
    likelihoods: Mapping[tuple[str, str], float],
    observed_symptoms: Sequence[str],
    candidate_failure_modes: Sequence[str],
    *,
    miss_likelihood: float = DEFAULT_MISS_LIKELIHOOD,
) -> dict[str, float]:
    """
    Naive Bayes: for each FM,
      score = prior(fm) * Π P(symptom_i | fm)
    Missing INDICATES edge → miss_likelihood (sparse-data soft landing)
    Then normalize across candidates so posteriors sum to 1.
    """
    ...
```

```python
# ============================================================
# BEAT: ranking glue (conceptual order inside graph_rag)
# ============================================================
# 1) severity/occurrence/detection ratings from graph counts
# 2) prior = occurrence_prior(occ)
# 3) likelihoods[(symptom_id, fm_id)] = INDICATES.confidence
# 4) posteriors = bayesian_posteriors(...)
# 5) sort by (posterior, rpn, link_count)
```

### Sparse data (what you say when ABox is thin)

| Strategy (industry) | We do? |
|---------------------|--------|
| OWL reasoner completion | No (runtime) |
| KGE edge prediction | No (v1) |
| Soft priors + miss likelihood + escalate | **Yes** |
| Grow ABox from bulletins/claims | **Yes** |

## PART 2 — Self-quiz

1. Write the naive Bayes formula we implement in words.
2. Where does `P(symptom|fm)` come from in the graph?
3. What is `miss_likelihood` for?
4. Why parameterized Cypher instead of f-strings?
5. Name three fields on a ranked failure mode a UI might show.
6. Difference between language_confidence and graph posterior (conceptual).
7. When do we escalate?

## PART 3 — Practice

**Level 1:** Fill: `posterior ∝ ____ × Π ____`
**Level 2:** Given symptoms S1,S2 and two FMs with confidences, compute posteriors by hand (toy numbers).
**Level 3:** Explain GraphRAG vs “vector RAG only” for diagnostics in 5 sentences.

## PART 4 — Common mistakes

- Multiplying RPN into the answer as if it were probability (we rank primarily by **posterior**).
- Saying vectors are required (hybrid TF-IDF is lexical; vector index is roadmap).
- Forgetting product scope (global symptom search is wrong architecture).

## PART 5 — Final boss

Trace: *“Espresso machine not heating, customer CUST-10120.”*
Walk resolve → match → Cypher → Bayes → steps/parts → response fields.

---

# MODULE 5 — LangGraph agent skeleton

## PART 0 — Story

> *"The outer assembly line never changed shape: detect the product, run diagnosis, format the reply, handle escalation. What changed over the project life is the richness of the diagnosis tool and the platform around it — not a reinvention of the conveyor belt every sprint."*

| # | Node | Job |
|---|------|-----|
| 1 | `detect_product` | Resolve product/asset; may set context block |
| 2 | `run_diagnosis` | Call `tool_diagnose` → GraphRAG |
| 3 | `format_response` | Lift `formatted_response` |
| 4 | `handle_escalation` | Persist case if needed |

**Unchanged insight vs tutorial agents:** evolve **tool guts**, keep **graph topology** stable.

## PART 1 — Annotated code (real)

```python
# ============================================================
# BEAT 1: State — explicit fields (not only messages list)
# File: agents/diagnosis_graph.py
# ============================================================
class AgentState(TypedDict, total=False):
    user_message: str
    product_id: str | None
    asset_id: str | None
    crm_product_id: str | None
    diagnosis: dict[str, Any] | None
    response: str
    escalated: bool
    case_id: str | None
    context_block_code: str
    # ... crm_context, force_keep_context, product_name


# ============================================================
# BEAT 2: Nodes — thin wrappers; intelligence lives in graph_rag
# ============================================================
def node_detect_product(state: AgentState) -> AgentState:
    product, _, effective_asset_id, _warnings, block_code, _meta = (
        resolve_product_for_diagnosis(...)
    )
    # soft_/hard context blocks can stop a misleading diagnosis
    ...


def node_run_graph_diagnosis(state: AgentState) -> AgentState:
    payload = tool_diagnose(
        state["user_message"],
        product_id=state.get("product_id"),
        asset_id=state.get("asset_id"),
        ...
    )
    return {**state, "diagnosis": payload}


def node_format_response(state: AgentState) -> AgentState:
    diagnosis = state.get("diagnosis") or {}
    return {
        **state,
        "response": diagnosis.get("formatted_response", "Unable to generate diagnosis."),
    }


def node_handle_escalation(state: AgentState) -> AgentState:
    diagnosis = state.get("diagnosis") or {}
    if not diagnosis.get("should_escalate"):
        return {**state, "escalated": False, "case_id": None}
    case = save_escalation(state["user_message"], diagnosis, status="open")
    return {**state, "escalated": True, "case_id": case["case_id"]}


# ============================================================
# BEAT 3: Graph wiring — linear pipeline (no tool-calling LLM loop required)
# ============================================================
def build_diagnosis_graph():
    graph = StateGraph(AgentState)
    graph.add_node("detect_product", node_detect_product)
    graph.add_node("run_diagnosis", node_run_graph_diagnosis)
    graph.add_node("format_response", node_format_response)
    graph.add_node("handle_escalation", node_handle_escalation)
    graph.set_entry_point("detect_product")
    graph.add_edge("detect_product", "run_diagnosis")
    graph.add_edge("run_diagnosis", "format_response")
    graph.add_edge("format_response", "handle_escalation")
    graph.add_edge("handle_escalation", END)
    return graph.compile()
```

```python
# ============================================================
# BEAT 4: Tool facade — agents/tools.py
# ============================================================
def tool_diagnose(message: str, product_id: str | None = None, ...) -> dict:
    result = diagnose(...)  # graph.graph_rag.diagnose
    payload = {
        "ranked_failure_modes": result.ranked_failure_modes,
        "diagnostic_steps": result.diagnostic_steps,
        "predicted_parts": result.predicted_parts,
        "confidence": result.confidence,
        "provenance_trail": result.provenance_trail,
        "context_blocked": result.context_blocked,
        "formatted_response": format_diagnosis_response(result),
        # subgraph for UI highlight when not blocked
        ...
    }
    return payload
```

### Contrast: two-LLM smart Cypher tutorial vs us

| Call site | Tutorial smart agent | This repo |
|-----------|----------------------|-----------|
| Outer agent | LLM decides tool calls | **Fixed edges** between nodes |
| Inner tool | LLM writes Cypher | **Fixed Cypher** + Bayes |
| Failure mode | Bad generated Cypher | Empty match / low confidence / context block |

## PART 2 — Self-quiz

1. Name the four nodes in order.
2. Where does ranking math live — node or `reliability.py`?
3. What is `context_block_code` for?
4. Does `build_diagnosis_graph` use `bind_tools` + ReAct loop? (as-built)
5. Which fields must a diagnosis payload include for a good demo UI?
6. Why keep nodes thin?

## PART 3 — Practice

**Level 1:** Fill node names on a blank flowchart.
**Level 2:** Rewrite `build_diagnosis_graph` from memory.
**Level 3:** Explain how you would add a “warranty eligibility” node without rewriting GraphRAG.

## PART 4 — Common mistakes

- Describing a ReAct tool-calling loop that is not the default as-built path.
- Putting Cypher inside the LangGraph node files.
- Forgetting escalation side effects (`save_escalation`).

## PART 5 — Final boss

90-second oral: skeleton stability across “versions,” pointing at only `tools`/`graph_rag` as evolution sites.

---

# MODULE 6 — Runtime scale: cache, Redis, limits

## PART 0 — Story

> *"When one cashier is open, a notepad of recent answers is enough. When ten cashiers open, they must share one whiteboard (Redis) or they’ll give contradictory answers and double-charge rate limits."*

| Capability | Memory mode | Redis mode |
|------------|-------------|------------|
| Named TTL caches | Per process | Shared multi-pod |
| Rate limit | Local sliding window | Shared window |
| Admission / concurrency | Local | Shared inflight keys |
| Budget (LLM) | Local | Shared daily |

Defaults: empty `REDIS_URL` → memory (demo OK). Multi-replica → set Redis.

## PART 1 — Annotated policy

```python
# Conceptual — see runtime/cache.py, runtime/redis_client.py, docs/16

# Tier 1: application cache (AS-BUILT)
# - ontology schema GET ~ 300s
# - product subgraph GET ~ 60s
# - diagnose cache ~ 90s, max entries bounded

# Tier 2: Neo4j plan reuse (AS-BUILT discipline)
# ALWAYS parameterize: product_id: $id

# Tier 3: embedding cache (ROADMAP — we don't embed at query time)

# After ETL / promote:
invalidate_all_named_caches()  # SCAN delete by prefix when Redis
```

### Partitioning honesty

| Strategy | Status |
|----------|--------|
| Logical `tenant|product` keys | LITE AS-BUILT |
| Neo4j read replicas | ROADMAP |
| Fabric product shards | ROADMAP |
| CAP: prefer consistency | Design choice for diagnosis |

## PART 2 — Self-quiz

1. Three cache TTLs to memorize (approx).
2. What breaks if you multi-replica API with memory-only rate limits?
3. Why not cache forever after promote?
4. Is Redis required for a laptop demo?

## PART 3 — Practice

**Level 1:** Table Memory vs Redis for cache/rate/admission.
**Level 2:** Design a diagnose cache key (what must be in the key?).
**Level 3:** Draw CAP choice for warranty knowledge updates.

## PART 4 — Common mistakes

- “Redis is mandatory” (false for single-node).
- Caching across promote without invalidation.
- Claiming Fabric is implemented.

---

# MODULE 7 — LLMOps (ready vs active)

## PART 0 — Story

> *"The diagnostic engine is a careful accountant. LLMOps is the security camera, the fire extinguisher, the monthly audit, and the optional translator at the door. The accountant still does the math even if the translator is home sick."*

| Discipline | State (as-built) | Path |
|------------|------------------|------|
| Observability | ACTIVE | `observability/` |
| Guardrails | ACTIVE | `guardrails/` |
| EvalOps | ACTIVE | `evals/` |
| Gateway / PromptOps / FinOps | READY, inactive unless enabled | `gateway/`, `prompts/`, `finops/` |
| Handbook | Human recipes | `docs/llmops-handbook/` |

**Default:** `llm_enabled=false` — core remains deterministic GraphRAG.

## PART 1 — What to say in interviews

1. We treat GraphRAG quality like model quality: **golden evals + smoke in CI**.
2. Input/output/action guardrails sit on the API boundary.
3. If LLM is enabled, it is a **rewrite/gateway** concern, not free-form diagnosis.
4. Runbooks exist for PII, injection, provider outage, quality regression.

## PART 2 — Self-quiz

1. Name three ACTIVE LLMOps areas.
2. What does READY-but-inactive mean?
3. Where is the system card?
4. Why eval smoke on every PR?

## PART 3 — Practice

Explain progressive delivery / canary as **roadmap** vs what is scaffolded.

## PART 4 — Common mistakes

- “We’re an LLM app.” (We’re a **graph diagnosis platform** with LLMOps readiness.)
- Dumping the entire handbook in an interview.

---

# MODULE 8 — Sparse data & enterprise scale (doc 24 compressed)

## PART 0 — Story

> *"Empty shelves are normal. Industry either (a) invents facts with logic rules, (b) guesses edges with embeddings, or (c) borrows a richer map from standards. We mostly refuse silent invention: we validate, we soft-score, we escalate, and we onboard more ABox."*

### Three industry strategies vs us

| # | Strategy | Status here |
|---|----------|-------------|
| 1 | OWL reasoner (HermiT…) | OUT-OF-SCOPE runtime; shapes LITE |
| 2 | KGE (TransE, pykeen) | OUT-OF-SCOPE v1 |
| 3 | Ontology alignment (SAREF, BFO…) | LITE inspiration (ISO 14224/FMEA) |
| — | **Our toolkit** | Bayes + priors + miss likelihood + escalate + multi-source ABox |

### Enterprise architecture one-pager (status words)

```text
UI/API AS-BUILT
  → LangGraph + GraphRAG AS-BUILT
  → Redis L1 AS-BUILT optional
  → Neo4j prod AS-BUILT · replicas ROADMAP
  → Staging promote AS-BUILT
  → Kafka write path ROADMAP
  → Analytics layer ROADMAP
```

### Demo vs enterprise table (memorize)

| Layer | As-built | Enterprise target |
|-------|----------|-------------------|
| Ontology | Shared TBox + Python shapes | + SHACL CI + TBox semver process |
| Graph | Dual single-node Neo4j | HA / replicas / Fabric |
| Search | Cypher + TF-IDF hybrid | + fulltext + optional vectors |
| Agent | Deterministic GraphRAG | Same + optional LLM rewrite |
| Cache | Memory/Redis TTL | Redis required multi-pod + CDN |
| Sparse | Bayes + packs | + governed KGE/alignment optional |

## PART 2 — Self-quiz

1. Recite the three sparse strategies and our status each.
2. Why prefer consistency over availability for diagnosis knowledge?
3. Name two indexes we have and two we don’t.
4. What is ontology drift and how do we catch unknown keys?

## PART 5 — Final boss

Whiteboard full enterprise diagram; mark each box AS-BUILT / ROADMAP without looking at doc 24.

---

# MODULE 9 — Domain chain (whiteboard gold)

```text
Asset / Serial
  → Product / Model / SKU
  → Symptom + ErrorCode
  → FailureMode          (diagnosis)
  → DiagnosticStep       (troubleshoot)
  → Component → Part     (BOM / ship)
  → Claim / History      (precedent)
  → WarrantyPolicy       (eligibility)
```

| Business question | Graph idea |
|-------------------|------------|
| What unit? | `INSTANCE_OF`, `BOUND_TO_SKU` |
| What wrong? | `INDICATES` |
| How sure? | confidence + Bayes posterior |
| What part? | `REQUIRES_PART`, `IMPACTS_COMPONENT` |
| Covered? | policy + eligibility service |

---

# PART — GLOBAL SELF-QUIZ (integrated)

1. One-sentence system pitch.
2. TBox vs ABox with file names.
3. Wizard steps.
4. Dual ports.
5. Bayes formula + miss_likelihood.
6. Four LangGraph nodes.
7. LLM default on or off?
8. Three sparse strategies status.
9. Redis required?
10. What we never invent (per-product OWL; LLM Cypher; chat→staging).

---

# PART — GLOBAL COMMON MISTAKES

| Mistake | Fix |
|---------|-----|
| “LLM diagnoses appliances” | GraphRAG + Bayes diagnose; LLM optional wording |
| “New product = new ontology file” | New ABox under shared TBox |
| “Ontology = whatever is in Neo4j” | TBox is the contract; Neo4j is operational ABox |
| “We use HermiT / SHACL full stack” | Shapes-lite; reasoner not in path |
| “Vector DB first” | Graph-first; hybrid lexical |
| “Smart Cypher generation” | Fixed parameterized Cypher |
| “Single Neo4j write-through” | Staging then production |
| “Redis always on” | Optional single-node |
| Overclaim ISO certification | Modeling inspiration only |
| Skip provenance in the story | Always mention evidence trail |

---

# PART — FINAL BOSS TEST (whole product)

## Boss 1 — 90 seconds

Deliver the warehouse story + one-sentence pitch + “not smart-Cypher” contrast.

## Boss 2 — Blank page architecture

Draw: sources → builder → validate → staging → prod → API → LangGraph → GraphRAG → UI.
Label TBox vs ABox once on the drawing.

## Boss 3 — Execution trace

Input: *“Washer won’t drain, E21, product wm-001.”*

Narrate:

1. Which node runs first?
2. How E21 becomes evidence?
3. What Cypher shape runs (parameterized MATCH INDICATES)?
4. How posterior is computed?
5. What the user sees (FM, steps, parts, confidence)?
6. When would we escalate instead?

## Boss 4 — Adversarial architect

Answer each in ≤3 sentences:

1. Why not KGE in v1?
2. Why dual graph?
3. How do 10,000 SKUs not require 10,000 OWL files?
4. How does multi-replica API stay correct?
5. What is still demo-only (connectors)?

## Boss 5 — Write-from-memory mini specs

Without looking, write:

1. Wizard chant
2. Four LangGraph nodes
3. Demo vs enterprise table (4 rows minimum)
4. Sparse strategies status table

Compare to this guide tomorrow — drill hesitations only.

---

# THE PROJECT LINEAGE TABLE (arc at a glance)

| | Early demo mental model | Multi-source TBox/ABox platform | Full enterprise target |
|--|-------------------------|----------------------------------|------------------------|
| Knowledge entry | Hand JSON / few products | Control-plane packs + shapes | Live SoR + CDC |
| Schema story | “Ontology in Neo4j” | Explicit **TBox vs ABox** | Versioned TBox + SHACL CI |
| Diagnosis | Graph walk + scores | Same + richer ABox + gates | Same + HA + optional vectors |
| Agent | LangGraph pipeline | Stable skeleton | Stable + LLMOps active |
| Scale | Single process | Redis-ready, pools, limits | Replicas, Fabric, multi-region |
| Determinism | High | **High** (still) | High on core path |
| Flexibility | Low SKU count | High ABox growth | High + governed experiments |

If you can reconstruct this table from memory, you understand not just files, but the **trade-off**: we bought **auditability and determinism** by refusing LLM-written Cypher and per-SKU ontologies, and we scale knowledge by **ABox pipelines under a frozen TBox**.

---

# QUICK FILE MAP (cheat sheet)

| Need | Open |
|------|------|
| Agent graph | `agents/diagnosis_graph.py` |
| Tools | `agents/tools.py` |
| GraphRAG | `graph/graph_rag.py` |
| Bayes/FMEA | `graph/reliability.py` |
| Hybrid match | `graph/symptom_retrieval.py` |
| TBox export | `graph/rdf_ontology_export.py` |
| Shapes | `graph/enterprise_pipeline/ontology_validate.py` |
| ABox build | `.../transformers/ontology_builder.py` |
| Populate | `graph/populate_graph.py` |
| Runtime cache | `runtime/cache.py` |
| API | `api/main.py` |
| Settings | `config/settings.py` |
| Patterns + sparse/scale | `docs/24-…` |
| Operator TBox/ABox | `docs/22-…` |
| AS_BUILT | `docs/sdd/AS_BUILT.md` |
| Gaps | `docs/sdd/08-GAPS.md` |

---

# HOW THIS RELATES TO THE “SMART CYPHER” STUDY FORMAT YOU LIKE

You asked for the same **details of explanation**: story anchor, change table, annotated beats, quiz, progressive practice, mistakes, final boss, lineage table.

| Their tutorial focus | Your repo focus in the same format |
|----------------------|-------------------------------------|
| One file agent evolving tools | Whole platform evolving knowledge + runtime |
| Second LLM writes Cypher | **We explicitly do not** — teach the contrast |
| Name collision `graph` | Dual meaning risk: LangGraph vs Neo4j — say **compiled app** vs **driver/session** |
| try/except around generated Cypher | try/except around **enterprise I/O**; graph errors → soft diagnosis/escalate paths |

Study **one module per day**. Retell the story before sleep. Next morning: quiz first, code second.

*Last updated: 2026-07-15 — Master-This-Codebase narrative aligned to as-built WarrantyGraph.*
