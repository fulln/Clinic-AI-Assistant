#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
LOG_DIR="$ROOT/.logs"

mkdir -p "$LOG_DIR"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[start]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }

# ── Load .env ────────────────────────────────────────────────────────────────
if [[ -f "$ROOT/.env" ]]; then
  set -a; source "$ROOT/.env"; set +a
  info "Loaded .env"
else
  error ".env not found — copy .env.example and fill in OPENAI_API_KEY"
fi

# ── Check Docker infra ────────────────────────────────────────────────────────
info "Checking Docker infra (postgres + redis)..."
if ! docker compose -f "$ROOT/docker-compose.yml" ps 2>/dev/null | grep -q "healthy"; then
  info "Starting postgres and redis..."
  docker compose -f "$ROOT/docker-compose.yml" up -d postgres redis
  until docker compose -f "$ROOT/docker-compose.yml" ps 2>/dev/null | grep -q "healthy"; do
    sleep 2
  done
  info "Infra is healthy"
else
  info "Infra already running"
fi

# ── Python venv ───────────────────────────────────────────────────────────────
if [[ ! -d "$VENV" ]]; then
  info "Creating Python venv with uv..."
  uv venv "$VENV" --python python3.11 2>/dev/null || uv venv "$VENV"
fi

info "Installing backend dependencies..."
uv pip install -r "$BACKEND/requirements.txt" --python "$VENV/bin/python" -q

PYTHON="$VENV/bin/python"
CELERY="$VENV/bin/celery"

# ── Alembic migrations ────────────────────────────────────────────────────────
info "Running DB migrations..."
(cd "$BACKEND" && "$PYTHON" -m alembic upgrade head) \
  && info "Migrations up to date" \
  || warn "Migration failed (schema may already be current)"

# ── Seed admin (idempotent) ───────────────────────────────────────────────────
info "Seeding admin user..."
(cd "$BACKEND" && "$PYTHON" -m scripts.seed_admin \
  --username admin --password 123456 --display-name "管理员" 2>&1) \
  | grep -v "Traceback\|File \"/\|raise\|Error" || true

# ── Frontend deps ─────────────────────────────────────────────────────────────
if [[ ! -d "$FRONTEND/node_modules" ]]; then
  info "Installing frontend dependencies..."
  (cd "$FRONTEND" && npm install --silent)
fi

# ── Launch processes ──────────────────────────────────────────────────────────
info "Starting backend  → http://localhost:8000  (logs: .logs/backend.log)"
(cd "$BACKEND" && "$PYTHON" -m uvicorn src.interfaces.api.main:app \
  --host 0.0.0.0 --port 8000 --reload \
  > "$LOG_DIR/backend.log" 2>&1) &
BACKEND_PID=$!

info "Starting celery   → logs: .logs/celery.log"
(cd "$BACKEND" && "$CELERY" -A src.infrastructure.celery_app worker \
  --loglevel=info \
  > "$LOG_DIR/celery.log" 2>&1) &
CELERY_PID=$!

info "Starting frontend → http://localhost:3000  (logs: .logs/frontend.log)"
(cd "$FRONTEND" && npm run dev \
  > "$LOG_DIR/frontend.log" 2>&1) &
FRONTEND_PID=$!

# ── Wait for backend ──────────────────────────────────────────────────────────
info "Waiting for backend to be ready..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8000/health | grep -q '"status":"ok"' 2>/dev/null; then
    info "Backend is ready"
    break
  fi
  sleep 2
done

# ── Seed agents (if backend is up) ───────────────────────────────────────────
if curl -s http://localhost:8000/health | grep -q '"status":"ok"' 2>/dev/null; then
  (cd "$BACKEND" && \
    ADMIN_USERNAME=admin ADMIN_PASSWORD=123456 API_BASE_URL=http://localhost:8000 \
    "$PYTHON" -m scripts.seed_agents --config config/agents/formal_agents.json 2>&1 | tail -5) &
  (cd "$BACKEND" && \
    ADMIN_USERNAME=admin ADMIN_PASSWORD=123456 API_BASE_URL=http://localhost:8000 \
    "$PYTHON" -m scripts.seed_agents --config config/agents/demo_agents.json 2>&1 | tail -5) &
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Frontend  →  ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend   →  ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs  →  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Login     →  admin / 123456"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Logs: tail -f .logs/backend.log  |  .logs/celery.log  |  .logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all processes."

# ── Cleanup on exit ───────────────────────────────────────────────────────────
trap "echo ''; info 'Shutting down...'; kill $BACKEND_PID $CELERY_PID $FRONTEND_PID 2>/dev/null; wait 2>/dev/null; info 'Done.'" EXIT INT TERM

wait $BACKEND_PID
