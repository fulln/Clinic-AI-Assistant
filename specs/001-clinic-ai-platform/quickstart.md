# Quickstart: 私立诊所 AI 助手平台

**Local Development Setup** | Docker Compose

## Prerequisites

- Docker Desktop 4.x+ (or Docker Engine + Compose plugin)
- Git
- `.env` file (copy from `.env.example`, fill in LLM API key)

## Environment Variables

Create `.env` in the project root:

```bash
# LLM
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1   # or custom compatible endpoint
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# PostgreSQL
POSTGRES_USER=clinic_user
POSTGRES_PASSWORD=clinic_pass
POSTGRES_DB=clinic_ai
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=development

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Start All Services

```bash
# First time: build images + start all services
docker compose up --build

# Subsequent starts
docker compose up

# Background mode
docker compose up -d
```

Services started:
- `postgres` → localhost:5432 (PostgreSQL 16 + pgvector)
- `redis` → localhost:6379
- `backend` → localhost:8000 (FastAPI, auto-reload in dev)
- `frontend` → localhost:3000 (Next.js, hot-reload in dev)

## Initialize Database

```bash
# Run migrations (Alembic)
docker compose exec backend alembic upgrade head

# Seed admin user
docker compose exec backend python -m scripts.seed_admin \
  --username admin \
  --password admin123 \
  --display-name "系统管理员"
```

## Verify Setup

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}

# API docs (Swagger UI)
open http://localhost:8000/docs

# Frontend
open http://localhost:3000
```

## Seed Demo Agents

```bash
# Batch-publish the 10 demo agents + 5 formal agents
docker compose exec backend python -m scripts.seed_agents --config config/agents/demo_agents.json
docker compose exec backend python -m scripts.seed_agents --config config/agents/formal_agents.json
```

## Development Workflow

### Backend (Python / FastAPI)

```bash
# Install deps locally (for IDE support)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run tests
docker compose exec backend pytest tests/ -v

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "add_feature_x"
```

### Frontend (Next.js / TypeScript)

```bash
# Install deps locally
cd frontend
npm install

# Run tests
npm test

# Type check
npm run type-check

# Lint
npm run lint
```

## Docker Compose Services Overview

```yaml
# docker-compose.yml structure (summary)
services:
  postgres:
    image: pgvector/pgvector:pg16
    volumes: [postgres_data:/var/lib/postgresql/data]
    env: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]

  backend:
    build: ./backend
    depends_on: [postgres, redis]
    volumes: [./backend:/app]   # hot-reload in dev
    env_file: .env

  frontend:
    build: ./frontend
    depends_on: [backend]
    volumes: [./frontend:/app]  # hot-reload in dev
    env_file: .env

volumes:
  postgres_data:
  redis_data:
```

## Stopping / Resetting

```bash
# Stop services (preserve data)
docker compose down

# Stop + delete all data volumes (full reset)
docker compose down -v
```
