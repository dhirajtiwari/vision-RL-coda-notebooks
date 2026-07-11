#!/bin/bash
# ============================================================================
# WarrantyGraph Application — Complete Restart Script
# Stops all old services and starts the correct 2026 stack:
#   - Neo4j (graph database)
#   - FastAPI backend (port 8080)
#   - Next.js frontend (port 3000)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="diagnostic-chatbot"
VENV_PATH="$SCRIPT_DIR/venv"

echo "═══════════════════════════════════════════════════════════════════════"
echo "  WarrantyGraph Full Application Restart"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# ────────────────────────────────────────────────────────────────────────────
# 1. KILL OLD SERVICES
# ────────────────────────────────────────────────────────────────────────────
echo "🔴 Stopping old services..."

# Kill old Streamlit (port 8501)
pkill -f "streamlit run ui/app.py" 2>/dev/null && echo "  ✓ Killed old Streamlit" || echo "  • Streamlit not running"

# Kill old FastAPI if running on port 8080 (we'll restart it fresh)
pkill -f "uvicorn api.main:app" 2>/dev/null && echo "  ✓ Killed old FastAPI" || echo "  • FastAPI not running"

# Kill old Next.js dev servers
pkill -f "next dev" 2>/dev/null && echo "  ✓ Killed old Next.js dev server" || echo "  • Next.js dev not running"
pkill -f "next-server" 2>/dev/null && echo "  ✓ Killed Next.js server processes" || echo "  • Next.js servers not running"

sleep 2
echo ""

# ────────────────────────────────────────────────────────────────────────────
# 2. START INFRA (Neo4j + Redis via Docker when available)
# ────────────────────────────────────────────────────────────────────────────
echo "🗄️  Starting infra (Neo4j + Redis)..."

if docker info >/dev/null 2>&1; then
  # Production Neo4j :7687 (prefer existing neo4j-demo)
  if docker ps -a --format '{{.Names}}' | grep -qx neo4j-demo; then
    docker start neo4j-demo >/dev/null 2>&1 || true
    echo "  ✓ neo4j-demo (production :7687)"
  else
    docker compose -f "$SCRIPT_DIR/docker/docker-compose.infra.yaml" up -d neo4j >/dev/null 2>&1 || true
    echo "  ✓ compose neo4j production"
  fi
  # Staging Neo4j :7688
  docker compose -f "$SCRIPT_DIR/docker/docker-compose.infra.yaml" up -d neo4j-staging >/dev/null 2>&1 || true
  echo "  ✓ neo4j staging :7688"
  if ! nc -z localhost 6379 2>/dev/null; then
    docker compose -f "$SCRIPT_DIR/docker/docker-compose.infra.yaml" up -d redis >/dev/null 2>&1 || true
    echo "  ✓ redis started"
  else
    echo "  ✓ redis already listening on :6379"
  fi
else
  echo "  ⚠ Docker daemon not running — start Docker Desktop, then re-run."
  echo "    open -a Docker"
fi

export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_STAGING_URI="${NEO4J_STAGING_URI:-bolt://localhost:7688}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"

# Wait for production Bolt
for i in 1 2 3 4 5 6 7 8 9 10; do
  nc -z localhost 7687 2>/dev/null && break
  sleep 2
done

if nc -z localhost 7687 2>/dev/null; then
    echo "  ✓ Neo4j production bolt://localhost:7687"
else
    echo "  ⚠ Neo4j production down — /diagnose will fail"
fi
if nc -z localhost 7688 2>/dev/null; then
    echo "  ✓ Neo4j staging bolt://localhost:7688"
else
    echo "  ⚠ Neo4j staging down — promote target=staging will fail"
fi
echo ""

# ────────────────────────────────────────────────────────────────────────────
# 3. START FASTAPI BACKEND
# ────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting FastAPI backend on http://localhost:8080..."

# Activate venv if it exists
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Start FastAPI in background (Redis-backed rate limit/cache when REDIS_URL set)
cd "$SCRIPT_DIR"
export PYTHONPATH="${PYTHONPATH:-$SCRIPT_DIR}"
nohup env REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}" \
  NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}" \
  NEO4J_STAGING_URI="${NEO4J_STAGING_URI:-bolt://localhost:7688}" \
  NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}" \
  PYTHONPATH="$SCRIPT_DIR" \
  uvicorn api.main:app --host 0.0.0.0 --port 8080 --log-level warning > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "  ✓ FastAPI started (PID: $FASTAPI_PID) REDIS_URL=$REDIS_URL"

sleep 2

# Verify FastAPI is responding
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "  ✓ FastAPI health check passed"
else
    echo "  ⚠ FastAPI health check failed (may still be starting...)"
fi
echo ""

# ────────────────────────────────────────────────────────────────────────────
# 4. START NEXT.JS FRONTEND
# ────────────────────────────────────────────────────────────────────────────
echo "🎨 Starting Next.js frontend on http://localhost:3000..."

cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

# Clear stale build cache to prevent stale styles / missing components
if [ -d ".next" ]; then
    rm -rf .next
    echo "  ✓ Cleared stale .next cache"
fi

# Start Next.js dev server in background
nohup npm run dev > /tmp/nextjs.log 2>&1 &
NEXTJS_PID=$!
echo "  ✓ Next.js dev server started (PID: $NEXTJS_PID)"

sleep 3

# Verify Next.js is responding
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ Next.js is responding"
else
    echo "  ⚠ Next.js may still be building..."
fi
echo ""

# ────────────────────────────────────────────────────────────────────────────
# 5. SUMMARY & STATUS
# ────────────────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════════"
echo "  ✅ Application started successfully!"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 Service Status:"
echo ""
echo "  🗄️  Neo4j Database"
echo "     • Bolt: bolt://localhost:7687"
echo "     • Browser: http://localhost:7474"
echo ""
echo "  🔌 FastAPI Backend"
echo "     • URL: http://localhost:8080"
echo "     • Health: http://localhost:8080/health"
echo "     • Docs: http://localhost:8080/docs"
echo "     • Log: tail -f /tmp/fastapi.log"
echo ""
echo "  🎨 Next.js Frontend"
echo "     • URL: http://localhost:3000"
echo "     • Log: tail -f /tmp/nextjs.log"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "🔗 Open in browser: http://localhost:3000"
echo ""
echo "To view logs:"
echo "  • FastAPI: tail -f /tmp/fastapi.log"
echo "  • Next.js: tail -f /tmp/nextjs.log"
echo ""
echo "To stop all services:"
echo "  pkill -f 'uvicorn api.main:app' && pkill -f 'next dev'"
echo ""
