# Contract: Conversation API

**Base path**: `/api/v1/conversations`
**Auth**: Bearer token required for all endpoints
**Streaming**: AI responses use Server-Sent Events (SSE) on message send

---

## POST /api/v1/conversations

Create a new conversation session.

**Request**
```json
{
  "title": "string (optional, auto-generated from first message if omitted)",
  "agent_id": "uuid (optional, sets active agent for the session)"
}
```

**Response 201**
```json
{
  "id": "uuid",
  "title": "新对话",
  "user_id": "uuid",
  "session_id": "uuid",
  "active_agent_id": "uuid | null",
  "rag_enabled": false,
  "created_at": "2026-05-17T10:00:00Z"
}
```

---

## GET /api/v1/conversations

List current user's conversations (paginated, newest first).

**Query params**: `page`, `page_size` (default 20)

**Response 200**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "active_agent_id": "uuid | null",
      "last_message_at": "2026-05-17T10:00:00Z",
      "created_at": "2026-05-17T10:00:00Z"
    }
  ],
  "total": 42
}
```

---

## GET /api/v1/conversations/{conversation_id}

Get conversation detail with message history.

**Query params**: `limit` (default: 50, max: 200), `before_id` (cursor pagination)

**Response 200**
```json
{
  "id": "uuid",
  "title": "string",
  "session": {
    "id": "uuid",
    "active_agent_id": "uuid | null",
    "rag_enabled": false
  },
  "messages": [
    {
      "id": "uuid",
      "role": "user | assistant",
      "content": "string",
      "agent_id": "uuid | null",
      "has_disclaimer": false,
      "created_at": "2026-05-17T10:00:00Z"
    }
  ]
}
```

---

## POST /api/v1/conversations/{conversation_id}/messages

Send a message and receive streaming AI response via SSE.

**Request**
```json
{
  "content": "string (required, max 4000 chars)",
  "agent_id": "uuid (optional, overrides session active agent for this message)",
  "rag_enabled": "bool (optional, doctor role only)"
}
```

**Response**: `Content-Type: text/event-stream`

SSE event stream:
```
event: start
data: {"message_id": "uuid", "agent_id": "uuid", "session_id": "uuid"}

event: token
data: {"token": "本次"}

event: token
data: {"token": "就诊"}

event: disclaimer
data: {"text": "本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。"}

event: end
data: {"message_id": "uuid", "total_tokens": 312, "latency_ms": 1840}

event: error
data: {"code": "agent_refused", "message": "该请求超出本平台服务范围，请咨询执业医师。"}
```

**Response 403** (if user role not in agent's `allowed_roles`):
```json
{ "error": "forbidden", "message": "您的角色无权使用此智能体" }
```

**Response 429** (rate limit):
```json
{ "error": "rate_limit", "message": "请求过于频繁，请稍后再试", "retry_after": 10 }
```

---

## PATCH /api/v1/conversations/{conversation_id}/session

Update active session settings (switch agent, toggle RAG).

**Request**
```json
{
  "active_agent_id": "uuid | null",
  "rag_enabled": "bool (doctor role only)"
}
```

**Response 200**: Updated session object.

---

## DELETE /api/v1/conversations/{conversation_id}

Soft-delete conversation. Message content is redacted; audit log preserved.

**Response 204**: No content.

---

## WebSocket: /ws/conversations/{conversation_id}

Alternative to SSE for bidirectional communication (e.g., tool call approval for human-in-the-loop).

**Auth**: `?token={access_token}` query param (WebSocket cannot set Authorization header).

**Client → Server**
```json
{ "type": "message", "content": "string", "agent_id": "uuid" }
{ "type": "approve_tool", "tool_call_id": "uuid" }
{ "type": "reject_tool", "tool_call_id": "uuid", "reason": "string" }
```

**Server → Client**
```json
{ "type": "token", "token": "string" }
{ "type": "tool_request", "tool_call_id": "uuid", "tool_name": "string", "args": {} }
{ "type": "end", "message_id": "uuid" }
{ "type": "error", "code": "string", "message": "string" }
```
