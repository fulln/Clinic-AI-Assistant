# Implementation Plan: 私立诊所 AI 助手平台

**Branch**: `001-clinic-ai-platform` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-clinic-ai-platform/spec.md`

## Summary

构建一个私立诊所/私人医生专属 AI 助手平台，采用前后端分离架构（Next.js 14 + Python FastAPI），
基于 LangChain + LangGraph 实现多智能体工作流编排，支持批量智能体上架、医师个人 RAG 知识库管理
和统一会话上下文管理。前后端均遵循 DDD（领域驱动设计）分层架构，数据层使用 PostgreSQL + pgvector
做向量化存储，Redis 做缓存与会话状态管理，全套基础设施通过 Docker Compose 部署。

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: TypeScript 5+ / Next.js 14+ (App Router)

**Primary Dependencies**:
- Backend: FastAPI, LangChain, LangGraph, SQLAlchemy 2.x, Alembic, Pydantic v2, python-jose (JWT), bcrypt, celery (async doc processing)
- Frontend: Next.js 14, React 18, TailwindCSS, shadcn/ui, Zustand (state), react-query

**Storage**:
- Primary DB: PostgreSQL 16 + pgvector extension (Docker: `pgvector/pgvector:pg16`)
- Cache / Session: Redis 7+ (Docker: `redis:7-alpine`)
- File uploads: Local volume (dev); configurable S3-compatible storage (prod)

**Testing**:
- Backend: pytest + pytest-asyncio + httpx (async test client)
- Frontend: Jest + React Testing Library + Playwright (E2E)

**Target Platform**: Docker Compose (single-host Linux/macOS); all services containerized.

**Project Type**: Full-stack web application (frontend SPA + backend REST/WebSocket API)

**Performance Goals**:
- Non-AI API endpoints: p95 < 200ms
- AI first-token response: p95 < 3s
- Document vectorization: < 60s for documents < 10MB
- Batch agent publish (15 agents): < 30s total

**Constraints**:
- All patient-adjacent data encrypted at rest and in transit (AES-256 / TLS 1.2+)
- Audit logs append-only; retained ≥ 5 years
- Max concurrent users: 50 (single-clinic scale)
- LLM via external API (OpenAI-compatible); no self-hosted model

**Scale/Scope**:
- 5 formal agents + 10 demo agents = 15 agents total
- 4 frontend showcase agents (subset of the 15)
- Max ~200 registered users per deployment
- Estimated DB size: < 50GB including vector embeddings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Check | Status |
|---|-----------|-------|--------|
| I | Medical Safety First | All AI endpoints inject disclaimer; intent classifier node rejects diagnostic/prescription requests; test suite covers refusal behavior | ✅ PASS |
| II | Patient Data Privacy | PII encrypted at rest (PostgreSQL column encryption + AES-256 at volume level); logs anonymized (IP last octet zeroed); JWT in httpOnly cookies; audit log redaction on message delete | ✅ PASS |
| III | Strict Service Scope | Platform covers exactly 4 permitted categories: auxiliary dialogue, document organization, operations consulting, health science popularization; spec gate reviewed | ✅ PASS |
| IV | Human-in-the-Loop | Doctor must review and approve AI-drafted documents before delivery; WebSocket protocol supports `tool_request`/`approve_tool` flow; no auto-send to patients | ✅ PASS |
| V | Auditability & Observability | AuditLog entity defined (append-only, 5-year retention); all 13 action types logged; health metrics endpoint exposed; Redis-backed context + PostgreSQL audit trail | ✅ PASS |

**Post-Design Re-check**: ✅ All gates passed after Phase 1. No constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-clinic-ai-platform/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: domain entities & DB schema
├── quickstart.md        # Phase 1: local dev setup guide
├── contracts/
│   ├── auth-api.md      # Authentication REST contracts
│   ├── agent-api.md     # Agent management + batch publish contracts
│   ├── conversation-api.md  # Unified conversation + SSE/WebSocket
│   └── rag-api.md       # Doctor RAG knowledge base contracts
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domains/                        # DDD Domain Layer
│   │   ├── auth/
│   │   │   ├── entities.py             # User entity, UserRole value object
│   │   │   ├── value_objects.py        # Password, Token value objects
│   │   │   ├── repository.py           # IUserRepository (abstract port)
│   │   │   └── services.py             # AuthDomainService
│   │   ├── agent/
│   │   │   ├── entities.py             # Agent entity, AgentPublication
│   │   │   ├── value_objects.py        # AgentConfig, AgentStatus, AgentType
│   │   │   ├── aggregates.py           # AgentCatalog aggregate root
│   │   │   ├── repository.py           # IAgentRepository
│   │   │   └── services.py             # AgentDispatcher, AgentScheduler
│   │   ├── conversation/
│   │   │   ├── entities.py             # Conversation, Message entities
│   │   │   ├── aggregates.py           # ConversationSession aggregate
│   │   │   ├── value_objects.py        # MessageRole, SessionContext
│   │   │   ├── repository.py           # IConversationRepository
│   │   │   └── services.py             # ConversationDomainService
│   │   ├── rag/
│   │   │   ├── entities.py             # KnowledgeBase, Document, DocumentChunk
│   │   │   ├── value_objects.py        # Embedding, ChunkMetadata
│   │   │   ├── repository.py           # IKnowledgeBaseRepository
│   │   │   └── services.py             # VectorSearchService, ChunkingService
│   │   ├── publishing/
│   │   │   ├── entities.py             # PublishingBatch, PublishingBatchItem
│   │   │   ├── aggregates.py           # PublishingBatch aggregate root
│   │   │   ├── repository.py           # IPublishingRepository
│   │   │   └── services.py             # BatchPublishingService
│   │   └── audit/
│   │       ├── entities.py             # AuditLog entity
│   │       └── services.py             # AuditService (cross-cutting)
│   ├── application/                    # DDD Application Layer (use cases)
│   │   ├── auth_service.py             # Login, logout, token refresh
│   │   ├── agent_service.py            # CRUD + publish + dispatch
│   │   ├── conversation_service.py     # Session management, message flow
│   │   ├── rag_service.py              # KB management, doc upload, query
│   │   └── publishing_service.py       # Batch publish orchestration
│   ├── infrastructure/                 # DDD Infrastructure Layer (adapters)
│   │   ├── db/
│   │   │   ├── models.py               # SQLAlchemy ORM models
│   │   │   ├── repositories/           # Concrete repository implementations
│   │   │   │   ├── user_repo.py
│   │   │   │   ├── agent_repo.py
│   │   │   │   ├── conversation_repo.py
│   │   │   │   ├── rag_repo.py
│   │   │   │   └── audit_repo.py
│   │   │   └── migrations/             # Alembic migration files
│   │   ├── cache/
│   │   │   └── redis_client.py         # Redis connection + key helpers
│   │   ├── llm/
│   │   │   ├── langchain_adapter.py    # LLM client wrapper
│   │   │   ├── langgraph_workflows/    # Agent StateGraph definitions
│   │   │   │   ├── base_workflow.py    # Shared nodes (context_loader, disclaimer, safety_check)
│   │   │   │   ├── medical_auxiliary.py
│   │   │   │   ├── document_organizer.py
│   │   │   │   ├── operations_consultant.py
│   │   │   │   ├── health_educator.py
│   │   │   │   └── rag_qa.py
│   │   │   └── checkpointer.py         # Redis-based LangGraph checkpointer
│   │   ├── vector_store/
│   │   │   └── pgvector_adapter.py     # pgvector HNSW similarity search
│   │   └── storage/
│   │       └── file_storage.py         # Document file upload adapter
│   └── interfaces/                     # DDD Interface Layer
│       └── api/
│           ├── main.py                 # FastAPI app factory
│           ├── dependencies.py         # Auth middleware, DB session injection
│           ├── routers/
│           │   ├── auth.py
│           │   ├── agents.py
│           │   ├── conversations.py
│           │   └── rag.py
│           ├── schemas/                # Pydantic request/response schemas
│           │   ├── auth_schemas.py
│           │   ├── agent_schemas.py
│           │   ├── conversation_schemas.py
│           │   └── rag_schemas.py
│           └── websocket/
│               └── conversation_ws.py  # WebSocket handler
├── tests/
│   ├── domain/                         # Pure domain unit tests (no DB)
│   ├── application/                    # Application service tests (mocked infra)
│   └── integration/                    # Full stack integration tests (real DB)
├── scripts/
│   ├── seed_admin.py
│   └── seed_agents.py
├── config/
│   └── agents/
│       ├── formal_agents.json
│       └── demo_agents.json
├── alembic.ini
├── requirements.txt
└── Dockerfile

frontend/
├── src/
│   ├── app/                            # Next.js App Router (Interface Layer)
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/
│   │   │   ├── agents/
│   │   │   │   ├── page.tsx            # Agent catalog
│   │   │   │   └── [agentId]/page.tsx  # Agent detail + demo entry
│   │   │   ├── conversation/
│   │   │   │   └── page.tsx            # Unified conversation UI
│   │   │   ├── rag/
│   │   │   │   └── page.tsx            # Doctor RAG management (doctor role only)
│   │   │   └── layout.tsx
│   │   ├── layout.tsx
│   │   └── middleware.ts               # Route protection by role
│   ├── domains/                        # DDD Domain Layer (frontend)
│   │   ├── auth/
│   │   │   ├── entities.ts             # User entity, UserRole type
│   │   │   └── services.ts             # AuthDomainService (validation rules)
│   │   ├── agent/
│   │   │   ├── entities.ts             # Agent entity
│   │   │   └── services.ts
│   │   ├── conversation/
│   │   │   ├── entities.ts             # Conversation, Message, Session
│   │   │   └── services.ts
│   │   └── rag/
│   │       ├── entities.ts             # KnowledgeBase, Document
│   │       └── services.ts
│   ├── features/                       # DDD Bounded Context modules
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   └── LoginForm.tsx
│   │   │   └── hooks/
│   │   │       └── useAuth.ts
│   │   ├── agent-catalog/
│   │   │   ├── components/
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   ├── AgentList.tsx
│   │   │   │   └── AgentTypeBadge.tsx
│   │   │   └── hooks/
│   │   │       └── useAgents.ts
│   │   ├── conversation/               # Unified conversation component (shared by all agents)
│   │   │   ├── components/
│   │   │   │   ├── ConversationPanel.tsx   # Root component (used by all agent UIs)
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   ├── AgentSelector.tsx
│   │   │   │   ├── DisclaimerBanner.tsx
│   │   │   │   └── StreamingMessage.tsx    # SSE token-by-token rendering
│   │   │   └── hooks/
│   │   │       ├── useConversation.ts
│   │   │       └── useSSEStream.ts
│   │   └── rag/
│   │       ├── components/
│   │       │   ├── KnowledgeBaseList.tsx
│   │       │   ├── DocumentUploader.tsx
│   │       │   └── DocumentStatusBadge.tsx
│   │       └── hooks/
│   │           └── useKnowledgeBase.ts
│   ├── shared/
│   │   ├── components/
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── api/
│   │   │   └── client.ts               # Axios/fetch wrapper with auth headers
│   │   └── store/
│   │       └── authStore.ts            # Zustand: user session state
├── tests/
│   ├── unit/
│   └── e2e/                            # Playwright E2E tests
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── Dockerfile

docker-compose.yml
docker-compose.dev.yml
.env.example
```

**Structure Decision**: Web application option (frontend + backend separation) selected. Both sub-projects follow DDD with Hexagonal Architecture: domain → application → infrastructure → interface. Frontend uses Next.js App Router as the interface layer with DDD feature modules as bounded contexts. The `features/conversation/` module is the single unified conversation component consumed by all agent UIs.

## Complexity Tracking

> No Constitution Check violations. No unjustified complexity.

| Design Choice | Justification |
|---------------|---------------|
| LangGraph for all agents (not just complex ones) | Uniformity: all agents share the same base workflow nodes (safety_check, disclaimer, context_loader); simpler to maintain 15 agents with one framework |
| Redis + PostgreSQL dual storage for conversation context | Constitution Principle V requires durable audit trail (PostgreSQL); UX requires low-latency context reads during streaming (Redis). Both are needed. |
| Celery for async document processing | Document vectorization can take 10-60s; must not block the HTTP request lifecycle. Celery + Redis as broker is Docker-native and fits the existing stack. |
