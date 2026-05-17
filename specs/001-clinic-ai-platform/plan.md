# Implementation Plan: 私立诊所 AI 助手平台

**Branch**: `001-clinic-ai-platform` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-clinic-ai-platform/spec.md`

## Summary

构建一个私立诊所/私人医生专属 AI 助手平台，采用前后端分离架构（Next.js 14 + Python FastAPI），
基于 LangChain + LangGraph 实现多智能体工作流编排，支持批量智能体上架、医师个人 RAG 知识库管理
和统一会话上下文管理。前后端均遵循 DDD（领域驱动设计）分层架构，数据层使用 PostgreSQL + pgvector
做向量化存储，Redis 做缓存与会话状态管理，全套基础设施通过 Docker Compose 部署。

本轮补充要求是在统一会话体系上增加国际化能力，且语言切换不仅影响页面文案，还必须成为 AI 回复语言、
免责声明语言、错误提示语言和工作流进度文案的统一来源。

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: TypeScript 5+ / Next.js 14+ (App Router)

**Primary Dependencies**:
- Backend: FastAPI, LangChain, LangGraph, SQLAlchemy 2.x, Alembic, Pydantic v2, python-jose (JWT), bcrypt, celery (async doc processing)
- Frontend: Next.js 14, React 18, TailwindCSS
- I18n strategy: repository-local translation dictionaries + session-level locale propagation; avoid adding a new i18n dependency unless routing/SSR complexity later proves it necessary

**Storage**:
- Primary DB: PostgreSQL 16 + pgvector extension (Docker: `pgvector/pgvector:pg16`)
- Cache / Session: Redis 7+ (Docker: `redis:7-alpine`)
- File uploads: Local volume (dev); configurable S3-compatible storage (prod)

**Testing**:
- Backend: pytest + pytest-asyncio + httpx (async test client)
- Frontend: Jest + React Testing Library + Playwright (E2E)
- I18n verification: locale-switch integration tests for session API, SSE events, disclaimer rendering, and AI response language instructions

**Target Platform**: Docker Compose (single-host Linux/macOS); all services containerized.

**Project Type**: Full-stack web application (frontend SPA + backend REST/WebSocket API)

**Performance Goals**:
- Non-AI API endpoints: p95 < 200ms
- AI first-token response: p95 < 3s
- Document vectorization: < 60s for documents < 10MB
- Batch agent publish (15 agents): < 30s total
- Locale switch should not add an extra round-trip before send-message on the happy path

**Constraints**:
- All patient-adjacent data encrypted at rest and in transit (AES-256 / TLS 1.2+)
- Audit logs append-only; retained ≥ 5 years
- Max concurrent users: 50 (single-clinic scale)
- LLM via external API (OpenAI-compatible); no self-hosted model
- Locale handling must be deterministic: same session locale drives UI labels, AI final answer, disclaimer, refusal copy, and progress messages

**Scale/Scope**:
- 5 formal agents + 10 demo agents = 15 agents total
- 4 frontend showcase agents (subset of the 15)
- Max ~200 registered users per deployment
- Initial supported locales: `zh-CN`, `en-US`
- Estimated DB size: < 50GB including vector embeddings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Check | Status |
|---|-----------|-------|--------|
| I | Medical Safety First | All localized AI endpoints must inject the disclaimer in the active locale; refusal logic remains language-independent and still blocks diagnostic/prescription requests | ✅ PASS |
| II | Patient Data Privacy | Locale preference is low-sensitivity product metadata; no new patient-data exposure path is introduced | ✅ PASS |
| III | Strict Service Scope | Internationalization changes only the presentation and generation language of allowed assistance features; it does not expand service scope | ✅ PASS |
| IV | Human-in-the-Loop | Locale switching does not bypass physician review requirements for clinical-adjacent output | ✅ PASS |
| V | Auditability & Observability | Session update and message logs should capture effective locale so reply-language behavior is auditable | ✅ PASS |

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
│   ├── domains/
│   │   ├── auth/
│   │   ├── agent/
│   │   ├── conversation/
│   │   │   ├── entities.py             # add locale to ConversationSession / localized disclaimer helpers
│   │   │   ├── repository.py
│   │   │   └── services.py
│   │   ├── rag/
│   │   ├── publishing/
│   │   └── audit/
│   ├── application/
│   │   └── conversation_service.py     # propagate locale into routing, progress text, supervisor prompt, fallback copy
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── models.py               # persist session locale
│   │   │   ├── repositories/
│   │   │   │   └── conversation_repo.py
│   │   │   └── migrations/
│   │   ├── llm/
│   │   │   ├── langchain_adapter.py
│   │   │   └── langgraph_workflows/    # localized system prompts and disclaimer injection
│   │   └── cache/
│   └── interfaces/
│       └── api/
│           ├── routers/conversations.py
│           └── schemas/conversation_schemas.py
├── tests/
│   ├── domain/
│   ├── application/
│   └── integration/
└── ...

frontend/
├── src/
│   ├── app/
│   ├── domains/
│   │   └── conversation/entities.ts    # session locale typing
│   ├── features/
│   │   └── conversation/
│   │       ├── hooks/
│   │       │   ├── useConversation.ts  # read/update locale, pass through send flow
│   │       │   └── useSSEStream.ts     # consume localized disclaimer / progress / error events
│   │       └── components/             # localized input placeholder / disclaimer banner / language switcher
│   └── shared/
│       ├── api/client.ts
│       └── i18n/                       # lightweight locale dictionaries and helpers
└── ...
```

**Structure Decision**: 保持现有前后端分离 DDD 结构不变，只在 `conversation` 边界上下游补充 locale 透传，并在 frontend `shared/i18n` 建立轻量字典层，避免为了中英双语先引入新的框架级依赖。

## Complexity Tracking

> No Constitution Check violations. No unjustified complexity.

| Design Choice | Justification |
|---------------|---------------|
| Session-level locale as source of truth | 用户可在同一账号下并行打开不同语言会话，且 AI 回复语言必须和当前会话保持一致；仅做全局页面语言无法满足会话级 AI 语言控制 |
| Localized disclaimer catalog instead of free-form model generation | 合规免责声明必须 100% 准确且可测试，不能交给模型自行翻译 |
| Prompt-level locale control plus SSE locale metadata | 同时覆盖主控 agent、子 agent、错误提示和流式 UI 渲染，避免只有最终回答变英文而过程文案仍是中文 |
| Reuse local dictionaries before adding next-intl | 当前需求集中在仪表盘应用与会话模块，先用轻量方案控制改动面和依赖面 |
