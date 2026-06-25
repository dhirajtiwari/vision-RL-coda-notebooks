#!/usr/bin/env bash
# Full enterprise demo: mock CRM/PIM/Claims/FSM APIs, ETL pipelines, REST API, Streamlit UI.
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

MOCK_PORT="${MOCK_ENTERPRISE_API_URL:-http://localhost:8090}"
MOCK_PORT="${MOCK_PORT##*:}"
MOCK_PORT="${MOCK_PORT%%/*}"
API_PORT="${API_PORT:-8080}"

cleanup() {
  echo ""
  echo "Shutting down background services..."
  [[ -n "${MOCK_PID:-}" ]] && kill "$MOCK_PID" 2>/dev/null || true
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "=== Step 1: Start Neo4j ==="
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

echo ""
echo "=== Step 2: Start mock enterprise APIs (port ${MOCK_PORT}) ==="
python -m simulation.mock_enterprise_apps &
MOCK_PID=$!
sleep 2

echo ""
echo "=== Step 3: Run enterprise ETL pipelines ==="
python -m graph.enterprise_pipeline.orchestrator

echo ""
echo "=== Step 4: Run test suites ==="
python tests/test_diagnosis.py
python tests/test_enterprise_scenarios.py --smoke
python tests/test_pipeline_integration.py
python tests/test_api.py

echo ""
echo "=== Step 5: Start Diagnostics REST API (port ${API_PORT}) ==="
python -m api.main &
API_PID=$!
sleep 2

echo ""
echo "=== Step 6: Launch Streamlit UI ==="
echo "  Streamlit UI:      http://localhost:8501"
echo "  Diagnostics API:   http://localhost:${API_PORT}/docs"
echo "  Mock Enterprise:   http://localhost:${MOCK_PORT}/docs"
echo "  Neo4j Browser:     http://localhost:7474"
streamlit run ui/app.py --server.headless true