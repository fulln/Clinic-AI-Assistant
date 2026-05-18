# 04. 医师个人 RAG 管理链路

本文档说明医师个人知识库的创建、文档上传、异步向量化、pgvector 检索、对话注入和权限控制。当前 RAG 能力严格限制为 `doctor` 角色。

## 目标

- 医师可创建和管理自己的知识库。
- 医师可上传文档，后台异步解析、分块、向量化。
- RAG 检索结果可注入 `rag_qa` 工作流和统一对话链路。
- 普通员工不能访问 RAG 页面和接口。
- RAG 回答必须带来源信息，并保持医疗安全边界。

## 模块结构

```text
frontend/src/app/(dashboard)/rag/page.tsx
frontend/src/features/rag/
├── components/KnowledgeBaseList.tsx
├── components/DocumentUploader.tsx
├── components/DocumentStatusBadge.tsx
└── hooks/useKnowledgeBase.ts

backend/src/interfaces/api/routers/rag.py
backend/src/application/rag_service.py
backend/src/domains/rag/
├── entities.py
├── repository.py
├── services.py
└── value_objects.py

backend/src/infrastructure/
├── celery_tasks/vectorize_document.py
├── vector_store/pgvector_adapter.py
├── storage/file_storage.py
└── db/repositories/rag_repo.py
```

## 权限模型

后端 RAG router 使用：

```text
require_role(UserRole.DOCTOR)
```

核心规则：

| 角色 | RAG 权限 |
| --- | --- |
| `doctor` | 创建、查看、上传、删除自己的知识库和文档 |
| `staff` | 无访问权限 |
| `admin` | 当前 RAG router 未放开；管理能力需另设接口 |

知识库所有权校验：

```text
current_user.role == doctor
AND knowledge_base.owner_id == current_user.id
```

## 数据模型

```text
KnowledgeBase
├── id
├── owner_id
├── name
├── description
├── document_count
├── created_at
└── updated_at

Document
├── id
├── kb_id
├── filename
├── file_size_bytes
├── mime_type
├── status              # uploading | processing | ready | failed
├── chunk_count
├── error_message
├── created_at
└── processed_at

DocumentChunk
├── id
├── document_id
├── chunk_index
├── content
├── embedding
├── token_count
└── metadata
```

当前实现中，上传后的原文件路径临时存放在 `Document.error_message`，供 Celery worker 定位文件；处理成功后应清理该字段，失败时写入真实错误消息。接口列表文档时仅在 `failed` 状态暴露 `error_message`，避免泄露内部路径。

## 知识库接口

| 接口 | 说明 |
| --- | --- |
| `POST /api/v1/rag/knowledge-bases` | 创建知识库 |
| `GET /api/v1/rag/knowledge-bases` | 查询当前医生的知识库 |
| `DELETE /api/v1/rag/knowledge-bases/{kb_id}` | 删除自己的知识库 |

创建链路：

```text
/rag 页面
  -> useKnowledgeBase.createKnowledgeBase
  -> POST /api/v1/rag/knowledge-bases
  -> RAGApplicationService.create_kb
  -> 校验 doctor
  -> KnowledgeBaseRepository.save_kb
  -> AuditLog KNOWLEDGE_BASE_CREATED
```

## 文档上传链路

接口：

```text
POST /api/v1/rag/knowledge-bases/{kb_id}/documents
Content-Type: multipart/form-data
field: file
```

当前响应状态码为 `201 Created`，返回 `document_id`、文件名、文件大小、状态和创建时间。

处理链路：

```text
DocumentUploader
  -> POST multipart file
  -> router 读取 UploadFile bytes
  -> RAGApplicationService.upload_document
  -> 校验 kb 存在且 owner_id 匹配
  -> FileStorage.save_file
  -> Document(status=uploading, error_message=file_path) 入库
  -> AuditLog DOCUMENT_UPLOADED
  -> vectorize_document.delay(document_id)
  -> 返回 DocumentUploadResponse
```

异步向量化：

```text
vectorize_document(document_id)
  -> 读取 Document
  -> 通过暂存 file_path 读取原文件
  -> 解析文本
  -> 分块
  -> 调用 embedding provider
  -> 批量写入 DocumentChunk + pgvector embedding
  -> Document.status = ready
  -> 写入 chunk_count / processed_at
  -> 失败时 Document.status = failed + error_message
```

文档查询与删除：

| 接口 | 说明 |
| --- | --- |
| `GET /api/v1/rag/knowledge-bases/{kb_id}/documents` | 查询知识库文档 |
| `DELETE /api/v1/rag/knowledge-bases/{kb_id}/documents/{doc_id}` | 删除文档和向量块 |

## 向量策略

推荐默认值：

| 项 | 建议 |
| --- | --- |
| chunk size | 800-1200 tokens |
| overlap | 100-200 tokens |
| embedding model | `EMBEDDING_MODEL`，默认 `text-embedding-3-small` |
| embedding key | `EMBEDDING_API_KEY` 或 `OPENAI_API_KEY` |
| embedding base URL | `EMBEDDING_BASE_URL` 或 `OPENAI_BASE_URL` |
| vector dim | 与模型输出一致；可通过 `EMBEDDING_DIMENSIONS` 控制 |
| top_k | 默认 5 |

metadata 建议：

```json
{
  "filename": "clinical_guide.pdf",
  "page_number": 12,
  "section_title": "随访管理",
  "knowledge_base_id": "uuid"
}
```

## 独立 RAG 查询

接口：

```text
POST /api/v1/rag/query

{
  "knowledge_base_id": "uuid",
  "query": "请总结随访要点",
  "top_k": 5
}
```

链路：

```text
RAGApplicationService.rag_query
  -> 校验 kb owner
  -> 调用 embedding provider 生成 query embedding
  -> KnowledgeBaseRepository.similarity_search
  -> AuditLog KB_QUERIED
  -> 返回 chunks、metadata、similarity_score
```

## 对话中启用 RAG

前端发送：

```json
{
  "content": "请根据我的知识库总结高血压随访要点",
  "agent_id": null,
  "rag_enabled": true
}
```

后端规则：

```text
ConversationApplicationService.stream_message
  -> 只有 user_role == doctor 时接受 rag_enabled
  -> 未指定 agent 时，主控路由倾向选择 rag_qa
  -> rag_qa step 执行前检索该医生所有个人知识库
  -> chunks 注入 AgentDispatcher.dispatch(..., rag_chunks)
  -> progress 事件返回 rag artifacts
  -> 最终回复由主控 agent 汇总并追加免责声明
```

RAG artifacts 用于前端展示检索来源，包括文件名、知识库名、相似度、chunk 摘要和文档 ID。

## Prompt 与安全约束

RAG 工作流必须遵守：

- 优先基于检索片段回答。
- 检索结果不足时明确说明当前知识库依据不足。
- 不得把文档内容外推成确定诊断或处方。
- 尽量展示来源文档名、页码或章节 metadata。
- 医疗相关回复统一追加免责声明。

免责声明：

```text
本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。
```

## 状态展示

| Document.status | 前端展示 | 用户动作 |
| --- | --- | --- |
| `uploading` | 已上传，等待处理 | 等待刷新 |
| `processing` | 向量化中 | 等待刷新 |
| `ready` | 可检索 | 可用于 RAG |
| `failed` | 处理失败 | 查看错误，重新上传 |

## 验收清单

- 医师可以创建知识库并看到自己的知识库列表。
- 普通员工请求任一 `/api/v1/rag/*` 接口被拒绝。
- 上传文档返回 `document_id`，随后 Celery worker 可处理为 `ready`。
- `GET documents` 不在非失败状态泄露内部文件路径。
- `POST /api/v1/rag/query` 返回相似片段和 metadata。
- 对话启用 RAG 后，`progress` 中能看到检索阶段和命中文档。
- 删除文档后，对应 chunks 不再被检索命中。
