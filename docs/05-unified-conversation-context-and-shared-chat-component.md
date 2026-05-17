# 05. 统一会话上下文与共用对话组件

本文档说明所有智能体如何复用同一套前端对话组件、同一组会话表、同一条 SSE 协议和同一个后端主控编排链路。目标是让正式、演示、RAG、多 agent 编排都从同一条路径运行。

## 设计目标

- 所有智能体页面都使用 `ConversationPanel`。
- 对话页可选择智能体；演示详情页可预绑定智能体。
- 用户不指定智能体时，后端主控 agent 自动选择正式子 agent。
- 同一会话保留历史消息和 active agent。
- 医疗安全、免责声明、审计、RAG 权限在后端统一执行。
- 前端只关心统一 SSE 事件，不关心具体 workflow 实现。

## 共用前端组件

入口：

```text
frontend/src/features/conversation/components/ConversationPanel.tsx
```

组件结构：

```text
ConversationPanel
├── AgentSelector
├── MessageList
├── MessageInput
└── useConversation
    └── useSSEStream
```

使用方式：

```tsx
<ConversationPanel />
<ConversationPanel agentId={agentId} />
<ConversationPanel agentId={agentId} conversationId={conversationId} />
```

行为：

| 场景 | 行为 |
| --- | --- |
| `/conversation` | 不预绑定智能体，允许选择或交给后端主控路由 |
| `/agents/{agentId}` | 预绑定智能体，禁用 selector |
| 已有会话 | 通过 `conversationId` 加载历史消息 |
| streaming 中 | 禁用发送和切换，避免并发错乱 |

## 前端发送链路

```text
MessageInput.onSend
  -> ConversationDomainService.validateMessageContent
  -> 如果没有 conversationId，先 POST /api/v1/conversations
  -> 乐观追加 user message
  -> useSSEStream POST /api/v1/conversations/{id}/messages
  -> 监听 start/progress/token/disclaimer/end/error
  -> token 拼接成 streamingContent
  -> end 时追加 assistant message
```

当前 SSE 使用 `fetch` 读取 text/event-stream，而不是浏览器原生 `EventSource`，因此可以在 POST 请求体中携带 `content`、`agent_id`、`rag_enabled`。

## 统一会话数据模型

```text
Conversation
├── id
├── user_id
├── title
├── is_deleted
└── timestamps

ConversationSession
├── id
├── conversation_id
├── active_agent_id
├── context_snapshot
├── rag_enabled
└── last_activity_at

Message
├── id
├── conversation_id
├── session_id
├── agent_id
├── role              # user | assistant | system
├── content
├── has_disclaimer
├── metadata
├── is_deleted
└── created_at
```

原则：

- `Conversation` 是用户看到的一条对话。
- `ConversationSession` 保存当前活跃智能体、RAG 开关和上下文快照。
- `Message.agent_id` 标记 assistant 消息由哪个智能体生成。
- user message 可以没有 `agent_id`，由请求或 session 决定本轮执行智能体。

## API 协议

创建会话：

```text
POST /api/v1/conversations

{
  "title": "可选",
  "agent_id": "uuid 或 null"
}
```

获取会话：

```text
GET /api/v1/conversations/{conversation_id}?limit=50
```

发送消息：

```text
POST /api/v1/conversations/{conversation_id}/messages

{
  "content": "用户输入",
  "agent_id": "uuid 或 null",
  "rag_enabled": true
}
```

更新 session：

```text
PATCH /api/v1/conversations/{conversation_id}/session

{
  "active_agent_id": "uuid 或 null",
  "rag_enabled": true
}
```

删除会话：

```text
DELETE /api/v1/conversations/{conversation_id}
```

## SSE 事件

| 事件 | data |
| --- | --- |
| `start` | `message_id`, `agent_id`, `session_id` |
| `progress` | `stage`, `message`, `agent_id`, `agent_name`, `workflow_type`, `artifacts` |
| `token` | `token` |
| `disclaimer` | `text` |
| `end` | `message_id`, `latency_ms` |
| `error` | `code`, `message` |

`progress` 是当前多 agent 编排的重要可视化协议，典型阶段包括：

- `supervisor`
- `routing`
- `rag_retrieval`
- `rag_retrieval_done`
- `child_start`
- `child_done`

## 后端上下文生命周期

```text
创建会话
  -> Conversation 入库
  -> ConversationSession 入库，可带 active_agent_id

发送消息
  -> 校验 conversation 属于当前用户
  -> 找到 session，不存在则创建
  -> 解析 effective_agent_id = request.agent_id || session.active_agent_id
  -> 校验角色是否可访问智能体
  -> doctor 可更新 rag_enabled
  -> 保存 user message
  -> 读取最近 20 条消息作为 LLM 上下文
  -> 主控编排或指定智能体执行
  -> 保存 assistant message
  -> session.touch 并保存
  -> 写审计日志

切换智能体
  -> PATCH session active_agent_id
  -> 保留同一 conversation 和历史消息
```

当前实现会读取最近 20 条消息作为 LLM 输入；`context_snapshot` 字段存在于 session 中，供后续扩展压缩摘要和 Redis 热缓存。

## 主控与子 agent 上下文

未指定智能体：

```text
用户问题 + 最近消息
  -> 主控 agent 根据正式智能体目录选择 1 个子 agent
  -> 如果问题明显涉及两个能力，追加第 2 个子 agent
  -> 子 agent 分别执行
  -> 主控 agent 汇总最终回复
```

指定智能体：

```text
request.agent_id 或 active_agent_id
  -> 直接执行该 agent 的 workflow
  -> 不再从正式目录自动选择其它 agent
```

跨智能体上下文示例：

```text
用户先用 Medical Auxiliary 整理主诉
  -> assistant message(agent_id=A) 入库

用户切到 Document Organizer
  -> session.active_agent_id=B

用户说：把刚才内容转 SOAP
  -> 后端读取同一 conversation 最近消息
  -> workflow B 基于历史继续回答
```

## RAG 与会话

RAG 开关保存在 `ConversationSession.rag_enabled`：

- 只有 `doctor` 可以更新为 true。
- 普通员工传 `rag_enabled=true` 不会生效。
- `rag_qa` 工作流执行前会检索医生个人知识库。
- RAG 检索命中通过 `progress.artifacts` 返回前端。

## 安全与合规

统一链路强制执行：

| 控制点 | 位置 |
| --- | --- |
| 身份校验 | `get_current_user` |
| 角色校验 | agent allowed_roles / RAG router |
| 会话归属 | `conversation.user_id == current_user.id` |
| RAG 权限 | `user_role == doctor` |
| 免责声明 | `ConversationApplicationService` 统一追加 |
| 审计 | `AuditService.log` |

固定免责声明：

```text
本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。
```

## 单机构假设

当前实现按单机构部署设计：

- 所有用户共用同一套 Agent、Conversation、Message 表。
- 权限由用户角色和 agent `allowed_roles` 控制。
- 未引入 `organization_id`。

如果未来支持多机构，应在以下表和所有查询条件中加入 `organization_id`：

- `users`
- `agents`
- `conversations`
- `conversation_sessions`
- `messages`
- `knowledge_bases`
- `audit_logs`

## 异常恢复

| 场景 | 行为 |
| --- | --- |
| SSE 中断 | 保留用户消息，结束 streaming 状态并显示错误 |
| `event:error` | 展示后端 message，不追加 assistant message |
| 页面刷新 | `GET /conversations/{id}` 恢复历史 |
| token 过期 | `apiClient` refresh，失败后退出登录 |
| Redis 清空 | 当前核心链路依赖 PostgreSQL，可继续恢复 |

## 验收清单

- 所有智能体入口都使用 `ConversationPanel`。
- `/conversation` 不指定智能体时能走主控路由。
- `/agents/{agentId}` 预绑定智能体后 selector 禁用。
- 同一会话切换智能体后历史消息仍可见。
- SSE 能展示 progress 和 streaming token。
- 医师启用 RAG 时能看到检索 progress；员工不能启用。
- assistant 消息落库并带 `has_disclaimer` / metadata。
- 软删除会话后不再出现在用户会话列表。
