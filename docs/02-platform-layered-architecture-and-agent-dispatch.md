# 02. 平台分层架构与智能体调度链路

本文档说明平台的前后端分层、DDD 边界、基础设施职责，以及一次用户消息如何从前端进入后端主控 agent，再被路由到一个或多个 LangGraph 子工作流。

## 总体架构

```text
Next.js App Router
  -> FastAPI routers / SSE
  -> Application services
  -> Domain entities / services / repositories
  -> Infrastructure adapters
  -> PostgreSQL / Redis / pgvector / Celery / LLM Provider / File Storage
```

核心栈：

| 层级 | 技术 |
| --- | --- |
| 前端 | Next.js, React, TypeScript, TailwindCSS, Zustand, TanStack Query |
| API | FastAPI, Pydantic |
| 应用层 | Python application services |
| 领域层 | DDD-style entities, value objects, repository ports |
| 智能体 | LangChain adapter + LangGraph workflow modules |
| 数据库 | PostgreSQL + SQLAlchemy + Alembic |
| 向量检索 | pgvector |
| 异步任务 | Celery |
| 缓存 | Redis |

## 后端目录边界

```text
backend/src/
├── interfaces/         # FastAPI routers、schemas、SSE/WebSocket
├── application/        # 用例编排、事务边界、跨领域协调
├── domains/            # 实体、值对象、领域服务、仓储接口
└── infrastructure/     # DB、LLM、文件、向量库、Celery、Redis
```

| 层 | 当前代表文件 | 不应承担的职责 |
| --- | --- | --- |
| Interface | `interfaces/api/routers/*.py` | 不写复杂业务规则 |
| Application | `application/*_service.py` | 不直接依赖前端协议 |
| Domain | `domains/*` | 不调用数据库、HTTP、LLM SDK |
| Infrastructure | `infrastructure/*` | 不决定业务权限和领域规则 |

## 限界上下文

| 上下文 | 职责 |
| --- | --- |
| Auth | 用户、角色、密码校验、token |
| Agent | 智能体元数据、状态、workflow 映射 |
| Conversation | 会话、消息、上下文快照、免责声明 |
| RAG | 知识库、文档、分块、向量检索 |
| Publishing | 批量上架、发布状态、版本快照 |
| Audit | 追加式审计日志 |

## 请求入口

主要 API：

| API | 作用 |
| --- | --- |
| `POST /api/v1/auth/login` | 登录 |
| `GET /api/v1/agents` | 列出当前用户可访问的 published 智能体 |
| `POST /api/v1/agents/batch-publish` | 管理员批量上架 |
| `POST /api/v1/conversations` | 创建会话 |
| `POST /api/v1/conversations/{id}/messages` | 发送消息并返回 SSE |
| `PATCH /api/v1/conversations/{id}/session` | 切换智能体或 RAG 开关 |
| `POST /api/v1/rag/query` | 医师个人知识库检索 |

## 智能体调度模型

后端核心调度类：

| 类 | 文件 | 职责 |
| --- | --- | --- |
| `ConversationApplicationService` | `application/conversation_service.py` | 会话用例、主控 agent 编排、SSE |
| `AgentDispatcher` | `domains/agent/services.py` | workflow_type 规范化与工作流调用 |
| `LLMAdapter` | `infrastructure/llm/langchain_adapter.py` | 外部 LLM 访问适配 |
| `*Workflow` | `infrastructure/llm/langgraph_workflows/` | 子 agent 执行逻辑 |

调度输入来自统一对话接口：

```json
{
  "conversation_id": "uuid",
  "user_id": "uuid",
  "content": "用户消息",
  "agent_id": "uuid 或 null",
  "rag_enabled": true
}
```

当前实现支持两种模式：

| 模式 | 触发条件 | 行为 |
| --- | --- | --- |
| 强制指定 | 请求带 `agent_id` 或 session 有 `active_agent_id` | 直接执行该智能体对应 workflow |
| 主控路由 | 未指定智能体 | 从已发布正式智能体中选择 1 个，必要时追加第 2 个子 agent |

## 主控 agent 编排链路

```text
POST /conversations/{id}/messages
  -> 校验 conversation 属于当前用户
  -> 找到或创建 ConversationSession
  -> 解析 effective_agent_id
  -> 校验用户角色是否可访问该智能体
  -> doctor 可更新 session.rag_enabled
  -> 保存 user message
  -> 读取最近 20 条消息作为共享上下文
  -> SSE event:start
  -> build_orchestra_steps
     -> 有指定智能体：单步执行
     -> 无指定智能体：主控 LLM 从正式 agent 目录选择
     -> 规则兜底：按关键词选择 workflow
  -> 每个 step 调用 AgentDispatcher.dispatch
  -> 必要时执行个人 RAG 检索
  -> 主控 LLM 汇总子 agent 输出
  -> SSE event:token
  -> 追加免责声明
  -> SSE event:disclaimer / end
  -> 保存 assistant message
  -> 保存 session 并写入审计
```

SSE 事件：

| 事件 | 用途 |
| --- | --- |
| `start` | 返回 message_id、agent_id、session_id |
| `progress` | 返回主控/子 agent/RAG 的阶段状态 |
| `token` | 返回最终回复 token |
| `disclaimer` | 通知前端本轮包含免责声明 |
| `end` | 返回 message_id 和 latency_ms |
| `error` | 返回错误码和错误消息 |

## Workflow 映射

正式配置：`backend/config/agents/formal_agents.json`

| 配置 workflow_type | 规范化后 | 工作流模块 |
| --- | --- | --- |
| `medical-auxiliary` | `medical_auxiliary` | `medical_auxiliary.py` |
| `document-organizer` | `document_organizer` | `document_organizer.py` |
| `operations-consultant` | `operations_consultant` | `operations_consultant.py` |
| `health-educator` | `health_educator` | `health_educator.py` |
| `rag-qa` | `rag_qa` | `rag_qa.py` |

演示配置：`backend/config/agents/demo_agents.json`

演示 agent 的 `workflow_type` 可以是 demo slug，例如 `demo-medical-auxiliary`。`AgentDispatcher.normalize_workflow_type` 会把它映射到对应正式工作流。

## RAG 注入规则

RAG 只对医师生效：

```text
request.rag_enabled 或 session.rag_enabled
  -> user_role 必须是 doctor
  -> workflow 为 rag_qa 时检索当前医生全部个人知识库
  -> pgvector top_k 检索
  -> chunks 作为 state.rag_chunks 注入 workflow
  -> progress 事件带回可展示的 rag artifacts
```

如果不是医师，`rag_enabled` 不会被 session 接受，RAG 检索返回空结果。

## 数据职责

| 数据 | 真源 | 说明 |
| --- | --- | --- |
| 用户、角色 | PostgreSQL | 登录和鉴权依据 |
| 智能体配置 | PostgreSQL | seed / batch publish 写入 |
| 会话、消息 | PostgreSQL | 历史恢复和审计依据 |
| session context | PostgreSQL 为真源，Redis 可作为热缓存 | 当前实现以数据库仓储为主 |
| 文档原文件 | 本地上传目录 | 路径临时存放在文档记录中供 worker 使用 |
| 文档向量 | PostgreSQL pgvector | RAG similarity search |
| 审计 | PostgreSQL | 追加式记录 |

## 容错

| 场景 | 当前行为 |
| --- | --- |
| 会话不存在或不属于当前用户 | 404 |
| 角色不能访问指定智能体 | 403 |
| workflow_type 未知 | SSE `event:error`，code 为 `agent_error` |
| 主控 LLM 路由失败 | 规则兜底选择 workflow |
| RAG 无知识库或非医师 | 返回空 chunks，流程继续 |
| 子 agent 执行异常 | SSE error，本轮 assistant message 不落库 |

## 验收清单

- Router 只做协议适配、依赖注入和错误转换，业务逻辑在 application/domain。
- `GET /agents` 只返回当前角色可访问的已发布智能体。
- 指定 `agent_id` 时只执行该智能体；不指定时走主控路由。
- `workflow_type` 支持 kebab-case、snake_case 和 demo alias。
- SSE 至少覆盖 `start/progress/token/end/error`。
- 医疗免责声明由统一会话链路追加，不依赖前端拼接。
