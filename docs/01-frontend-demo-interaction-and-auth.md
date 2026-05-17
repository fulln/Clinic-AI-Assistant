# 01. 前端演示交互与登录鉴权链路

本文档说明前端如何提供统一的登录、角色导航、智能体目录、演示智能体详情页和对话入口。当前实现以 Next.js App Router 为入口，所有正式和演示智能体最终都复用 `ConversationPanel`。

## 目标

- 支持账号密码登录，并在前端缓存 access token 与用户信息。
- 医师、员工、管理员看到不同的导航入口和智能体能力。
- 正式智能体和演示智能体共用目录、详情页和统一对话组件。
- 演示详情页可以预绑定指定智能体，保证演示路径稳定。
- 前端只做体验层权限过滤，后端仍是最终鉴权边界。

## 前端结构

```text
frontend/src/app/
├── (auth)/login/page.tsx
├── (dashboard)/layout.tsx
├── (dashboard)/agents/page.tsx
├── (dashboard)/agents/[agentId]/page.tsx
├── (dashboard)/conversation/page.tsx
├── (dashboard)/rag/page.tsx
└── middleware.ts

frontend/src/features/
├── auth/
├── agent-catalog/
├── conversation/
└── rag/

frontend/src/shared/
├── api/client.ts
├── components/
└── store/authStore.ts
```

关键文件：

| 文件 | 职责 |
| --- | --- |
| `features/auth/components/LoginForm.tsx` | 登录表单 |
| `features/auth/hooks/useAuth.ts` | 登录、登出、获取当前用户 |
| `shared/store/authStore.ts` | Zustand 持久化登录态 |
| `shared/api/client.ts` | Axios client、token 注入、401 refresh |
| `app/(dashboard)/layout.tsx` | 登录后壳层和导航 |
| `app/(dashboard)/agents/page.tsx` | 智能体目录 |
| `app/(dashboard)/agents/[agentId]/page.tsx` | 智能体详情和预绑定对话 |
| `features/conversation/components/ConversationPanel.tsx` | 统一对话组件 |

## 登录链路

```text
LoginForm
  -> useAuth.login(username, password)
  -> POST /api/v1/auth/login
  -> 后端校验用户和密码
  -> 返回 access_token + user，并设置 refresh cookie
  -> authStore.setAuth(token, user)
  -> apiClient 后续请求注入 Authorization header
  -> 跳转登录后页面
```

接口：

| 接口 | 用途 |
| --- | --- |
| `POST /api/v1/auth/login` | 登录，返回 access token 和 user |
| `GET /api/v1/auth/me` | 校验当前 token 并恢复用户信息 |
| `POST /api/v1/auth/refresh` | 使用 refresh cookie 获取新 access token |
| `POST /api/v1/auth/logout` | 登出并清理 refresh cookie |

前端缓存规则：

- `authStore` 保存 `accessToken`、`user`、`isAuthenticated`。
- 浏览器运行时把 token 同步到 `window.__authToken`，供 `apiClient` 与 SSE hook 使用。
- `apiClient` 对普通 HTTP 请求注入 `Authorization: Bearer <token>`。
- 401 时尝试调用 `/api/v1/auth/refresh`；刷新失败则清理本地登录态。

## 角色与导航

角色：

| 角色 | 前端能力 |
| --- | --- |
| `doctor` | 对话、智能体目录、个人 RAG |
| `staff` | 对话、智能体目录；无个人 RAG |
| `admin` | 对话、智能体目录；管理能力由后端接口控制 |

当前前端导航由 `app/(dashboard)/layout.tsx` 生成：

```text
读取 authStore.user.role
  -> 基础导航：智能体、对话
  -> doctor/admin 增加：个人知识库
  -> staff 不展示 RAG 入口
```

注意：隐藏导航不是安全边界。`/api/v1/rag/*` 由后端 `require_role(UserRole.DOCTOR)` 强制限制，普通员工即使直接请求接口也会被拒绝。

## 智能体目录链路

```text
/agents
  -> useAgents({ type })
  -> GET /api/v1/agents?agent_type=formal|demo
  -> 后端只返回 published 且当前角色可访问的智能体
  -> AgentList 渲染 AgentCard
  -> 点击卡片进入 /agents/{agentId}
```

当前后端 `GET /api/v1/agents` 返回数组 `AgentResponse[]`，不是 `{ items: [...] }` 包装对象。前端目录 hook 已按数组处理。

目录展示要求：

- 支持“全部 / 正式 / 演示”筛选。
- 演示智能体展示“演示”标识。
- 卡片显示名称、描述、能力标签和可访问角色。
- 不在前端展示后端未授权返回的智能体。

## 演示详情和预绑定对话

```text
/agents/{agentId}
  -> GET /api/v1/agents/{agentId}
  -> POST /api/v1/conversations { agent_id }
  -> 渲染 <ConversationPanel agentId={agentId} conversationId={conversationId} />
```

`ConversationPanel` 收到 `agentId` 后：

- 将该智能体设为初始选中项。
- 禁用 `AgentSelector`，避免演示过程中切换到其它智能体。
- 发送消息时把 `agent_id` 传给后端，后端按该智能体的 `workflow_config.workflow_type` 执行。

全局 `/conversation` 页面则渲染 `<ConversationPanel />`，允许用户通过 `AgentSelector` 手动选择智能体；不指定智能体时，后端主控 agent 会根据用户问题在正式智能体中自动路由。

## 4 个重点演示入口

当前演示配置位于 `backend/config/agents/demo_agents.json`，其中 4 个重点销售演示入口为：

| 演示智能体 | slug | 路由到的工作流 | 典型脚本 |
| --- | --- | --- | --- |
| Demo Medical Auxiliary | `demo-medical-auxiliary` | `medical_auxiliary` | 整理主诉、病史摘要、就诊前问题 |
| Demo Document Organizer | `demo-document-organizer` | `document_organizer` | 将粘贴文本整理成结构化摘要或 SOAP |
| Demo Operations Consultant | `demo-operations-consultant` | `operations_consultant` | 排班、接待、复诊提醒流程建议 |
| Demo Health Educator | `demo-health-educator` | `health_educator` | 面向患者的健康科普内容 |

它们和其它 demo agent 一样走统一目录、详情页、会话、SSE、审计和免责声明链路。

## 对话交互状态

`useConversation` 负责：

- 没有会话时自动创建会话。
- 发送用户消息前做本地内容校验。
- 将用户消息乐观追加到消息列表。
- 通过 `useSSEStream` 监听 `start`、`progress`、`token`、`disclaimer`、`end`、`error`。
- 流式结束后追加 assistant message。
- 加载历史会话时调用 `GET /api/v1/conversations/{conversation_id}`。

异常处理：

| 场景 | 前端行为 |
| --- | --- |
| 未登录 | middleware 或接口错误引导登录 |
| token 过期 | `apiClient` refresh，失败后清理登录态 |
| SSE 错误 | 展示错误，结束 streaming 状态 |
| streaming 中切换智能体 | `AgentSelector` 禁用 |
| 普通员工访问 RAG | 页面隐藏入口，接口由后端拒绝 |

## 验收清单

- 医师登录后能看到智能体、对话、个人知识库入口。
- 普通员工登录后看不到个人知识库入口，直接请求 RAG 接口被拒绝。
- `/agents` 能按正式/演示筛选并展示已发布智能体。
- 进入演示详情页后，`ConversationPanel` 预绑定该智能体且不能切换。
- 全局对话页可以手动选择智能体，也可以不指定智能体交给后端主控路由。
- 页面刷新后 token 能恢复；access token 失效时 refresh 或退出登录。
