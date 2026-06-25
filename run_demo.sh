#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

USE_ENTERPRISE="${USE_ENTERPRISE:-false}"

echo "=== Step 1: Check Neo4j ==="
if ! docker ps --format '{{.Names}}' | grep -q neo4j-demo; then
  echo "Starting neo4j-demo container..."
  docker start neo4j-demo 2>/dev/null || docker run -d \
    --name neo4j-demo \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    neo4j:latest
  sleep 8
fi

if [[ "$USE_ENTERPRISE" == "true" ]]; then
  echo ""
  echo "=== Step 2: Enterprise pipeline mode ==="
  if ! curl -sf "http://localhost:8090/health" >/dev/null 2>&1; then
    echo "Starting mock enterprise APIs on port 8090..."
    python -m simulation.mock_enterprise_apps &
    MOCK_PID=$!
    sleep 2
    trap 'kill $MOCK_PID 2>/dev/null || true' EXIT INT TERM
  fi
  python -m graph.enterprise_pipeline.orchestrator
else
  echo ""
  echo "=== Step 2: Generate synthetic data (quick demo mode) ==="
  python graph/synthetic_data_generator.py

  echo ""
  echo "=== Step 3: Populate knowledge graph ==="
  python graph/populate_graph.py
fi

echo ""
echo "=== Step 4: Run evaluation tests ==="
python tests/test_diagnosis.py

echo ""
echo "=== Step 5: Launch Streamlit demo ==="
echo "Opening http://localhost:8501"
echo "Tip: USE_ENTERPRISE=true ./run_demo.sh for full enterprise ETL flow"
streamlit run ui/app.py --server.headless true