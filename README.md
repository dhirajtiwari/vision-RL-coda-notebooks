# Enterprise Diagnostics GraphRAG Platform

A production-style demo for **explainable appliance warranty diagnosis** using **Neo4j GraphRAG**, **LangGraph**, **enterprise ETL pipelines**, and **Streamlit**.

The platform simulates how a manufacturer would integrate CRM, PIM, FSM, and Claims systems into a knowledge graph, run diagnosis with full provenance, and hand off escalations to human agents.

## Architecture

```
Enterprise Sources (CRM · PIM · FSM · Claims)
        │
        ▼
Knowledge ETL Pipeline ──► Ontology Builder ──► Neo4j Knowledge Graph
        │                                              │
        ▼                                              ▼
Lineage Audit Log                              GraphRAG Layer
                                                       │
Customer / Agent UI ◄── LangGraph Agent ◄─────────────┘
        │
        ▼
Case Management (escalations) · Warranty Gate · REST API
```

**Runtime flow:** Customer message → LangGraph (`detect → diagnose → format → escalate`) → GraphRAG Cypher queries → ranked failure modes with provenance trail → optional CRM enrichment and warranty check → human agent dashboard on escalation.

## Prerequisites

| Requirement | Version / Notes |
|-------------|-----------------|
| **Python** | 3.12+ (venv recommended) |
| **Docker** | Running daemon; used for Neo4j (`neo4j-demo` container on ports 7474/7687) |
| **Node.js** | 18+ (optional — only for regenerating Word docs in `docs/`) |
| **Disk** | ~2 GB free (Neo4j image, Python packages, generated data) |
| **Ports** | 7474, 7687, 8080, 8090, 8501 available locally |
| **LLM API key** | Not required — demo runs in graph-native mode |

**Before first run:**

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; defaults work for local demo
```

## Dependencies

### Runtime (Python)

| Package | Role |
|---------|------|
| `neo4j` | Bolt driver for knowledge graph queries |
| `langgraph`, `langchain` | Agent workflow orchestration |
| `pydantic`, `pydantic-settings` | Ontology validation and configuration |
| `streamlit` | Demo UI (customer chat, agent dashboard) |
| `fastapi`, `uvicorn` | Diagnostics REST API |
| `httpx` | Enterprise connector HTTP calls |
| `pandas` | Data transforms in ETL pipelines |

### Infrastructure

| Service | Default | Purpose |
|---------|---------|---------|
| **Neo4j** | `bolt://localhost:7687` | Knowledge graph store |
| **Mock Enterprise APIs** | `http://localhost:8090` | Simulated CRM, PIM, FSM, Claims |
| **Diagnostics API** | `http://localhost:8080` | `POST /diagnose`, lineage endpoints |
| **Streamlit** | `http://localhost:8501` | Interactive demo |

### Documentation tooling (optional)

```bash
npm install   # docx package for Word doc generation
```

## Assumptions

> **Enterprise delivery:** Document **11** (`11-Enterprise-Delivery-Assumptions-Dependencies-and-Open-Questions.docx`) is the authoritative register of program-level assumptions, client unknowns, and mandatory dependencies. **Nothing is validated today** — including this demo. The demo is a design illustration on synthetic data; it does not confirm architecture, accuracy, integrations, or roadmap feasibility. Documents 01, 05, and 10 are hypothetical reference designs for discussion only.

**Local demo assumptions:**

- **Demo scope:** Three appliance families (washer, dishwasher, microwave) with synthetic or fixture-based enterprise data — not a production catalog.
- **Graph-native diagnosis:** Reasoning uses Neo4j Cypher and lexical symptom matching; no LLM is required for core diagnosis.
- **Mock integrations by default:** `USE_MOCK_ENTERPRISE_APIS=true` serves CRM/PIM/Claims/FSM from local fixtures unless real URLs are set in `.env`.
- **Single Neo4j instance:** Staging and production share one database in the demo; production would separate instances.
- **Escalation threshold:** Default 65% confidence (`ESCALATION_CONFIDENCE_THRESHOLD`); critical symptoms always escalate regardless of score.
- **Provenance enabled:** ETL attaches source-system metadata when `ENABLE_PROVENANCE=true`.
- **Local trust boundary:** Demo stores escalations and cases in local JSON files, not a live case management system.

## Risk Mitigation

| Risk | Mitigation in this platform |
|------|----------------------------|
| **Unsafe repair advice** | Answers grounded in graph data with safety notes; critical symptoms force human escalation |
| **Low-confidence misdiagnosis** | Mandatory escalation below confidence threshold; multi-symptom dilution demonstrated in tests |
| **Stale knowledge graph** | Enterprise ETL pipelines with smoke validation gate before graph promotion |
| **Unexplainable AI output** | `provenance_trail` and `evidence[]` on every diagnosis; no black-box LLM in demo path |
| **Invalid warranty claims** | CRM asset binding + warranty eligibility gate before diagnosis proceeds |
| **Bad ETL loads** | Smoke validation pipeline blocks staging promotion on regression failure |
| **Integration failures** | Connectors fall back to local fixtures; health checks on mock and REST APIs |
| **PII in knowledge graph** | Neo4j holds product/diagnostic knowledge only; customer context fetched at runtime from CRM |

## Quick Start

### Option A — Full enterprise demo (recommended)

Starts mock enterprise APIs, runs all ETL pipelines, REST API, and Streamlit UI:

```bash
cd diagnostic-chatbot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
chmod +x run_enterprise_demo.sh
./run_enterprise_demo.sh
```

| Service | URL |
|---------|-----|
| Streamlit UI | http://localhost:8501 |
| Diagnostics REST API | http://localhost:8080/docs |
| Mock Enterprise APIs | http://localhost:8090/docs |
| Neo4j Browser | http://localhost:7474 (`neo4j` / `password`) |

### Option B — Quick demo (synthetic data)

```bash
chmod +x run_demo.sh
./run_demo.sh
```

### Option C — Quick demo with enterprise ETL

```bash
USE_ENTERPRISE=true ./run_demo.sh
```

## Demo Features

| Tab / Surface | What it does |
|---------------|--------------|
| **Customer Chatbot** | Describe problems → graph-backed diagnosis with provenance |
| **Diagnosis Graph (interactive)** | Force-directed subgraph per chat answer — same pattern as Neo4j Browser tutorials |
| **CRM Context** | Bind customer/asset (`CUST-10042` / `AST-WM-4421`) for warranty-aware sessions |
| **Human Agent Dashboard** | Review escalated cases with full payload and provenance trail |
| **Knowledge Graph** | ER ontology diagram, interactive product graphs, Cypher Explorer |
| **Enterprise Systems** | ETL lineage batches, simulated CCaaS cases, pipeline commands |
| **REST API** | `POST /diagnose`, `GET /graph/ontology`, `GET /graph/product/{id}` |

## Example Queries

- "My washing machine won't spin and water stays in the drum"
- "Dishwasher leaves dishes wet and cold after the cycle"
- "Microwave runs but food stays cold, and I see arcing inside"

**CRM demo customers** (from `data/enterprise_sources/crm_assets.json`):

| Customer | Asset | Product |
|----------|-------|---------|
| CUST-10042 (Jane Martinez) | AST-WM-4421 | wm-001 (washer) |
| CUST-10087 (Robert Chen) | AST-DW-1180 | dw-001 (dishwasher) |
| CUST-10042 | AST-MW-7702 | mw-001 (microwave) |

## Project Structure

```
diagnostic-chatbot/
├── api/                          # REST API (FastAPI)
│   ├── main.py                   # /diagnose, /health, /lineage/batches
│   └── schemas.py
├── agents/
│   ├── diagnosis_graph.py        # LangGraph workflow
│   └── tools.py
├── config/settings.py            # Environment + enterprise URLs
├── graph/
│   ├── graph_rag.py              # GraphRAG queries + provenance trail
│   ├── graph_visualization.py    # Interactive subgraph payloads + PyVis renderer
│   ├── populate_graph.py         # Neo4j loader (MERGE + provenance)
│   ├── provenance.py             # Provenance models
│   ├── neo4j_client.py
│   ├── synthetic_data_generator.py
│   └── enterprise_pipeline/      # ETL pipelines
│       ├── orchestrator.py       # Pipeline runner
│       ├── connectors/           # PIM, FSM, Claims, CRM
│       ├── transformers/         # OntologyBuilder
│       └── pipelines/            # knowledge_etl, smoke_validation, staging_promotion
├── integrations/
│   ├── crm_enrichment.py         # Runtime CRM session binding
│   ├── warranty_eligibility.py   # Warranty gate
│   └── case_management.py        # CCaaS handoff
├── simulation/
│   └── mock_enterprise_apps.py   # Mock CRM/PIM/Claims/FSM (:8090)
├── ui/app.py                     # Streamlit demo (4 tabs)
├── utils/
│   ├── escalation_store.py       # Human agent cases
│   └── lineage_store.py          # ETL batch audit log
├── data/
│   ├── enterprise_sources/       # CRM, PIM, FSM, Claims fixtures
│   ├── enterprise_knowledge_catalog.json
│   └── provenance_manifest.json
├── tests/                        # Diagnosis, enterprise, pipeline, API tests
├── docs/                         # Architecture docs + Graphviz diagrams
├── run_demo.sh                   # Quick launcher
└── run_enterprise_demo.sh        # Full enterprise launcher
```

## Enterprise Pipelines

Three pipelines run in order via the orchestrator:

```bash
python -m graph.enterprise_pipeline.orchestrator
```

| # | Pipeline | Purpose |
|---|----------|---------|
| 1 | **Knowledge ETL** | Extract from PIM/FSM/Claims/CRM → build ontology → load Neo4j |
| 2 | **Smoke Validation** | Run regression scenarios before promotion |
| 3 | **Staging Promotion** | Promote validated catalog to Neo4j |

Lineage batches are logged to `data/lineage/etl_batches.jsonl` (gitignored at runtime).

## REST API

```bash
python -m api.main
# or: uvicorn api.main:app --port 8080
```

```bash
curl -X POST http://localhost:8080/diagnose \
  -H "Content-Type: application/json" \
  -d '{"message":"washer won'\''t spin","customer_id":"CUST-10042","asset_id":"AST-WM-4421"}'
```

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_ENTERPRISE_APIS` | `true` | Use simulated CRM/PIM/Claims/FSM on :8090 |
| `MOCK_ENTERPRISE_API_URL` | `http://localhost:8090` | Mock enterprise base URL |
| `ENABLE_PROVENANCE` | `true` | Attach source-system trail to diagnoses |
| `ESCALATION_CONFIDENCE_THRESHOLD` | `0.65` | Escalate below this confidence |
| `API_PORT` | `8080` | Diagnostics REST API port |

## Tests

```bash
python tests/test_diagnosis.py
python tests/test_enterprise_scenarios.py
python tests/test_enterprise_scenarios.py --smoke
python tests/test_pipeline_integration.py
python tests/test_api.py
```

## Documentation

Word documents in `docs/` (generate with Node.js + `docx` package). Each document includes **prerequisites**, **dependencies**, **assumptions**, and **risk mitigation** where applicable:

| Doc | Topic |
|-----|-------|
| 01 | Architecture & Solution Design |
| 02 | Knowledge Graph Ontology & GraphRAG Deep Dive |
| 03 | Beginner's Guide |
| 04 | Cypher Query Walkthrough with Diagrams |
| 05 | Enterprise Implementation Roadmap |
| 06 | Architecture Diagrams (Graphviz) |
| 07 | Enterprise Pipelines & Data Lineage |
| 08 | Customer Interaction Scripts & Presentation Runbook |
| 09 | Live Diagnostic Session Technical Walkthrough |
| 10 | Production Pipelines & Phased Roadmap |
| **11** | **Enterprise Delivery Assumptions, Dependencies & Open Questions** |
| **12** | **Solution Approach & Delivery Methodology** |

**Executive proposal deck (client-facing):**

`docs/Enterprise-Warranty-Diagnostics-Executive-Proposal.pptx` — generate with:

```bash
npm install
node docs/scripts/generate_executive_presentation.js
node docs/scripts/generate_documents.js
node docs/scripts/generate_implementation_plan.js
node docs/scripts/generate_assumptions_doc.js
node docs/scripts/generate_methodology_doc.js
node docs/scripts/generate_graph_visualization_guide_doc.js
node docs/scripts/generate_warranty_ontology_doc.js
node docs/scripts/generate_pipelines_doc.js
bash docs/graphviz/render_all.sh
```

## Graph Visualization

The Streamlit UI embeds **interactive force-directed graphs** (PyVis) — the same mental model as Neo4j Browser / Bloom tutorials:

| View | Where |
|------|--------|
| ER ontology schema | Knowledge Graph → **Ontology (ER Diagram)** |
| Full product neighborhood | Knowledge Graph → **Product Graph** |
| Query-driven subgraph | Knowledge Graph → **Cypher Explorer** |
| Per-chat diagnosis path | Customer Chatbot → **Diagnosis Graph** expander |

REST endpoints return `{nodes, edges}` for custom portals: `GET /graph/ontology`, `GET /graph/product/{product_id}`, `GET /graph/diagnosis-subgraph`.

See **Document 13** (graph visualization) and **Document 14** (`14-Enterprise-Warranty-Diagnosis-Ontology-and-Industry-Alignment.docx`) for the full warranty-claims chain, parts predictor design, and industry research alignment.

## Warranty Diagnosis Chain (Enterprise Ontology)

```
Asset (serial) → Product / Model / SKU
    → Symptoms + Error codes
    → Failure modes (diagnosis)
    → Troubleshooting steps (CONFIRMS)
    → Impacted components (BOM)
    → Predicted parts (REQUIRES_PART + SKU fit + claim precedent)
    → Warranty policy / claim history
```

Bind a CRM asset in the chat UI to enable model/SKU-scoped parts prediction. Reload graph after updates: `python graph/populate_graph.py`.

## Enterprise OEM Product Catalog

| OEM | Model | Product ID | Public sources |
|-----|-------|------------|----------------|
| Samsung | WF45T6000AW | `oem-sam-wf45` | Samsung support (UE, 4E, 5E, spin troubleshooting) |
| LG | LDF5545ST | `oem-lg-ldf5545` | LG dishwasher error code list (OE, IE, HE, AE) |
| Whirlpool | WTW5000DW | `oem-whi-wtw5000` | Whirlpool top-load diagnostic |
| Bosch | SHPM88Z75N | `oem-bos-shpm88` | Bosch E24/E01 dishwasher codes |
| GE | JVM3160RFSS | `oem-ge-jvm3160` | GE OTR microwave service |

| LG | WM4000HWA Washer | `oem-lg-wm4000` |
| Samsung | DW80B7070US Dishwasher | `oem-sam-dw80` |
| Samsung | RF28R7351SG Refrigerator | `oem-sam-rf28` |
| LG | DLE3400W Dryer | `oem-lg-dle3400` |
| Whirlpool | WFG505M0BS Gas Range | `oem-whi-wfg505` |

Plus 3 legacy demo products (`wm-001`, `dw-001`, `mw-001`) — **13 products total**. Each blueprint includes model/SKU, BOM components, OEM error codes, dynamic `NEXT_STEP` diagnostic trees, parts predictor links, and `oem_sources[]` URLs.

**PIM sync (ETL ingestion):**
```bash
python -m graph.synthetic_data_generator          # regenerates catalog + syncs PIM
python -m graph.enterprise_pipeline.transformers.pim_blueprint_sync
python graph/populate_graph.py
```

**Data policy:** Catalog uses publicly available OEM support documentation only. Part numbers are representative service references — validate against live PIM before production.

## Architecture Diagrams (C4 + LLD)

Rendered via `bash docs/graphviz/render_all.sh` → `docs/graphviz/rendered/png/`:

| Diagram | File | Level |
|---------|------|-------|
| System Context | `21-architecture-L1-system-context.dot` | L1 |
| Containers | `22-architecture-L2-container.dot` | L2 |
| Components | `23-architecture-L3-component.dot` | L3 |
| Code / classes | `24-architecture-L4-code.dot` | L4 |
| Diagnosis + claim sequence | `25-architecture-LLD-diagnosis-claim-sequence.dot` | LLD |
| Product blueprint ontology | `26-enterprise-product-blueprint.dot` | Ontology |

## Neo4j Browser

http://localhost:7474 — login `neo4j` / `password`

```cypher
MATCH (s:Symptom)-[r:INDICATES]->(fm:FailureMode)
RETURN s.description, fm.name, r.confidence
ORDER BY r.confidence DESC
```

## Escalation Rules

Cases escalate automatically when:

- Product cannot be detected
- Any matched symptom has `critical` severity
- Diagnosis confidence is below `ESCALATION_CONFIDENCE_THRESHOLD` (default 65%)

Example: washer multi-symptom query may rank the correct failure mode but still escalate at ~46% confidence.

## Notes

- Works **without an LLM API key** (graph-native demo mode)
- Optional: set `XAI_API_KEY` or `OPENAI_API_KEY` in `.env` for future LLM-enhanced responses
- Mock enterprise APIs simulate Salesforce CRM, PIM, FSM, and Claims for local development
- Production path: replace mock URLs with real connector credentials (see Document 05)

## License

Demo / educational use.