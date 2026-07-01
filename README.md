# WarrantyGraph — Enterprise AI Diagnostics Platform

> **Graph-native appliance warranty diagnosis** powered by **Neo4j GraphRAG**, **LangGraph**, **FastAPI**, and a **Next.js 16** enterprise UI. No LLM required for core diagnosis — reasoning runs entirely on the knowledge graph with full provenance.

---

## What it does

A customer describes an appliance problem in natural language. The platform:

1. **Matches symptoms** to the knowledge graph (Cypher + lexical scoring)
2. **Runs Bayesian inference** over failure modes (FMEA-weighted posteriors)
3. **Returns an explainable diagnosis** with ranked failure modes, confidence breakdown, parts prediction, and a provenance trail back to source systems
4. **Highlights the exact reasoning path** through the knowledge graph interactively
5. **Escalates to a human agent** when confidence is below threshold or symptoms are critical

---

## Stack (2026)

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16 · React 19 · React Flow · Tailwind CSS · React Query |
| **Backend API** | FastAPI · Uvicorn (port 8080) |
| **Agent Workflow** | LangGraph · LangChain |
| **Knowledge Graph** | Neo4j (bolt://localhost:7687) |
| **Confidence Engine** | FMEA + Bayesian inference + dominance boost |
| **Enterprise ETL** | Python pipelines: PIM / CRM / FSM / Claims → Neo4j |
| **Archived UI** | Streamlit (moved to `ui-streamlit-archive/`) |

---

## Architecture

```
Enterprise Sources (CRM · PIM · FSM · Claims)
        │
        ▼
Knowledge ETL Pipeline ──► Ontology Builder ──► Neo4j Knowledge Graph
                                                       │
                              FMEA / Bayesian ◄────────┘
                              Reliability Engine
                                     │
Customer / Agent UI ◄── LangGraph Agent ◄── GraphRAG (Cypher + lexical match)
  (Next.js :3000)              │
                        Case Management
                        Warranty Gate
                        REST API (:8080)
```

**Diagnosis path:** `detect → diagnose → score → format → escalate?`

---

## Quick Start

### Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python 3.12+ | `python -m venv venv && source venv/bin/activate` |
| Node.js 18+ | For Next.js frontend |
| Docker | Neo4j container on ports 7474 / 7687 |
| Ports free | 3000 (UI), 8080 (API), 7474/7687 (Neo4j) |

### One-command restart (recommended)

```bash
cd diagnostic-chatbot
source venv/bin/activate
./restart-all.sh
```

Kills stale processes, clears the Next.js build cache, starts FastAPI and the Next.js dev server, and verifies all three services are healthy.

### Manual start

```bash
# Terminal 1 — API
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8080

# Terminal 2 — UI
cd frontend
npm install        # first time only
npm run dev        # http://localhost:3000
```

### First run (populate graph)

```bash
source venv/bin/activate
pip install -r requirements.txt
python graph/populate_graph.py          # loads 13 products into Neo4j
```

### Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| **Next.js UI** | http://localhost:3000 | Primary interface |
| **API docs** | http://localhost:8080/docs | FastAPI Swagger |
| **API health** | http://localhost:8080/health | `{"status":"ok","neo4j":true}` |
| **Neo4j Browser** | http://localhost:7474 | `neo4j` / `password` |

---

## UI Features (Next.js Frontend)

### Diagnosis Chat
- Describe appliance problems in natural language
- Structured diagnosis card with:
  - **Recommendation strength badge** — `Strong / Moderate / Weak` (Bayesian dominance)
  - **3-tile confidence breakdown** — Posterior % · Graph Link % · Text Match % with explanations
  - Ranked failure modes with FMEA confidence scores
  - Provenance trail (source system → entity → record ID)
  - `🔍 Explore Exact Path` — jumps to Knowledge Explorer with the diagnosis path highlighted

### Knowledge Explorer (Interactive Graph)
- Live graph from Neo4j — 13 OEM products, typed nodes (Product · Symptom · Failure Mode · Part · Diagnostic Step · Resolution)
- **Dagre hierarchical layout** (TB direction, automatic)
- **Diagnosis path highlight** — `applyHighlight()` overlays the reasoning path on the full graph without replacing it or re-running layout
  - Path nodes: solid fill + dynamic-color glow
  - Off-path nodes: 42% opacity (clearly dimmed, never invisible)
  - Path edges: animated emerald + drop-shadow
- **Node inspection panel** — click any node to see its ID, type, path status, and connected nodes; click connections to navigate
- **Keyboard navigation** — Arrow keys pan the viewport (80 px; Shift = 200 px)
- **Dark / Light theme** — full CSS variable token system for both themes

### Agent Cases
Escalations dashboard with claim submission and status tracking.

### Enterprise Ops
ETL pipeline lineage batches and integration connector health.

### Admin
Onboard new products, dry-run ETL, validate, approve, and promote to the knowledge graph — all through the UI.

---

## Confidence & Reliability Engine

`graph/reliability.py` — deterministic scoring, no LLM:

| Function | Purpose |
|----------|---------|
| `composite_confidence()` | Combines Bayesian posterior + graph edge strength + text match |
| `dominance_boost()` | Boosts confidence when top FM is clearly dominant (ratio ≥ 1.8×) |
| `recommendation_strength()` | Maps signal combination to `Strong / Moderate / Weak / Insufficient data` |

**Why scores look modest (e.g. 57%):**
Bayesian posteriors distribute probability across all competing failure modes. A 57% posterior with a 1.72 dominance ratio means the top diagnosis is well-supported — the `recommendation_strength` label translates the full signal to a clear decision for the user.

---

## Knowledge Graph (13 Products)

```
Asset → Product/Model/SKU
  → Symptoms + Error Codes
  → Failure Modes          (Bayesian P(fm|symptoms))
  → Troubleshooting Steps  (CONFIRMS edges)
  → Impacted Components    (BOM)
  → Parts Prediction       (REQUIRES_PART + claim precedent)
  → Warranty Policy / Claim History
```

| OEM | Model | Product ID |
|-----|-------|------------|
| Samsung | WF45T6000AW Front Load Washer | `oem-sam-wf45` |
| Samsung | DW80B7070US Smart Dishwasher | `oem-sam-dw80` |
| Samsung | RF28R7351SG French Door Refrigerator | `oem-sam-rf28` |
| LG | LDF5545ST Built-in Dishwasher | `oem-lg-ldf5545` |
| LG | WM4000HWA Front Load Washer | `oem-lg-wm4000` |
| LG | DLE3400W Electric Dryer | `oem-lg-dle3400` |
| Whirlpool | WTW5000DW Top Load Washer | `oem-whi-wtw5000` |
| Whirlpool | WFG505M0BS Gas Range | `oem-whi-wfg505` |
| Bosch | SHPM88Z75N 800 Series Dishwasher | `oem-bos-shpm88` |
| GE | JVM3160RFSS Over-the-Range Microwave | `oem-ge-jvm3160` |
| — | Front Load Washing Machine 8kg | `wm-001` |
| — | Built-in Dishwasher 12 Place Setting | `dw-001` |
| — | Convection Microwave 25L | `mw-001` |

---

## Example Queries

```
"My washing machine won't spin and water stays in the drum"
"Dishwasher leaves dishes wet and cold after the cycle"
"Microwave runs but food stays cold, and I see arcing inside"
```

**Demo CRM customers:**

| Customer | Asset | Product |
|----------|-------|---------|
| CUST-10042 (Jane Martinez) | AST-WM-4421 | wm-001 (washer) |
| CUST-10087 (Robert Chen) | AST-DW-1180 | dw-001 (dishwasher) |
| CUST-10042 | AST-MW-7702 | mw-001 (microwave) |

---

## Project Structure

```
diagnostic-chatbot/
├── frontend/                         # Next.js 16 UI (primary)
│   ├── app/
│   │   ├── page.tsx                  # All views: Chat, Cases, Explorer, Ops, Admin
│   │   ├── globals.css               # CSS token system + ReactFlow overrides
│   │   └── layout.tsx
│   └── lib/
│       ├── api.ts                    # API client
│       └── types.ts                  # TypeScript interfaces
├── api/
│   ├── main.py                       # /diagnose, /health, /graph/*, /admin/*
│   └── schemas.py
├── agents/
│   ├── diagnosis_graph.py            # LangGraph workflow
│   └── tools.py                      # Tool wrappers for agent
├── graph/
│   ├── graph_rag.py                  # GraphRAG queries + DiagnosisResult
│   ├── reliability.py                # FMEA + Bayesian confidence engine
│   ├── graph_visualization.py        # Subgraph payloads for API
│   ├── populate_graph.py             # Neo4j MERGE loader
│   ├── oem_product_catalog.py        # 13 OEM product blueprints
│   ├── parts_predictor.py
│   ├── symptom_retrieval.py
│   └── enterprise_pipeline/          # ETL: connectors / transformers / pipelines
├── integrations/
│   ├── crm_enrichment.py
│   ├── warranty_eligibility.py
│   └── case_management.py
├── simulation/mock_enterprise_apps.py  # Simulated CRM/PIM/FSM/Claims (:8090)
├── config/settings.py
├── utils/
│   ├── escalation_store.py
│   ├── lineage_store.py
│   └── persistence.py
├── data/
│   ├── enterprise_sources/           # CRM, PIM, FSM, Claims fixtures
│   └── provenance_manifest.json
├── tests/                            # 46 pytest tests
├── docs/                             # Architecture docs, C4/Graphviz diagrams
├── ui-streamlit-archive/             # Archived Streamlit UI (replaced by Next.js)
├── restart-all.sh                    # One-command service restart
├── run_demo.sh
└── run_enterprise_demo.sh
```

---

## REST API

```bash
# Health
curl http://localhost:8080/health

# Diagnose
curl -X POST http://localhost:8080/diagnose \
  -H "Content-Type: application/json" \
  -d '{"message":"washer wont spin","customer_id":"CUST-10042","asset_id":"AST-WM-4421","product_id":"wm-001"}'

# Full product graph (Knowledge Explorer)
curl http://localhost:8080/graph/product/wm-001

# Diagnosis path subgraph
curl "http://localhost:8080/graph/diagnosis-subgraph?product_id=wm-001&symptom_ids=wm-s03,wm-s01&failure_mode_id=wm-fm01"
```

Response includes: `recommendation_strength`, `posterior_dominance_ratio`, `traversed_symptom_ids`, `traversed_fm_id`, `provenance_trail[]`, `evidence[]`.

---

## Tests

```bash
source venv/bin/activate
python -m pytest -q                              # 46 tests
python -m pytest tests/test_diagnosis.py
python -m pytest tests/test_product_resolution.py
python -m pytest tests/test_enterprise_scenarios.py
```

> Tests run **without Neo4j** — `list_products()` degrades gracefully to the static
> OEM catalog when the graph is unreachable, so CI and Docker-less machines pass.

---

## Developer Setup (hooks, lint, auto-fix)

All tooling is **cross-platform (Windows / macOS / Linux) and Docker-free**.

### One-time setup after cloning

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

pre-commit install                  # commit hook (auto-fix on every commit)
pre-commit install -t pre-push      # pre-push hook (runs full test suite)

cd frontend && npm install && cd ..
```

### What the hooks do automatically

| Stage | Tool | Action |
|-------|------|--------|
| **pre-commit** | ruff | Python lint **+ auto-fix** |
| **pre-commit** | ruff-format | Python formatting |
| **pre-commit** | ESLint | Frontend lint **+ auto-fix** (`--fix`) |
| **pre-commit** | tsc | Frontend TypeScript typecheck |
| **pre-commit** | hygiene | Trailing whitespace, EOF, YAML/JSON/TOML, line endings, merge conflicts |
| **pre-push** | pytest | Full backend test suite |

Hooks **auto-fix in place** — if a commit is blocked, the files are already fixed;
just re-stage (`git add -u`) and commit again.

### Manual commands

```bash
# Python
ruff check . --fix          # lint + auto-fix
ruff format .               # format
pytest tests/ -q            # tests

# Frontend
cd frontend
npm run lint:fix            # ESLint auto-fix
npm run typecheck           # tsc --noEmit
npm run build               # production build

# Run every hook on the whole repo
pre-commit run --all-files
```

These are the **exact same checks CI runs** — passing locally means CI passes.

---

## Configuration

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_ENTERPRISE_APIS` | `true` | Simulated CRM/PIM/Claims/FSM |
| `ENABLE_PROVENANCE` | `true` | Source-system trail on diagnoses |
| `ESCALATION_CONFIDENCE_THRESHOLD` | `0.65` | Escalate below this |
| `API_PORT` | `8080` | FastAPI port |

---

## Enterprise ETL Pipelines

```bash
python -m graph.enterprise_pipeline.orchestrator
```

| # | Pipeline | Purpose |
|---|----------|---------|
| 1 | Knowledge ETL | PIM/FSM/Claims/CRM → ontology → Neo4j |
| 2 | Smoke Validation | Regression scenarios before promotion |
| 3 | Staging Promotion | Promote validated catalog to graph |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Unsafe repair advice | Graph-grounded answers + safety notes; critical symptoms force escalation |
| Low-confidence misdiagnosis | Mandatory escalation below threshold; `recommendation_strength` label |
| Unexplainable AI output | `provenance_trail` and `evidence[]` on every diagnosis; no black-box LLM |
| Stale knowledge graph | ETL smoke validation gate before graph promotion |
| Bad ETL loads | Validation pipeline blocks staging promotion on failure |

---

## Architecture Diagrams

```bash
bash docs/graphviz/render_all.sh    # renders .dot → PNG
```

See `docs/PIPELINE-AND-MODULE-GUIDE.md` for a full module-by-module reference.

---

## Assumptions

This is a design illustration on synthetic data — not a validated production system.

- **Scope:** 3 appliance families + 10 OEM models on synthetic/fixture data
- **Graph-native:** No LLM required for core diagnosis (optional for response formatting)
- **Mock integrations by default:** Real enterprise URLs configurable via `.env`
- **Local trust boundary:** Escalations stored in JSON, not a live case management system

See `docs/` document 11 for the full enterprise delivery assumptions register.
