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
| **CRM Context** | Bind customer/asset (`CUST-10042` / `AST-WM-4421`) for warranty-aware sessions |
| **Human Agent Dashboard** | Review escalated cases with full payload and provenance trail |
| **Knowledge Graph** | Browse products, failure modes, diagnostic steps |
| **Enterprise Systems** | ETL lineage batches, simulated CCaaS cases, pipeline commands |
| **REST API** | `POST /diagnose` with CRM enrichment and warranty gating |

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

Word documents in `docs/` (generate with Node.js + `docx` package):

| Doc | Topic |
|-----|-------|
| 01 | Architecture & Solution Design |
| 02 | Knowledge Graph Ontology & GraphRAG Deep Dive |
| 03 | Beginner's Guide |
| 04 | Cypher Query Walkthrough with Diagrams |
| 05 | Enterprise Implementation Roadmap |
| 06 | Architecture Diagrams (Graphviz) |
| 07 | Enterprise Pipelines & Data Lineage |

```bash
npm install
node docs/scripts/generate_documents.js
node docs/scripts/generate_pipelines_doc.js
bash docs/graphviz/render_all.sh
```

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