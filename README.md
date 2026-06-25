# Enterprise Diagnostics Chatbot Demo

A production-style demo for explainable appliance diagnosis using **Neo4j GraphRAG**, **LangGraph**, and **Streamlit**.

## Architecture

```
Customer Message
      │
      ▼
LangGraph Agent (detect → diagnose → format → escalate)
      │
      ▼
GraphRAG Layer (Neo4j queries)
      │
      ▼
Knowledge Graph (Products, Symptoms, Failure Modes, Steps, Resolutions)
```

## Quick Start (One Command)

```bash
cd ~/diagnosis-chatbot-demo/diagnostic-chatbot
chmod +x run_demo.sh
./run_demo.sh
```

Opens **http://localhost:8501**

## Manual Setup

```bash
cd ~/diagnosis-chatbot-demo/diagnostic-chatbot
source venv/bin/activate

# 1. Generate data
python graph/synthetic_data_generator.py

# 2. Start Neo4j (if not running)
docker start neo4j-demo

# 3. Populate graph
python graph/populate_graph.py

# 4. Run tests
python tests/test_diagnosis.py

# 5. Launch UI
streamlit run ui/app.py
```

## Demo Features

| Tab | What it does |
|-----|--------------|
| **Customer Chatbot** | Describe problems → get graph-backed diagnosis |
| **Human Agent Dashboard** | Review escalated cases with full payload |
| **Knowledge Graph** | Browse products, failure modes, diagnostic steps |

## Example Queries

- "My washing machine won't spin and water stays in the drum"
- "Dishwasher leaves dishes wet and cold after the cycle"
- "Microwave runs but food stays cold, and I see arcing inside"

## Project Structure

```
diagnostic-chatbot/
├── config/settings.py          # Configuration
├── graph/
│   ├── synthetic_data_generator.py
│   ├── populate_graph.py
│   ├── neo4j_client.py
│   └── graph_rag.py            # GraphRAG queries
├── agents/
│   ├── diagnosis_graph.py      # LangGraph workflow
│   └── tools.py
├── ui/app.py                   # Streamlit demo
├── utils/escalation_store.py   # Human agent cases
├── tests/test_diagnosis.py     # Evaluation
└── run_demo.sh                 # One-command launcher
```

## Neo4j Browser

http://localhost:7474 — login `neo4j` / `password`

```cypher
MATCH (s:Symptom)-[r:INDICATES]->(fm:FailureMode)
RETURN s.description, fm.name, r.confidence
ORDER BY r.confidence DESC
```

## Notes

- Works **without an LLM API key** (graph-native demo mode)
- Escalates critical symptoms or low-confidence diagnoses automatically
- Optional: set `XAI_API_KEY` in `.env` for future LLM-enhanced responses