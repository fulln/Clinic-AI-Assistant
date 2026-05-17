# 03. 多 Agent 批量上架体系

本文档说明 5 个正式智能体、10 个演示智能体如何通过配置文件、seed 脚本和批量发布接口进入平台目录，并被后端按状态和角色过滤后提供给前端。

## 目标

- 一次性发布 15 个智能体配置。
- 5 个正式智能体承载平台核心能力。
- 10 个演示智能体面向销售演示、试用和轻量场景。
- 批量上架异步处理，返回 `batch_id` 后可轮询状态。
- 单个配置失败不阻断其它配置处理。
- 每次发布保留版本快照，便于审计回溯。

## 配置来源

```text
backend/config/agents/
├── formal_agents.json  # 5 个正式智能体
└── demo_agents.json    # 10 个演示智能体
```

辅助脚本：

```text
backend/scripts/seed_agents.py
```

脚本会登录管理员账号，调用 `POST /api/v1/agents/batch-publish`，然后轮询 `GET /api/v1/agents/batches/{batch_id}`。

## 5 个正式智能体

| 名称 | slug | workflow_type | 定位 |
| --- | --- | --- | --- |
| Medical Auxiliary Assistant | `medical-auxiliary` | `medical-auxiliary` | 医疗辅助沟通、病史和就诊问题整理 |
| Document Organizer | `document-organizer` | `document-organizer` | 医疗文档摘要、归类、结构化 |
| Operations Consultant | `operations-consultant` | `operations-consultant` | 诊所运营、排班、复诊、接待流程 |
| Health Educator | `health-educator` | `health-educator` | 患者健康科普与宣教内容 |
| RAG QA Assistant | `rag-qa` | `rag-qa` | 基于医生个人知识库问答 |

正式智能体参与未指定 `agent_id` 时的主控路由。

## 10 个演示智能体

| 名称 | slug | workflow_type | 映射工作流 |
| --- | --- | --- | --- |
| Demo Medical Auxiliary | `demo-medical-auxiliary` | `demo-medical-auxiliary` | `medical_auxiliary` |
| Demo Document Organizer | `demo-document-organizer` | `demo-document-organizer` | `document_organizer` |
| Demo Operations Consultant | `demo-operations-consultant` | `demo-operations-consultant` | `operations_consultant` |
| Demo Health Educator | `demo-health-educator` | `demo-health-educator` | `health_educator` |
| Demo RAG QA | `demo-rag-qa` | `demo-rag-qa` | `rag_qa` |
| Symptom Checker Demo | `symptom-checker-demo` | `symptom-checker-demo` | `medical_auxiliary` |
| Appointment Helper Demo | `appointment-helper-demo` | `appointment-helper-demo` | `operations_consultant` |
| Medication Info Demo | `medication-info-demo` | `medication-info-demo` | `health_educator` |
| Diet Guide Demo | `diet-guide-demo` | `diet-guide-demo` | `health_educator` |
| Mental Wellness Demo | `mental-wellness-demo` | `mental-wellness-demo` | `health_educator` |

演示智能体主要通过目录或详情页被显式选中，不参与当前未指定智能体时的正式主控候选集。

## Agent 配置模型

最小配置：

```json
{
  "name": "Medical Auxiliary Assistant",
  "slug": "medical-auxiliary",
  "description": "Assists medical staff...",
  "agent_type": "formal",
  "capabilities": ["conversation", "medical_summary"],
  "allowed_roles": ["doctor", "staff", "admin"],
  "workflow_config": {
    "workflow_type": "medical-auxiliary"
  },
  "version": "1.0.0"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `name` | 展示名称 |
| `slug` | 配置和 URL 语义标识 |
| `description` | 目录和详情页描述 |
| `agent_type` | `formal` 或 `demo` |
| `capabilities` | 能力标签，用于展示和工具授权 |
| `allowed_roles` | 可访问角色 |
| `workflow_config.workflow_type` | 调度到 LangGraph workflow 的关键字段 |
| `version` | 发布版本 |

## 批量发布 API

提交：

```text
POST /api/v1/agents/batch-publish
Authorization: Bearer <admin token>

{
  "agents": [ ...agent configs... ]
}
```

响应：

```json
{
  "batch_id": "uuid",
  "status": "pending",
  "total_count": 15,
  "submitted_at": "datetime"
}
```

限制：

- 仅 `admin` 可调用。
- 单批最多 50 个 agent。
- 返回状态码为 `202 Accepted`。

## 异步处理链路

```text
agents router
  -> PublishingApplicationService.submit_batch
  -> PublishingBatchAggregate.create
  -> aggregate.add_item(agent_config)
  -> PublishingRepository.save_batch
  -> Celery process_publishing_batch.delay(batch_id)
  -> worker 逐项校验和发布
  -> 保存 Agent
  -> 保存 AgentPublication 版本快照
  -> 更新 item success/failed
  -> 更新 batch completed/partial_failure/failed
```

查询：

```text
GET /api/v1/agents/batches/{batch_id}
Authorization: Bearer <admin token>
```

响应包含：

| 字段 | 说明 |
| --- | --- |
| `batch_id` | 批次 ID |
| `status` | 批次状态 |
| `total_count` | 总数 |
| `success_count` | 成功数 |
| `failure_count` | 失败数 |
| `items` | 每个配置的状态、agent_id、error |

## 校验规则

发布前必须校验：

- `name`、`slug` 非空。
- `slug` 在平台内唯一或可被安全 upsert。
- `agent_type` 只能是 `formal` 或 `demo`。
- `allowed_roles` 只能包含 `doctor`、`staff`、`admin`。
- `workflow_config.workflow_type` 能被 `AgentDispatcher` 规范化到已注册 workflow。
- `version` 存在，并符合平台版本约定。
- demo agent 不启用高风险工具。
- RAG 能力只能绑定到具备 RAG 检索链路的工作流。

失败项示例：

```json
{
  "index": 3,
  "status": "failed",
  "agent_id": null,
  "error": "Unknown workflow type: demo-unknown-agent"
}
```

## 发布状态

```text
draft -> published -> archived
```

规则：

- `POST /api/v1/agents` 创建草稿。
- `POST /api/v1/agents/{id}/publish` 发布单个智能体。
- `POST /api/v1/agents/{id}/archive` 归档单个智能体。
- 批量发布可创建并直接发布。
- `GET /api/v1/agents` 只返回 `published` 且当前角色可访问的智能体。
- 历史会话保留 `agent_id`，归档不删除历史消息。

## 版本快照

每次发布写入 `AgentPublication`：

```text
AgentPublication
├── agent_id
├── published_by
├── published_at
├── version_snapshot
└── notes
```

`version_snapshot` 必须保存当时完整配置，避免后续配置变更影响审计。

## 前端展示链路

```text
/agents
  -> useAgents({ type })
  -> GET /api/v1/agents?agent_type=formal|demo
  -> 后端按 status=published + allowed_roles 过滤
  -> AgentList / AgentCard 展示
  -> /agents/{agentId}
  -> ConversationPanel(agentId, conversationId)
```

展示要求：

- 正式和演示有明确标签。
- 普通员工只看到 `allowed_roles` 包含 `staff` 的智能体。
- 医师可看到授权给 `doctor` 的智能体。
- 管理员管理草稿、发布、归档应通过管理接口完成；普通目录仍以已发布可访问列表为准。

## 审计

应记录：

- 批量提交：`batch.submitted`
- 发布成功：`agent.published`
- 发布失败：失败原因、配置 index
- 归档：`agent.archived`
- 操作者、角色、资源 ID、时间、结果

## 验收清单

- `formal_agents.json` 中 5 个正式智能体可发布。
- `demo_agents.json` 中 10 个演示智能体可发布。
- 批量接口返回 `batch_id`，并可轮询每项结果。
- 单项失败不影响其它有效配置发布。
- `GET /agents?agent_type=demo` 能看到已发布演示智能体。
- 指定演示智能体发起对话时，demo `workflow_type` 能正确映射到正式工作流。
