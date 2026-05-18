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
  "agent_id": "uuid (optional, sets active agent for the session)",
  "locale": "zh-CN | en-US (optional, default: zh-CN)"
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
  "locale": "zh-CN",
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
    "rag_enabled": false,
    "locale": "zh-CN"
  },
  "messages": [
    {
      "id": "uuid",
      "role": "user | assistant",
      "content": "string",
      "agent_id": "uuid | null",
      "has_disclaimer": false,
      "created_at": "2026-05-17T10:00:00Z",
      "metadata": {
        "locale": "zh-CN"
      }
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
  "rag_enabled": "bool (optional, doctor role only)",
  "locale": "zh-CN | en-US (optional, overrides and persists session locale for this message)"
}
```

**Response**: `Content-Type: text/event-stream`

SSE event stream:
```
event: start
data: {"message_id": "uuid", "agent_id": "uuid", "session_id": "uuid", "locale": "en-US"}

event: token
data: {"token": "For "}

event: token
data: {"token": "this visit"}

event: progress
data: {"stage": "routing", "message": "Supervisor is selecting the best agent", "locale": "en-US"}

event: disclaimer
data: {"text": "This content is for auxiliary reference only and does not constitute medical diagnosis or treatment advice. Please follow a licensed physician's guidance.", "locale": "en-US"}

event: end
data: {"message_id": "uuid", "latency_ms": 1840, "locale": "en-US"}

event: error
data: {"code": "agent_refused", "message": "This request is outside the platform's service scope. Please consult a licensed physician.", "locale": "en-US"}
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
  "rag_enabled": "bool (doctor role only)",
  "locale": "zh-CN | en-US"
}
```

**Response 200**: Updated session object.

**Behavior rules**:
- `locale` on `PATCH /session` updates the session default for all subsequent messages.
- `locale` on `POST /messages` takes effect immediately and also persists back to the session.
- Compliance disclaimer, refusal copy, progress messages, and backend-generated errors MUST use the effective locale.

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
