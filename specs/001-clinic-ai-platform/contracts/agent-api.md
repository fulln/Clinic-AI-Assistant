# Contract: Agent API

**Base path**: `/api/v1/agents`
**Auth**: Bearer token required for all endpoints

---

## GET /api/v1/agents

List all visible agents. Filters by role: staff sees only published agents; admin sees all statuses.

**Query params**:
- `type` (optional): `formal | demo`
- `status` (optional, admin only): `draft | published | archived`
- `page` (default: 1), `page_size` (default: 20, max: 100)

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "slug": "string",
      "description": "string",
      "agent_type": "formal | demo",
      "capabilities": ["string"],
      "allowed_roles": ["doctor | staff | admin"],
      "status": "published",
      "version": "1.0.0"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

---

## GET /api/v1/agents/{agent_id}

Get single agent detail.

**Response 200**: Full agent object including `workflow_config` (admin only; omitted for non-admin).

**Response 404**
```json
{ "error": "not_found", "message": "智能体不存在" }
```

---

## POST /api/v1/agents

Create a new agent (draft status). **Admin only.**

**Request**
```json
{
  "name": "string (required, unique)",
  "slug": "string (optional, auto-generated if omitted)",
  "description": "string (required)",
  "agent_type": "formal | demo (required)",
  "capabilities": ["string"],
  "allowed_roles": ["doctor | staff"],
  "workflow_config": {}
}
```

**Response 201**: Created agent object.

**Response 422**: Validation errors with field-level detail.

---

## PATCH /api/v1/agents/{agent_id}

Update agent metadata or config. **Admin only.** Cannot modify `status` via this endpoint.

**Request**: Partial update; only provided fields are updated.

**Response 200**: Updated agent object.

---

## POST /api/v1/agents/{agent_id}/publish

Transition agent from draft → published. **Admin only.** Validates `workflow_config` before publishing.

**Response 200**
```json
{
  "agent": { "...full agent object..." },
  "publication": {
    "id": "uuid",
    "published_at": "2026-05-17T10:00:00Z",
    "version": "1.0.0"
  }
}
```

**Response 422**
```json
{ "error": "invalid_workflow_config", "message": "LangGraph config 验证失败", "detail": "..." }
```

---

## POST /api/v1/agents/{agent_id}/archive

Transition agent from published → archived. **Admin only.** Active conversations are not interrupted.

**Response 200**: Updated agent object with `status: archived`.

---

## POST /api/v1/agents/batch-publish

Batch publish multiple agents in a single request. **Admin only.**

**Request**
```json
{
  "agents": [
    {
      "name": "string",
      "description": "string",
      "agent_type": "formal | demo",
      "capabilities": ["string"],
      "allowed_roles": ["string"],
      "workflow_config": {}
    }
  ]
}
```
Max 50 agents per batch request.

**Response 202**: Batch accepted for async processing.
```json
{
  "batch_id": "uuid",
  "status": "processing",
  "total_count": 15,
  "submitted_at": "2026-05-17T10:00:00Z"
}
```

---

## GET /api/v1/agents/batches/{batch_id}

Poll batch publishing status. **Admin only.**

**Response 200**
```json
{
  "batch_id": "uuid",
  "status": "completed | processing | partial_failure",
  "total_count": 15,
  "success_count": 14,
  "failure_count": 1,
  "items": [
    { "index": 0, "status": "success", "agent_id": "uuid" },
    { "index": 1, "status": "failed", "error": "name already exists: '辅助诊断助手'" }
  ]
}
```
