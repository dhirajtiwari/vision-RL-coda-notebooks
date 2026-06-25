#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source venv/bin/activate

echo "=== Step 1: Generate synthetic data ==="
python graph/synthetic_data_generator.py

echo ""
echo "=== Step 2: Check Neo4j ==="
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
echo "=== Step 3: Populate knowledge graph ==="
python graph/populate_graph.py

echo ""
echo "=== Step 4: Run evaluation tests ==="
python tests/test_diagnosis.py

echo ""
echo "=== Step 5: Launch Streamlit demo ==="
echo "Opening http://localhost:8501"
streamlit run ui/app.py --server.headless true