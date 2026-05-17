# Tasks: 私立诊所 AI 助手平台

**Input**: Design documents from `specs/001-clinic-ai-platform/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Tests**: Not explicitly requested — test tasks are excluded from this breakdown. Add them separately if TDD is required.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Paths follow the DDD structure defined in `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create all directory scaffolding and base configuration before any code is written.

- [x] T001 Create backend directory structure per plan.md (`backend/src/domains/`, `backend/src/application/`, `backend/src/infrastructure/`, `backend/src/interfaces/`, `backend/tests/`, `backend/scripts/`, `backend/config/agents/`)
- [x] T002 Create frontend directory structure per plan.md (`frontend/src/app/`, `frontend/src/domains/`, `frontend/src/features/`, `frontend/src/shared/`, `frontend/tests/`)
- [x] T003 [P] Create `docker-compose.yml` with services: `pgvector/pgvector:pg16`, `redis:7-alpine`, backend (FastAPI), frontend (Next.js); declare named volumes `postgres_data` and `redis_data`
- [x] T004 [P] Create `docker-compose.dev.yml` override with hot-reload bind-mounts for `./backend:/app` and `./frontend:/app`
- [x] T005 [P] Create `.env.example` with all variables from `quickstart.md` (LLM, DB, Redis, JWT, ports)
- [x] T006 [P] Create `backend/Dockerfile` (Python 3.11-slim, install requirements, uvicorn entrypoint)
- [x] T007 [P] Create `frontend/Dockerfile` (Node 20-alpine, `npm ci`, `next build` for prod; `next dev` for dev)
- [x] T008 [P] Create `backend/requirements.txt` with all Python dependencies from plan.md: FastAPI, LangChain, LangGraph, SQLAlchemy 2.x, Alembic, Pydantic v2, python-jose, bcrypt, celery, redis, pgvector, httpx, uvicorn
- [x] T009 [P] Initialize `frontend/package.json` with all Node dependencies from plan.md: Next.js 14, React 18, TypeScript 5, TailwindCSS, shadcn/ui, Zustand, @tanstack/react-query, axios
- [x] T010 [P] Configure backend linting in `backend/pyproject.toml` (ruff, black, isort; line-length 100)
- [x] T011 [P] Configure frontend linting in `frontend/.eslintrc.json` and `frontend/.prettierrc` (ESLint with Next.js rules, Prettier)
- [x] T012 [P] Configure TailwindCSS in `frontend/tailwind.config.ts` and `frontend/next.config.ts` (App Router, content paths, shadcn theme)
- [x] T013 [P] Create `frontend/tsconfig.json` with path aliases (`@/*` → `./src/*`, strict mode enabled)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, Redis, app factory, and cross-cutting infrastructure MUST be complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T014 Initialize Alembic in `backend/` (`alembic init backend/src/infrastructure/db/migrations`); configure `alembic.ini` and `env.py` to read `DATABASE_URL` from environment
- [x] T015 Add `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` and `CREATE EXTENSION IF NOT EXISTS vector` to Alembic `env.py` run_migrations hook in `backend/src/infrastructure/db/migrations/env.py`
- [x] T016 Create SQLAlchemy ORM models for ALL entities in `backend/src/infrastructure/db/models.py`: User, Agent, AgentPublication, PublishingBatch, PublishingBatchItem, Conversation, ConversationSession, Message, KnowledgeBase, Document, DocumentChunk, AuditLog — with all enum types, relationships, and indexes from `data-model.md`
- [x] T017 [P] Configure Redis async client (aioredis) with connection pool and key helper functions in `backend/src/infrastructure/cache/redis_client.py`; expose `get`, `set`, `delete`, `expire` wrappers
- [x] T018 Generate Alembic initial migration from models (autogenerate) and review output in `backend/src/infrastructure/db/migrations/versions/`; add HNSW index for `document_chunks.embedding` manually
- [x] T019 [P] Create FastAPI app factory in `backend/src/interfaces/api/main.py`: create app, register all routers, configure CORS (allow `NEXT_PUBLIC_API_URL`), mount `/health` endpoint returning `{"status":"ok","version":"1.0.0"}`
- [x] T020 [P] Create dependency injection utilities in `backend/src/interfaces/api/dependencies.py`: async DB session factory (`get_db`), `get_current_user` JWT decoder using python-jose, `require_role(*roles)` guard
- [x] T021 [P] Configure global exception handlers (422, 403, 404, 500) and request logging middleware in `backend/src/interfaces/api/main.py`
- [x] T022 [P] Create frontend API client in `frontend/src/shared/api/client.ts`: axios instance with `NEXT_PUBLIC_API_URL` base URL, auth header injection from authStore, automatic 401 → token refresh → retry interceptor
- [x] T023 [P] Create Next.js route protection middleware in `frontend/src/app/middleware.ts`: redirect unauthenticated users to `/login`; protect `/rag` route to `doctor` role only
- [x] T024 [P] Configure Celery application with Redis broker in `backend/src/infrastructure/celery_app.py`; expose `celery_app` instance used by all async tasks
- [x] T025 [P] Create AuditLog domain entity in `backend/src/domains/audit/entities.py` (all 13 AuditAction values per data-model.md) and AuditService in `backend/src/domains/audit/services.py` (append-only `log()` method; no update/delete permitted)

**Checkpoint**: Docker Compose starts cleanly, `/health` returns 200, Alembic migrations apply successfully — ready for user story work.

---

## Phase 3: User Story 1 — 用户登录与角色区分 (Priority: P1) 🎯 MVP

**Goal**: Users can log in with username/password, receive role-appropriate dashboard access, and maintain session across browser restarts.

**Independent Test**: POST `/api/v1/auth/login` with valid doctor credentials → 200 + httpOnly refresh cookie set; access `/dashboard` → role-appropriate navigation visible; close and reopen browser → still logged in.

- [x] T026 [P] [US1] Create User entity and UserRole enum value object in `backend/src/domains/auth/entities.py` (fields: id, username, password_hash, role, display_name, is_active, timestamps; invariants from data-model.md)
- [x] T027 [P] [US1] Create Password and Token value objects in `backend/src/domains/auth/value_objects.py` (Password wraps bcrypt hash/verify; Token wraps JWT encode/decode with python-jose)
- [x] T028 [P] [US1] Define `IUserRepository` abstract interface in `backend/src/domains/auth/repository.py` (methods: `find_by_id`, `find_by_username`, `save`)
- [x] T029 [P] [US1] Implement `AuthDomainService` in `backend/src/domains/auth/services.py`: `verify_password(plain, hash)`, `create_access_token(user_id, role)`, `create_refresh_token(user_id, device_id)`, `blacklist_token(jti, ttl)` using Redis
- [x] T030 [US1] Implement `UserRepository` in `backend/src/infrastructure/db/repositories/user_repo.py` using SQLAlchemy async session (depends on T028, T016)
- [x] T031 [US1] Implement `AuthApplicationService` in `backend/src/application/auth_service.py`: `login(username, password)` → access token + sets refresh cookie, `logout(jti)` → blacklist token, `refresh(refresh_token)` → new access token (depends on T029, T030)
- [x] T032 [P] [US1] Create auth Pydantic v2 schemas in `backend/src/interfaces/api/schemas/auth_schemas.py`: `LoginRequest`, `LoginResponse` (access_token, user), `UserResponse` (id, username, role, display_name), `RefreshResponse`
- [x] T033 [US1] Implement auth API router in `backend/src/interfaces/api/routers/auth.py`: `POST /login`, `POST /refresh`, `POST /logout`, `GET /me` — wire all routes per `contracts/auth-api.md`; register router in main.py (depends on T031, T032)
- [x] T034 [P] [US1] Create User entity and UserRole type in `frontend/src/domains/auth/entities.ts` (mirror backend roles: doctor | staff | admin)
- [x] T035 [P] [US1] Create client-side `AuthDomainService` in `frontend/src/domains/auth/services.ts` (username format validation, password non-empty check)
- [x] T036 [US1] Create Zustand `authStore` in `frontend/src/shared/store/authStore.ts`: state `{ user, accessToken, isAuthenticated }`, actions `setUser`, `setToken`, `clearAuth`; persist to sessionStorage (depends on T034)
- [x] T037 [US1] Implement `useAuth` hook in `frontend/src/features/auth/hooks/useAuth.ts`: wraps `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`; updates authStore on success (depends on T035, T036)
- [x] T038 [US1] Create `LoginForm` component in `frontend/src/features/auth/components/LoginForm.tsx`: controlled username/password inputs, submit calls `useAuth.login`, show error on failure, redirect to dashboard on success (depends on T037)
- [x] T039 [US1] Create login page in `frontend/src/app/(auth)/login/page.tsx`: renders `LoginForm`; full-page centered layout (depends on T038)
- [x] T040 [P] [US1] Create auth route group layout in `frontend/src/app/(auth)/layout.tsx` (no nav header; redirect to dashboard if already authenticated)
- [x] T041 [US1] Create dashboard layout in `frontend/src/app/(dashboard)/layout.tsx` with role-based sidebar navigation: show "RAG管理" link only when `user.role === 'doctor'`; show "智能体管理" only for `admin` (depends on T036)

**Checkpoint**: Doctor and staff users can log in, see role-appropriate nav, and maintain session — independently verifiable without AI features.

---

## Phase 4: User Story 2 — 统一AI对话交互 (Priority: P1)

**Goal**: All logged-in users can send messages to any published agent via a unified conversation UI with SSE streaming, context persistence across agent switches, and mandatory medical disclaimers.

**Independent Test**: Log in → open conversation page → send message to `medical_auxiliary` agent → see streaming response with disclaimer banner → switch agent → prior messages visible in history.

- [x] T042 [P] [US2] Create Agent entity, AgentType, AgentStatus, AgentConfig value objects in `backend/src/domains/agent/entities.py` and `backend/src/domains/agent/value_objects.py`
- [x] T043 [P] [US2] Define `IAgentRepository` abstract interface in `backend/src/domains/agent/repository.py` (methods: `find_by_id`, `find_by_slug`, `find_published`, `save`)
- [x] T044 [P] [US2] Create Conversation, ConversationSession, Message entities in `backend/src/domains/conversation/entities.py` with all invariants from data-model.md (`has_disclaimer` MUST be true for medical assistant messages; content redacted on soft-delete)
- [x] T045 [P] [US2] Create ConversationSession aggregate root and MessageRole, SessionContext value objects in `backend/src/domains/conversation/aggregates.py` and `backend/src/domains/conversation/value_objects.py`
- [x] T046 [P] [US2] Define `IConversationRepository` abstract interface in `backend/src/domains/conversation/repository.py` (methods: `find_by_id`, `find_by_user_id`, `save_message`, `get_messages`)
- [x] T047 [US2] Implement `AgentRepository` in `backend/src/infrastructure/db/repositories/agent_repo.py` with Redis catalog cache (`agent:catalog`, TTL 5 min; invalidate on publish/archive) (depends on T043, T016, T017)
- [x] T048 [US2] Implement `ConversationRepository` in `backend/src/infrastructure/db/repositories/conversation_repo.py`; on session save, write `context_snapshot` to both PostgreSQL and Redis `session:{session_id}:context` (TTL 24h) (depends on T046, T016, T017)
- [x] T049 [P] [US2] Create LangChain LLM adapter in `backend/src/infrastructure/llm/langchain_adapter.py`: wraps `ChatOpenAI` (configurable model from env), exposes streaming `astream()` method
- [x] T050 [P] [US2] Create Redis-backed LangGraph checkpointer in `backend/src/infrastructure/llm/checkpointer.py` using `langgraph.checkpoint.redis`; connects to Redis from env vars (depends on T017)
- [x] T051 [US2] Create base LangGraph workflow with shared nodes in `backend/src/infrastructure/llm/langgraph_workflows/base_workflow.py`: `context_loader` (loads Redis session), `intent_classifier` (rejects diagnosis/prescription intents → `agent_refused` SSE error), `disclaimer` (appends 免责声明 to response), `context_saver` (writes checkpoint) (depends on T049, T050)
- [x] T052 [P] [US2] Create `medical_auxiliary` LangGraph StateGraph in `backend/src/infrastructure/llm/langgraph_workflows/medical_auxiliary.py`: inherits base nodes, adds medical FAQ tool (depends on T051)
- [x] T053 [P] [US2] Create `document_organizer` LangGraph StateGraph in `backend/src/infrastructure/llm/langgraph_workflows/document_organizer.py`: inherits base nodes, adds document structuring tool (depends on T051)
- [x] T054 [P] [US2] Create `operations_consultant` LangGraph StateGraph in `backend/src/infrastructure/llm/langgraph_workflows/operations_consultant.py`: inherits base nodes, adds clinic ops knowledge (depends on T051)
- [x] T055 [P] [US2] Create `health_educator` LangGraph StateGraph in `backend/src/infrastructure/llm/langgraph_workflows/health_educator.py`: inherits base nodes, adds health education content (depends on T051)
- [x] T056 [P] [US2] Create `rag_qa` LangGraph StateGraph stub in `backend/src/infrastructure/llm/langgraph_workflows/rag_qa.py`: inherits base nodes; RAG retrieval node wired in Phase 6 (depends on T051)
- [x] T057 [US2] Create `AgentDispatcher` domain service in `backend/src/domains/agent/services.py`: routes message to correct LangGraph workflow by `agent_id`; registers all 5 formal workflows (depends on T042, T052–T056)
- [x] T058 [US2] Create `ConversationDomainService` in `backend/src/domains/conversation/services.py`: enforces `has_disclaimer` invariant, handles soft-delete redaction, manages agent switch within session (depends on T044, T045)
- [x] T059 [US2] Implement `ConversationApplicationService` in `backend/src/application/conversation_service.py`: create/get/delete conversation, send message → dispatch to AgentDispatcher → stream SSE tokens → save Message + update ConversationSession (depends on T057, T058, T048)
- [x] T060 [P] [US2] Create conversation Pydantic schemas in `backend/src/interfaces/api/schemas/conversation_schemas.py`: `CreateConversationRequest`, `ConversationResponse`, `MessageRequest`, `MessageResponse`, `SessionUpdateRequest` per `contracts/conversation-api.md`
- [x] T061 [US2] Implement conversation API router in `backend/src/interfaces/api/routers/conversations.py`: all endpoints per `contracts/conversation-api.md` including SSE `POST /{id}/messages` (response `text/event-stream`), PATCH `/session`, DELETE soft-delete; register router in main.py (depends on T059, T060)
- [x] T062 [US2] Implement WebSocket handler in `backend/src/interfaces/api/websocket/conversation_ws.py`: `/ws/conversations/{id}?token=...`; handle `message`, `approve_tool`, `reject_tool` client events; emit `token`, `tool_request`, `end`, `error` server events per `contracts/conversation-api.md` (depends on T059)
- [x] T063 [P] [US2] Create Conversation, Message, ConversationSession entities in `frontend/src/domains/conversation/entities.ts`
- [x] T064 [P] [US2] Create `ConversationDomainService` in `frontend/src/domains/conversation/services.ts` (client-side message length validation, agent switch logic)
- [x] T065 [US2] Create `useSSEStream` hook in `frontend/src/features/conversation/hooks/useSSEStream.ts`: connects to `POST /conversations/{id}/messages` EventSource; accumulates token stream; emits `onToken`, `onDisclaimer`, `onEnd`, `onError` callbacks
- [x] T066 [US2] Create `useConversation` hook in `frontend/src/features/conversation/hooks/useConversation.ts`: load conversation history, send message via `useSSEStream`, manage agent selection, handle PATCH session for agent switch (depends on T064, T065)
- [x] T067 [P] [US2] Create `DisclaimerBanner` component in `frontend/src/features/conversation/components/DisclaimerBanner.tsx`: renders "本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。" in amber callout style (Constitution Principle I)
- [x] T068 [P] [US2] Create `StreamingMessage` component in `frontend/src/features/conversation/components/StreamingMessage.tsx`: renders token-by-token streaming text with typing cursor; shows `DisclaimerBanner` when `has_disclaimer` is true
- [x] T069 [P] [US2] Create `MessageList` component in `frontend/src/features/conversation/components/MessageList.tsx`: renders user and assistant messages; auto-scrolls to bottom; uses `StreamingMessage` for in-flight AI responses
- [x] T070 [P] [US2] Create `MessageInput` component in `frontend/src/features/conversation/components/MessageInput.tsx`: textarea with submit (Enter/button), max 4000 chars, disabled during streaming
- [x] T071 [P] [US2] Create `AgentSelector` component in `frontend/src/features/conversation/components/AgentSelector.tsx`: dropdown of published agents filtered by current user role; triggers PATCH session on selection change
- [x] T072 [US2] Create `ConversationPanel` root component in `frontend/src/features/conversation/components/ConversationPanel.tsx`: composes AgentSelector + MessageList + MessageInput + DisclaimerBanner; accepts optional `agentId` prop for demo mode binding (depends on T067–T071)
- [x] T073 [US2] Create main conversation page in `frontend/src/app/(dashboard)/conversation/page.tsx`: renders `ConversationPanel`; loads or creates conversation on mount (depends on T066, T072)

**Checkpoint**: Unified conversation with SSE streaming, disclaimer, context persistence, and agent switching all work end-to-end.

---

## Phase 5: User Story 3 — 智能体目录与演示交互 (Priority: P2)

**Goal**: Users can browse all published agents, see formal/demo distinction, click a demo agent to open a bound conversation session.

**Independent Test**: Log in → navigate to `/agents` → see 15 agents (after seeding) → click demo agent → ConversationPanel opens pre-bound to that agent → send one message.

- [x] T074 [P] [US3] Create Agent entity in `frontend/src/domains/agent/entities.ts` (id, name, slug, description, agent_type, capabilities, status, allowed_roles)
- [x] T075 [P] [US3] Create `AgentDomainService` in `frontend/src/domains/agent/services.ts` (filter agents by role, check demo vs formal)
- [x] T076 [US3] Create `useAgents` hook in `frontend/src/features/agent-catalog/hooks/useAgents.ts`: wraps `GET /api/v1/agents` with react-query; supports `type` filter parameter (depends on T074)
- [x] T077 [P] [US3] Create `AgentTypeBadge` component in `frontend/src/features/agent-catalog/components/AgentTypeBadge.tsx`: renders "正式" (blue) or "演示" (amber) badge based on `agent_type`
- [x] T078 [P] [US3] Create `AgentCard` component in `frontend/src/features/agent-catalog/components/AgentCard.tsx`: displays name, description, `AgentTypeBadge`, capabilities list; "进入演示" button for demo agents
- [x] T079 [US3] Create `AgentList` component in `frontend/src/features/agent-catalog/components/AgentList.tsx`: grid layout of `AgentCard` components; empty state when no agents published (depends on T077, T078)
- [x] T080 [US3] Create agents catalog page in `frontend/src/app/(dashboard)/agents/page.tsx`: renders `AgentList` using `useAgents`; tab filter for formal/demo/all (depends on T076, T079)
- [x] T081 [US3] Create agent detail + demo page in `frontend/src/app/(dashboard)/agents/[agentId]/page.tsx`: shows agent capabilities/description; renders `ConversationPanel` with `agentId` prop pre-bound; creates new conversation session bound to this agent on mount (depends on T072, T080)
- [x] T082 [US3] Validate agent catalog Redis cache in `backend/src/infrastructure/db/repositories/agent_repo.py`: ensure `agent:catalog` key is invalidated when any agent is published or archived (adjust T047 implementation if needed)

**Checkpoint**: Agent catalog fully browsable; demo agent conversation works from catalog page.

---

## Phase 6: User Story 4 — 医师个人知识库（RAG）管理 (Priority: P2)

**Goal**: Doctors can upload medical documents, track vectorization status, and use their personal knowledge base to augment AI responses in conversation.

**Independent Test**: Log in as doctor → upload a PDF → wait for status "ready" → enable knowledge base in conversation → send a question about PDF content → AI response cites the document.

- [x] T083 [P] [US4] Create KnowledgeBase, Document, DocumentChunk entities in `backend/src/domains/rag/entities.py` with all invariants from data-model.md (KnowledgeBase owner MUST be doctor role; DocumentChunk embedding dimension = 1536)
- [x] T084 [P] [US4] Create Embedding and ChunkMetadata value objects in `backend/src/domains/rag/value_objects.py`
- [x] T085 [P] [US4] Define `IKnowledgeBaseRepository` abstract interface in `backend/src/domains/rag/repository.py` (methods: `find_by_id`, `find_by_owner`, `save_document`, `save_chunks`, `delete_document`, `similarity_search`)
- [x] T086 [US4] Implement `KnowledgeBaseRepository` in `backend/src/infrastructure/db/repositories/rag_repo.py`: all CRUD operations; `delete_document` cascades to DocumentChunk rows including embeddings (depends on T085, T016)
- [x] T087 [P] [US4] Create pgvector adapter in `backend/src/infrastructure/vector_store/pgvector_adapter.py`: `similarity_search(query_embedding, kb_id, top_k)` using HNSW cosine index; returns ranked DocumentChunk results with similarity scores
- [x] T088 [P] [US4] Create file storage adapter in `backend/src/infrastructure/storage/file_storage.py`: `save_file(file_bytes, filename)` → local volume path (dev); configurable S3-compatible endpoint (prod); `delete_file(path)`
- [x] T089 [US4] Create `ChunkingService` and `VectorSearchService` in `backend/src/domains/rag/services.py`: ChunkingService splits document text into chunks (max 512 tokens, 50-token overlap); VectorSearchService calls pgvector adapter with OpenAI embedding for query (depends on T083, T084)
- [x] T090 [US4] Create Celery task `vectorize_document` in `backend/src/infrastructure/celery_tasks/vectorize_document.py`: extract text from PDF/TXT/DOCX/MD → chunk → embed via OpenAI API → batch insert DocumentChunk rows → update Document.status to `ready` (or `failed` on error); update `kb:{kb_id}:status` in Redis (depends on T087, T088, T089, T024)
- [x] T091 [US4] Implement `RAGApplicationService` in `backend/src/application/rag_service.py`: create/list/delete KnowledgeBase; upload document (save file + create Document + dispatch Celery task); list documents with status; delete document (cascade delete); `rag_query()` for direct knowledge base query (depends on T086, T090)
- [x] T092 [P] [US4] Create RAG Pydantic schemas in `backend/src/interfaces/api/schemas/rag_schemas.py`: `CreateKnowledgeBaseRequest/Response`, `DocumentUploadResponse`, `DocumentListItem`, `RAGQueryRequest/Response` per `contracts/rag-api.md`
- [x] T093 [US4] Implement RAG API router in `backend/src/interfaces/api/routers/rag.py`: all endpoints per `contracts/rag-api.md`; enforce `role = doctor` on all routes; register router in main.py (depends on T091, T092)
- [x] T094 [P] [US4] Create KnowledgeBase and Document entities in `frontend/src/domains/rag/entities.ts` (DocumentStatus: uploading | processing | ready | failed)
- [x] T095 [P] [US4] Create `RAGDomainService` in `frontend/src/domains/rag/services.ts` (file type validation: PDF/TXT/DOCX/MD; file size limit: 50MB)
- [x] T096 [US4] Create `useKnowledgeBase` hook in `frontend/src/features/rag/hooks/useKnowledgeBase.ts`: react-query for KB list, document list (polling every 5s while any document is `processing`), upload mutation, delete mutations (depends on T094)
- [x] T097 [P] [US4] Create `DocumentStatusBadge` component in `frontend/src/features/rag/components/DocumentStatusBadge.tsx`: color-coded status pill (uploading: gray, processing: yellow spinner, ready: green, failed: red) per DocumentStatus
- [x] T098 [P] [US4] Create `DocumentUploader` component in `frontend/src/features/rag/components/DocumentUploader.tsx`: drag-and-drop + click-to-select; validates file type and size (≤50MB); shows upload progress; disabled during processing
- [x] T099 [US4] Create `KnowledgeBaseList` component in `frontend/src/features/rag/components/KnowledgeBaseList.tsx`: lists KBs with document count; expandable document list showing `DocumentStatusBadge` per document; delete button per document and per KB (depends on T097)
- [x] T100 [US4] Create RAG management page in `frontend/src/app/(dashboard)/rag/page.tsx`: doctor role only (middleware enforced); renders `KnowledgeBaseList` + `DocumentUploader`; "创建知识库" modal (depends on T096, T098, T099)
- [x] T101 [US4] Wire RAG retrieval into `rag_qa` LangGraph workflow in `backend/src/infrastructure/llm/langgraph_workflows/rag_qa.py`: add `rag_retriever` node calling `VectorSearchService` when `rag_enabled=true` in session; inject retrieved chunks into LLM context; annotate citations in response metadata (depends on T056, T089)

**Checkpoint**: Doctor uploads a document → status reaches "ready" → RAG-enabled conversation returns cited knowledge base content.

---

## Phase 7: User Story 5 — 智能体批量上架管理 (Priority: P3)

**Goal**: Admin can batch-publish up to 50 agents in one API call; agents become visible in the catalog; seed scripts can initialize all 15 platform agents from JSON config.

**Independent Test**: Run `seed_agents.py --config formal_agents.json` → all 5 formal agents status = published → visible in `GET /agents`; then run with `demo_agents.json` → 10 demo agents also published.

- [x] T102 [P] [US5] Create PublishingBatch and PublishingBatchItem entities in `backend/src/domains/publishing/entities.py` with BatchStatus and ItemStatus enums per data-model.md
- [x] T103 [P] [US5] Create PublishingBatch aggregate root in `backend/src/domains/publishing/aggregates.py`: `add_item()`, `mark_item_success(index, agent_id)`, `mark_item_failed(index, error)`, `finalize()` → sets BatchStatus to `completed` or `partial_failure`
- [x] T104 [P] [US5] Define `IPublishingRepository` abstract interface in `backend/src/domains/publishing/repository.py` (methods: `save_batch`, `find_batch_by_id`, `update_batch_status`)
- [x] T105 [US5] Implement `PublishingRepository` in `backend/src/infrastructure/db/repositories/publishing_repo.py` (depends on T104, T016)
- [x] T106 [US5] Create `BatchPublishingService` in `backend/src/domains/publishing/services.py`: validate each agent config (workflow_config schema check), create Agent entities, dispatch individual `AgentDispatcher.register()` calls, aggregate results via PublishingBatch aggregate (depends on T102, T103, T057)
- [x] T107 [US5] Implement `PublishingApplicationService` in `backend/src/application/publishing_service.py`: receive batch request → create PublishingBatch → dispatch `BatchPublishingService` asynchronously via Celery → return batch_id; `get_batch_status(batch_id)` for polling (depends on T105, T106, T024)
- [x] T108 [P] [US5] Create agent Pydantic schemas in `backend/src/interfaces/api/schemas/agent_schemas.py`: `CreateAgentRequest`, `AgentResponse`, `BatchPublishRequest` (max 50 items), `BatchPublishResponse`, `BatchStatusResponse` per `contracts/agent-api.md`
- [x] T109 [US5] Implement agent API router in `backend/src/interfaces/api/routers/agents.py`: all endpoints per `contracts/agent-api.md` — `GET /agents`, `GET /agents/{id}`, `POST /agents` (admin), `PATCH /agents/{id}` (admin), `POST /agents/{id}/publish` (admin), `POST /agents/{id}/archive` (admin), `POST /agents/batch-publish` (admin), `GET /agents/batches/{id}` (admin); register router in main.py (depends on T107, T108)
- [x] T110 [P] [US5] Create formal agents seed config in `backend/config/agents/formal_agents.json`: 5 entries for `medical_auxiliary`, `document_organizer`, `operations_consultant`, `health_educator`, `rag_qa` with full `workflow_config`, `capabilities`, `allowed_roles`
- [x] T111 [P] [US5] Create demo agents seed config in `backend/config/agents/demo_agents.json`: 10 lightweight demo agent entries (simplified versions of formal agents + 5 additional demo variants); all with `agent_type: demo`
- [x] T112 [US5] Create `seed_agents.py` script in `backend/scripts/seed_agents.py`: reads JSON config, calls `POST /agents/batch-publish` using admin credentials from env, polls `GET /batches/{id}` until `completed`, prints summary (depends on T109, T110, T111)
- [x] T113 [P] [US5] Create `seed_admin.py` script in `backend/scripts/seed_admin.py`: accepts `--username`, `--password`, `--display-name` args; creates User with `role = admin` directly via SQLAlchemy (bypasses API auth); idempotent (skip if username already exists)

**Checkpoint**: All 15 agents published via seed scripts; batch-publish endpoint handles partial failures correctly; agent catalog shows formal/demo distinction.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Audit logging wired to all services, security hardening, shared UI components, Docker validation.

- [x] T114 [P] Inject `AuditService` into all application services in `backend/src/application/`: `auth_service.py` (log login/logout), `conversation_service.py` (log message.sent, message.refused), `rag_service.py` (log document.uploaded, document.deleted, knowledge_base.created, knowledge_base.deleted), `publishing_service.py` (log agent.published, agent.archived, batch.submitted) — covers all 13 AuditAction types
- [x] T115 [P] Add per-user rate limiting middleware in `backend/src/interfaces/api/main.py`: max 30 messages/minute per user for conversation endpoint; return 429 with `retry_after` per `contracts/conversation-api.md`
- [x] T116 [P] Add append-only DB trigger for AuditLog in a new Alembic migration: `BEFORE UPDATE OR DELETE ON audit_logs` → RAISE EXCEPTION; prevents accidental mutation at DB level
- [x] T117 [P] Add security HTTP response headers in `backend/src/interfaces/api/main.py`: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security` (prod mode); configure `Secure` + `HttpOnly` + `SameSite=Strict` on refresh token cookie
- [x] T118 [P] Create shared UI components in `frontend/src/shared/components/`: `Button.tsx` (primary/secondary/danger variants), `Modal.tsx` (dialog with backdrop), `LoadingSpinner.tsx` (animated SVG) — used across all features
- [x] T119 [P] Add global error boundary in `frontend/src/app/layout.tsx` and friendly fallback UI for AI service unavailability (SSE `error` event → inline error message, preserve user input per edge case in spec.md)
- [x] T120 Run full Docker Compose validation per `quickstart.md`: `docker compose up --build` → health check passes → `alembic upgrade head` → seed admin → seed agents → verify catalog shows 15 agents
- [x] T121 [P] Verify HNSW index exists on `document_chunks.embedding` after migration in Docker (`\d document_chunks` in psql); confirm similarity search query plan uses index
- [x] T122 [P] Update `CLAUDE.md` SPECKIT block to reference `specs/001-clinic-ai-platform/tasks.md` as the active task list

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)           → No dependencies — start immediately
Phase 2 (Foundational)    → Depends on Phase 1 — BLOCKS all user stories
Phase 3 (US1 Login)       → Depends on Phase 2 — first P1 story
Phase 4 (US2 Conversation) → Depends on Phase 2 — second P1 story (can parallel with US1 after Phase 2)
Phase 5 (US3 Catalog)     → Depends on Phase 4 (needs ConversationPanel) + Phase 2
Phase 6 (US4 RAG)         → Depends on Phase 4 (rag_qa workflow) + Phase 2
Phase 7 (US5 Batch Pub)   → Depends on Phase 2 only (no hard dependency on US1-4)
Phase 8 (Polish)          → Depends on all Phase 3–7 features desired in scope
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|-----------|-------------------|
| US1 Login (P1) | Phase 2 complete | US2 (after Phase 2) |
| US2 Conversation (P1) | Phase 2 complete | US1 (after Phase 2) |
| US3 Catalog (P2) | US2 (ConversationPanel) | US4, US5 |
| US4 RAG (P2) | US2 (rag_qa workflow stub) | US3, US5 |
| US5 Batch Publish (P3) | Phase 2 only | US3, US4 |

### Within Each User Story

- Backend domain entities → domain services → application service → API router → frontend hooks → frontend components → page

### Parallel Opportunities Per Story

```bash
# US1: After T030 (UserRepository) is done, parallelize:
T031 AuthApplicationService  ||  T032 auth schemas  ||  T034 frontend User entity

# US2: After T051 (base workflow) is done, parallelize:
T052 medical_auxiliary  ||  T053 document_organizer  ||  T054 operations_consultant  ||  T055 health_educator  ||  T056 rag_qa

# US2 frontend: After T066 (useConversation) is done, parallelize:
T067 DisclaimerBanner  ||  T068 StreamingMessage  ||  T069 MessageList  ||  T070 MessageInput  ||  T071 AgentSelector

# US4: After T089 (ChunkingService) is done, parallelize:
T090 Celery task  ||  T087 pgvector adapter (independent)

# US5: Parallelize seed configs:
T110 formal_agents.json  ||  T111 demo_agents.json  ||  T113 seed_admin.py
```

---

## Implementation Strategy

### MVP: P1 Stories Only (US1 + US2)

1. Complete Phase 1 (Setup) → Phase 2 (Foundational)
2. Complete Phase 3 (US1 Login) — verify independently
3. Complete Phase 4 (US2 Conversation) — verify independently
4. **STOP and VALIDATE**: Doctor logs in, sends message to `medical_auxiliary`, sees disclaimer, switches to `document_organizer`, history preserved
5. MVP is demonstrable at this point

### Incremental Delivery

```
Phase 1+2 → Foundation              (Docker + DB + app factory)
+ Phase 3 (US1) → Login MVP         (auth works, role nav visible)
+ Phase 4 (US2) → Conversation MVP  (AI chat works with streaming + disclaimer)
+ Phase 5 (US3) → Catalog           (browse and demo agents from UI)
+ Phase 6 (US4) → RAG               (doctor uploads docs, chat cites them)
+ Phase 7 (US5) → Batch Publish     (admin seeds all 15 agents via scripts)
+ Phase 8       → Production-ready  (audit logging, security, rate limiting)
```

### Parallel Team Strategy

With 2+ developers after Phase 2 completion:
- **Developer A**: US1 (login) → US3 (catalog) after US2 ConversationPanel lands
- **Developer B**: US2 (conversation) → US4 (RAG)
- **Developer C**: US5 (batch publish) — independent from US1-4 after Phase 2

---

## Summary

| Phase | Story | Tasks | Notes |
|-------|-------|-------|-------|
| 1 Setup | — | T001–T013 (13) | Docker, deps, linting |
| 2 Foundation | — | T014–T025 (12) | DB, Redis, app factory, audit infra |
| 3 US1 P1 🎯 | Login | T026–T041 (16) | Auth backend + frontend |
| 4 US2 P1 🎯 | Conversation | T042–T073 (32) | LangGraph + SSE + unified UI |
| 5 US3 P2 | Catalog | T074–T082 (9) | Agent browse + demo mode |
| 6 US4 P2 | RAG | T083–T101 (19) | Vector search + doctor KB |
| 7 US5 P3 | Batch Publish | T102–T113 (12) | Admin publish pipeline + seed scripts |
| 8 Polish | — | T114–T122 (9) | Audit, security, validation |
| **Total** | | **122 tasks** | |

- **[P] parallelizable tasks**: ~60 tasks can run in parallel within their phase
- **MVP scope**: Phases 1–4 (US1 + US2) = 73 tasks
- **Suggested first sprint**: Phase 1 + Phase 2 = 25 tasks (foundation ready)
