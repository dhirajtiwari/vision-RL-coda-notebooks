# Pipeline & Module Guide — Blueprint to Claim

This guide explains how product ontology and the knowledge graph are created, how diagnosis runs, and how claims are processed end-to-end.

**C4 diagrams:** [`docs/c4/README.md`](c4/README.md) · **Pipeline diagrams:** 34–37 in `docs/graphviz/`.

## Do we need Entity-Relationship Diagrams (ERDs)?

**Yes — for the blueprinting approach they are essential.**

| Purpose | Diagram |
|---------|---------|
| Schema contract before coding blueprints | **34** `enterprise-blueprint-ERD.dot` |
| Per-SKU instance walkthrough | **26** `enterprise-product-blueprint.dot` |
| Legacy core schema (3-product demo) | **05** `neo4j-ontology.dot` |

ERDs answer: *What entities exist? What relationships connect Product → Symptom → FailureMode → Part → Claim?* Without them, OEM builders in `oem_product_catalog.py` and the Neo4j loader in `populate_graph.py` can drift apart.

---

## Symmetrical layer architecture

See **`35-layer-architecture-symmetric.dot`** — six balanced layers:

| Layer | Responsibility | Key modules |
|-------|----------------|-------------|
| **L6 Experience** | UI, API, dashboards | `ui/app.py`, `api/main.py` |
| **L5 Orchestration** | Agent, claims, warranty gate | `diagnosis_graph.py`, `claims_workflow.py` |
| **L4 Intelligence** | GraphRAG, trees, parts | `graph_rag.py`, `diagnostic_engine.py`, `parts_predictor.py` |
| **L3 Integration** | Enterprise connectors | `*_connector.py`, `crm_enrichment.py`, mock API |
| **L2 Knowledge Store** | Neo4j load & query | `populate_graph.py`, `neo4j_client.py` |
| **L1 Data Platform** | Blueprints, ETL, fixtures | `oem_product_catalog.py`, `orchestrator.py` |

---

## End-to-end pipeline (phases 0–5)

See **`36-end-to-end-pipeline-io.dot`** for the visual flow.

### Phase 0 — OEM blueprint authoring

| | |
|--|--|
| **Input** | Public OEM support documentation (error codes, service manuals, BOM categories) |
| **Tool** | `graph/oem_product_catalog.py` — 10 OEM product builders + 3 legacy |
| **Tool** | `graph/warranty_catalog_extensions.py` — Model, SKU, Component, Asset, Claim extensions |
| **Output** | In-memory Python dict: `products[]` with nested symptoms, failure_modes, diagnostic_steps, parts, error_codes, NEXT_STEP trees |

### Phase 1 — Fixture sync

| | |
|--|--|
| **Command** | `python -m graph.enterprise_pipeline.transformers.pim_blueprint_sync` |
| **Tool** | `graph/enterprise_pipeline/transformers/pim_blueprint_sync.py` |
| **Output** | `data/enterprise_sources/pim_catalog.json` — `{source_system, synced_at, products[]}` |
| **Output** | `data/enterprise_knowledge_catalog.json` — full catalog + assets, claims, policies |

Also triggered by `python -m graph.synthetic_data_generator` after legacy product generation.

### Phase 2 — Enterprise ETL (batch)

| | |
|--|--|
| **Command** | `python -m graph.enterprise_pipeline.orchestrator` |
| **Input fixtures** | `pim_catalog.json`, `crm_assets.json`, `claims_history.json`, `fsm_work_orders.json` |
| **Connectors** | `graph/enterprise_pipeline/connectors/{pim,crm,claims,fsm}_connector.py` |
| **Fetch mode** | HTTP `GET` to mock API `:8090` **or** `fixture_fallback` from JSON files |
| **Transform** | `ontology_builder.py` merges PIM products + FSM resolutions + closed claims |
| **Output** | `data/synthetic_diagnosis_data.json` — validated catalog with `provenance{}` |
| **Audit** | `data/lineage/etl_batches.jsonl` via `utils/lineage_store.py` |
| **Pipelines** | 1) `knowledge_etl` → 2) `smoke_validation` → 3) `staging_promotion` |

### Phase 3 — Neo4j graph load

| | |
|--|--|
| **Command** | `python graph/populate_graph.py` (also called from ETL when `load_neo4j=true`) |
| **Tool** | `graph/populate_graph.py` |
| **Input** | `synthetic_diagnosis_data.json` or `enterprise_knowledge_catalog.json` |
| **Output** | Neo4j graph (Bolt `:7687`) — nodes: Product, Symptom, FailureMode, DiagnosticStep, Part, Model, SKU, Component, ErrorCode, Asset, Claim, WarrantyPolicy, HistoricalResolution |
| **Relationships** | HAS_SYMPTOM, INDICATES, CAN_HAVE, NEXT_STEP, CONFIRMS, REQUIRES_PART, INSTANCE_OF, FOR_ASSET, USED_PART, etc. |

### Phase 4 — Runtime diagnosis

| | |
|--|--|
| **Entry** | `POST /diagnose` or Streamlit Chat → `run_diagnosis()` |
| **Input** | `message` (text), optional `product_id`, `asset_id`, `customer_id` |
| **CRM bind** | `integrations/crm_enrichment.py` — resolves asset → product, SKU, warranty status |
| **Warranty gate** | `integrations/warranty_eligibility.py` — may short-circuit if out of warranty |
| **LangGraph** | `agents/diagnosis_graph.py` — detect_product → run_diagnosis → format → escalate |
| **GraphRAG** | `graph/graph_rag.py` — token match symptoms/error codes, rank failure modes via INDICATES confidence |
| **Dynamic tree** | `graph/diagnostic_engine.py` — traverse NEXT_STEP, CONFIRMS, RULES_OUT |
| **Parts** | `graph/parts_predictor.py` — rank parts from REQUIRES_PART, BOM, SKU compatibility, claim precedent |
| **Output** | JSON `DiagnosisResult`: matched_symptoms, ranked_failure_modes, predicted_parts, diagnostic_tree, confidence, provenance_trail, graph_subgraph |

### Phase 5 — Claim processing

| | |
|--|--|
| **Submit** | `POST /claims/submit` or Streamlit Claims tab |
| **Tool** | `integrations/claims_workflow.py` → `submit_claim_from_diagnosis()` |
| **Input** | Diagnosis dict + asset_id + customer_id |
| **Warranty re-check** | `warranty_eligibility.py` with predicted parts |
| **Output (JSON)** | `data/enterprise_sources/claims_submissions.json` — claim_id, status, parts, costs, graph_evidence |
| **Output (Neo4j)** | MERGE `:Claim` with FOR_ASSET, CONFIRMED, USED_PART |
| **Approve/Deny** | `update_claim_status()` — UI buttons or `PATCH /claims/{id}/status` |

---

## Key files (detailed)

### `graph/oem_product_catalog.py`
Builds **enterprise OEM blueprints** from public documentation patterns. Each builder function (e.g. `samsung_wf45t6000aw`) returns a full product dict: symptoms, failure modes, diagnostic steps with NEXT_STEP branches, parts, error codes, components. `build_oem_enterprise_catalog()` merges 10 OEM + 3 legacy into one catalog payload.

### `graph/diagnostic_engine.py`
**Dynamic tree traversal** at runtime. Queries Neo4j for `HAS_DIAGNOSTIC_STEP`, `NEXT_STEP` edges (with conditions), and `CONFIRMS`/`RULES_OUT` links to failure modes. Returns `diagnostic_tree` used in diagnosis responses and graph visualization.

### `graph/parts_predictor.py`
**Multi-source parts ranking** for a product + failure_mode (+ optional SKU):
1. `REQUIRES_PART` direct links (highest weight)
2. `IMPACTS_COMPONENT` → `REALIZED_BY` BOM path
3. `SKU -[:COMPATIBLE_WITH]-> Part` when asset-bound
4. Historical `Claim -[:USED_PART]->` precedent boost

### `integrations/claims_workflow.py`
**Claim lifecycle**: submit from diagnosis, list/get claims, update status (approved/denied/closed). Persists to JSON store and optionally MERGEs Claim nodes in Neo4j for graph precedent in future predictions.

---

## Supporting files

| File | Role |
|------|------|
| `graph/graph_rag.py` | Core `diagnose()` — symptom matching, failure mode ranking, evidence assembly |
| `graph/graph_visualization.py` | Subgraph extraction + PyVis for UI/API `/graph/*` |
| `graph/warranty_catalog_extensions.py` | Enterprise node extensions merged into product payloads |
| `graph/neo4j_client.py` | Bolt connection pool |
| `graph/provenance.py` | Source system metadata on entities |
| `agents/diagnosis_graph.py` | LangGraph 4-node workflow |
| `agents/tools.py` | Thin wrappers: `tool_diagnose`, `tool_detect_product` |
| `api/main.py` | REST surface: diagnose, claims, graph, health, lineage |
| `ui/app.py` | Streamlit: Chat, Warranty Claims, Agent Dashboard, KG Explorer |
| `integrations/crm_enrichment.py` | Runtime CRM asset/customer binding |
| `integrations/warranty_eligibility.py` | Policy eligibility before diagnosis/claim |
| `integrations/case_management.py` | Escalation → simulated case / CCaaS target |
| `simulation/mock_enterprise_apps.py` | FastAPI mock for PIM/CRM/Claims/FSM |
| `utils/lineage_store.py` | ETL batch audit log |
| `utils/escalation_store.py` | Agent escalation queue JSON |
| `config/settings.py` | All paths, URLs, feature flags |

---

## Data file formats (quick reference)

### `pim_catalog.json`
```json
{
  "source_system": "SAP PLM / PIM (OEM blueprint sync)",
  "synced_at": "ISO-8601",
  "products": [{ "product": {...}, "symptoms": [...], "failure_modes": [...], ... }]
}
```

### `crm_assets.json`
```json
{ "customers": [...], "registered_assets": [{ "asset_id", "product_id", "serial_number", "warranty_status" }] }
```

### `claims_history.json`
```json
{ "closed_claims": [{ "claim_id", "product_id", "failure_mode_id", "part_id", "resolution" }] }
```

### `claims_submissions.json`
```json
[{ "claim_id", "status", "asset_id", "predicted_parts", "warranty_check", "graph_evidence", ... }]
```

### `synthetic_diagnosis_data.json` / `enterprise_knowledge_catalog.json`
```json
{
  "products": [{ "product", "symptoms", "failure_modes", "diagnostic_steps", "parts", ... }],
  "provenance": { "entity_id": { "source_system", "source_document_uri", ... } },
  "assets": [...], "claims": [...], "warranty_policies": [...]
}
```

---

## Commands cheat sheet

```bash
# 1. Generate/sync OEM blueprints → fixtures
python -m graph.synthetic_data_generator
python -m graph.enterprise_pipeline.transformers.pim_blueprint_sync

# 2. Load graph (local)
python graph/populate_graph.py

# 3. Full enterprise ETL pipeline
python -m graph.enterprise_pipeline.orchestrator

# 4. Render all diagrams
bash docs/graphviz/render_all.sh

# 5. View on Mac
bash docs/graphviz/view_on_mac.sh 34
```

## Diagram index (new)

| ID | File | Purpose |
|----|------|---------|
| 34 | `34-enterprise-blueprint-ERD.dot` | Full ontology ERD |
| 35 | `35-layer-architecture-symmetric.dot` | 6-layer symmetrical architecture |
| 36 | `36-end-to-end-pipeline-io.dot` | Pipeline with I/O formats |
| 37 | `37-module-catalog-by-phase.dot` | File/tool catalog by phase |