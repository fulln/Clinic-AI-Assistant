# Clinic AI Assistant

Clinic AI Assistant is a multilingual SaaS-style AI workspace for clinic and care scenarios. It combines AI conversation, agent catalog management, and RAG knowledge retrieval in one admin-ready web application.

## What It Does

- Multilingual site UI with Chinese and English support.
- Locale-aware AI responses that follow the active conversation/site language.
- AI chat workspace with persistent conversations.
- Agent catalog, admin agent management, publish/archive/restore workflow.
- RAG document retrieval with similarity filtering to suppress weak matches.
- Public landing page plus authenticated SaaS dashboard.

## Tech Stack

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS, Zustand, React Query
- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis
- Data: PostgreSQL with `pgvector`
- AI stack: OpenAI SDK, LangChain, LangGraph

## Project Structure

```text
frontend/   Next.js application
backend/    FastAPI app, jobs, migrations, agent/RAG APIs
docs/       Project docs
specs/      Specs and task artifacts
start.sh    Local bootstrap script
```

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.11+
- `uv`
- Docker
- An `.env` file with at least the required database settings and `OPENAI_API_KEY`

### Start The Project

Use the repo bootstrap script:

```bash
./start.sh
```

This script will:

- start PostgreSQL and Redis with Docker
- create the backend virtualenv if missing
- install backend and frontend dependencies
- run Alembic migrations
- start backend, Celery, and frontend
- seed built-in agents

### Default Local URLs

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Default Admin Account

- Username: `admin`
- Password: `123456`

## Notes

- The landing page is public; workspace areas require login.
- Admin users can access agent management.
- RAG results are filtered so only matches with `similarity_score > 0.5` are returned.

## Current Focus

This repo currently includes:

- full-site internationalization treatment
- AI reply locale alignment
- SaaS dashboard styling refresh
- landing page and workspace integration for chat, agents, agent management, and RAG
