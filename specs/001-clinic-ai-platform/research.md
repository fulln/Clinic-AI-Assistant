# Research: 私立诊所 AI 助手平台

**Phase 0 Output** | **Date**: 2026-05-17 | **Feature**: 001-clinic-ai-platform

## Technology Stack Decisions

### Decision 1: Frontend Framework
- **Decision**: Next.js 14+ (App Router)
- **Rationale**: SSR/SSG hybrid rendering suits the dashboard + public demo pages; App Router enables server components for reduced client bundle; TypeScript-first ecosystem aligns with DDD type safety requirements.
- **Alternatives considered**: Nuxt.js (Vue) — team alignment with React preferred; Remix — less mature ecosystem for this use case; CRA/Vite SPA — lacks SSR needed for initial load performance.

### Decision 2: Backend Framework
- **Decision**: FastAPI (Python 3.11+)
- **Rationale**: Async-native (asyncio), automatic OpenAPI schema generation for contract documentation, Pydantic v2 models align with DDD value objects, excellent LangChain integration.
- **Alternatives considered**: Django REST — heavier, sync-first, less suitable for streaming AI responses; Flask — too low-level for this complexity.

### Decision 3: Agent Orchestration
- **Decision**: LangGraph for multi-step agent workflows + LangChain for tool/chain composition
- **Rationale**: LangGraph provides stateful graph-based orchestration with explicit state management — matches the "agent scheduling" requirement; supports interrupt/resume for human-in-the-loop checkpoints (Constitution Principle IV). LangChain provides the tool abstractions and LLM adapters.
- **Alternatives considered**: AutoGen — less deterministic for production; CrewAI — limited state management; Plain LangChain without LangGraph — insufficient for complex multi-step workflows.

### Decision 4: Vector Storage
- **Decision**: PostgreSQL 16 + pgvector extension
- **Rationale**: Unified storage (relational + vector) reduces operational complexity; pgvector provides HNSW index for efficient similarity search; integrates with existing SQLAlchemy ORM; Docker-deployable via `pgvector/pgvector:pg16` image. Avoids introducing a separate vector DB (Qdrant/Weaviate) for a clinic-scale deployment (<200 users).
- **Alternatives considered**: Qdrant — excellent performance but separate service to manage; Chroma — suitable for dev but less production-hardened; Weaviate — over-engineered for this scale.

### Decision 5: Caching & Session Storage
- **Decision**: Redis 7+ (via Docker)
- **Rationale**: Session token storage + conversation context cache + agent state cache. Redis Streams can support future event-driven patterns. `redis:7-alpine` Docker image is lightweight.
- **Alternatives considered**: Memcached — lacks pub/sub and persistence options needed for session; In-memory Python dict — not distributed, loses state on restart.

### Decision 6: Authentication
- **Decision**: JWT (access token 30min + refresh token 7 days) stored in httpOnly cookies; backend issues tokens; frontend uses Next.js middleware for route protection.
- **Rationale**: Stateless JWT reduces DB lookups per request; httpOnly cookies prevent XSS token theft; refresh token rotation aligns with security best practices. Redis stores revoked token list for logout.
- **Alternatives considered**: Session-based auth — requires sticky sessions or shared Redis session store (adds complexity); NextAuth.js — introduces its own DB schema requirements that conflict with DDD domain model.

### Decision 7: DDD Architecture Pattern
- **Decision**: Hexagonal Architecture (Ports & Adapters) applied to both backend and frontend
- **Rationale**: Domain logic isolated from infrastructure (DB, Redis, LLM APIs); enables testing of domain without external dependencies; clear separation between domain, application, infrastructure, and interface layers.
- **Backend layers**: Domain → Application Services → Infrastructure Adapters → FastAPI Interface
- **Frontend layers**: Domain Entities/Services → Feature modules (bounded contexts) → Next.js App Router (interface)
- **Alternatives considered**: Layered architecture (traditional MVC) — domain logic tends to leak into controllers; Clean Architecture — equivalent but hexagonal naming more widely understood in Python community.

### Decision 8: Multi-Agent Dispatch Strategy
- **Decision**: Central AgentDispatcher (domain service) routes conversation messages to the appropriate LangGraph workflow based on agent_id; each agent workflow is a registered LangGraph StateGraph.
- **Rationale**: Decouples routing logic from individual agents; supports runtime agent registration (batch publishing); enables conversation context injection as LangGraph state.
- **Alternatives considered**: Direct agent invocation from API layer — bypasses domain routing logic; LangGraph multi-agent supervisor — harder to integrate with the custom publishing/catalog system.

### Decision 9: Unified Session Context
- **Decision**: ConversationSession aggregate stores messages + current agent context in PostgreSQL; hot context (last N messages + active agent state) cached in Redis with 24h TTL.
- **Rationale**: Persistence in PostgreSQL ensures audit trail compliance (Constitution Principle V); Redis cache ensures low-latency context retrieval for active conversations. LangGraph checkpointer uses this Redis cache as its state backend.
- **Alternatives considered**: Store all context in Redis only — not durable enough for 5-year audit requirement; Store all in PostgreSQL — too slow for frequent reads during streaming.

### Decision 10: Infrastructure / Deployment
- **Decision**: Docker Compose for local dev and initial production; services: postgres-pgvector, redis, backend, frontend, nginx (reverse proxy).
- **Rationale**: User explicitly specified Docker; Docker Compose is sufficient for single-clinic scale; pgvector available as official Docker image.
- **Alternatives considered**: Kubernetes — over-engineered for <200 users single deployment; plain bare-metal — loses reproducibility.

### Decision 11: Internationalization Strategy
- **Decision**: Use a session-level `locale` (`zh-CN` / `en-US`) as the source of truth for conversation language, and reuse repository-local translation dictionaries for frontend and backend copy.
- **Rationale**: The requirement is not only UI translation but deterministic AI response localization. A session-scoped locale lets one user keep multiple conversations in different languages without collision. Local dictionaries keep copy reviewable and avoid adding a new dependency prematurely.
- **Alternatives considered**: Browser-language auto-detection only — not stable enough for clinical workflows; global per-user locale only — cannot support mixed-language parallel conversations; immediate adoption of a full i18n framework — heavier than needed for the current two-locale dashboard scope.

### Decision 12: AI Reply Language Control
- **Decision**: Enforce reply language through explicit prompt instructions on both supervisor and child-agent workflows, while keeping disclaimer/refusal/error copy outside the model as localized constants.
- **Rationale**: Prompt instructions are the least invasive way to make existing LangGraph workflows reply in the selected language. Compliance copy must not be model-generated because wording must remain exact and testable.
- **Alternatives considered**: Post-generation translation pass — adds latency and may distort medical nuance; separate model deployments per language — unnecessary operational complexity; letting the model infer language from the latest user message — brittle when UI language and message language differ.

### Decision 13: SSE Localization Surface
- **Decision**: Localize not only final assistant content but also SSE `progress`, `disclaimer`, and error payloads, with the effective locale included in session state and optionally echoed in stream metadata.
- **Rationale**: If only the final answer is translated, the user still sees mixed-language UX during streaming. Progress and error payloads originate from backend orchestration, so they must use the same locale contract.
- **Alternatives considered**: Frontend-only translation of backend status keys — possible for fixed progress labels, but backend-generated detail text and disclaimer payload still require locale-aware source copy.

## LangGraph Agent Architecture

Each agent is a `StateGraph` with these standard nodes:
1. `context_loader` — loads conversation history + user's RAG knowledge base (if doctor + RAG enabled)
2. `intent_classifier` — classifies request; rejects if diagnostic/prescriptive intent detected
3. `tool_executor` — executes agent-specific tools (document search, RAG query, operation lookup)
4. `response_generator` — generates a response in the effective session locale with mandatory localized disclaimer injection
5. `context_saver` — persists updated conversation state

Formal agents (5): medical_auxiliary, document_organizer, operations_consultant, health_educator, rag_qa
Demo agents (10): lightweight versions of the above with simplified tool sets and reduced context windows.

## DDD Bounded Contexts

| Context | Aggregate Roots | Key Invariants |
|---------|----------------|----------------|
| Auth | User | Password MUST be hashed; Role MUST be one of {doctor, staff, admin} |
| Agent | Agent, AgentCatalog | Published agent MUST have valid LangGraph config; Demo agents MUST be tagged |
| Conversation | Conversation, ConversationSession | Session MUST belong to exactly one User; Context MUST be auditable |
| RAG | KnowledgeBase, Document | KnowledgeBase MUST belong to exactly one doctor User |
| Publishing | PublishingBatch | Batch MUST process all items; partial failures MUST be reported individually |

## Security Research Findings

- pgvector queries susceptible to prompt injection via embedded documents → implement content sanitization before vectorization.
- LangGraph tool calls must validate output against Constitution Principle I before returning to user.
- JWT refresh token rotation: invalidate old token on refresh to prevent token reuse attacks.
- Redis session keys must use user-scoped namespacing: `session:{user_id}:{session_id}`.
- All API endpoints must validate role claims from JWT, not rely solely on frontend routing.
- Localized disclaimer and refusal copy must be version-controlled constants reviewed by product/compliance, not free-form prompt text.
