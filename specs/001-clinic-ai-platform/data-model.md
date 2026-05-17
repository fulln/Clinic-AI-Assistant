# Data Model: 私立诊所 AI 助手平台

**Phase 1 Output** | **Date**: 2026-05-17 | **Feature**: 001-clinic-ai-platform

## Domain Entities & Aggregates

### Bounded Context: Auth

#### Entity: User (Aggregate Root)
```
User
├── id: UUID (PK)
├── username: str (unique, 3-50 chars)
├── password_hash: str (bcrypt)
├── role: UserRole (enum: doctor | staff | admin)
├── display_name: str
├── is_active: bool (default: true)
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

**Invariants**:
- `username` must be unique across all users.
- `password_hash` must never be returned in API responses.
- Only `admin` role can create/deactivate other users.
- `role` is immutable after creation (requires admin intervention to change).

**Value Object: UserRole**
```
UserRole: Enum
├── DOCTOR   # Access: conversation, RAG management, all agents
├── STAFF    # Access: conversation, demo agents only
└── ADMIN    # Access: all features + agent management
```

---

### Bounded Context: Agent

#### Entity: Agent (Aggregate Root)
```
Agent
├── id: UUID (PK)
├── name: str (unique, max 100 chars)
├── slug: str (unique, URL-safe, max 100 chars)
├── description: str (max 500 chars)
├── agent_type: AgentType (enum: formal | demo)
├── capabilities: list[str]  (e.g., ["rag_query", "document_draft"])
├── workflow_config: JSON    (LangGraph StateGraph serialized config)
├── allowed_roles: list[UserRole]
├── status: AgentStatus (enum: draft | published | archived)
├── version: str (semver, e.g., "1.0.0")
├── created_by: UUID (FK → User.id)
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

**Invariants**:
- `workflow_config` MUST be a valid LangGraph config (validated on publish).
- `status` transitions: draft → published → archived (no reversal from archived).
- Demo agents MUST have `agent_type = demo` and reduced `capabilities`.
- Published agent MUST have `version` set.

#### Entity: AgentPublication
```
AgentPublication
├── id: UUID (PK)
├── agent_id: UUID (FK → Agent.id)
├── published_by: UUID (FK → User.id)
├── published_at: datetime (UTC)
├── version_snapshot: JSON   (immutable copy of agent config at publish time)
└── notes: str (optional)
```

#### Aggregate: PublishingBatch
```
PublishingBatch
├── id: UUID (PK)
├── submitted_by: UUID (FK → User.id)
├── submitted_at: datetime (UTC)
├── status: BatchStatus (enum: pending | processing | completed | partial_failure)
├── total_count: int
├── success_count: int
├── failure_count: int
└── items: list[PublishingBatchItem]

PublishingBatchItem
├── id: UUID (PK)
├── batch_id: UUID (FK → PublishingBatch.id)
├── agent_config: JSON
├── status: ItemStatus (enum: pending | success | failed)
└── error_message: str (nullable)
```

---

### Bounded Context: Conversation

#### Entity: Conversation (Aggregate Root)
```
Conversation
├── id: UUID (PK)
├── user_id: UUID (FK → User.id)
├── title: str (auto-generated from first message, max 100 chars)
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

#### Entity: ConversationSession
```
ConversationSession
├── id: UUID (PK)
├── conversation_id: UUID (FK → Conversation.id)
├── active_agent_id: UUID (FK → Agent.id, nullable)
├── context_snapshot: JSON  (LangGraph checkpoint state, last N messages)
├── rag_enabled: bool (default: false)
├── created_at: datetime (UTC)
└── last_activity_at: datetime (UTC)
```

**Note**: `context_snapshot` is also cached in Redis at key `session:{session_id}:context` (TTL: 24h). The PostgreSQL record is the source of truth; Redis is the performance cache.

#### Entity: Message
```
Message
├── id: UUID (PK)
├── conversation_id: UUID (FK → Conversation.id)
├── session_id: UUID (FK → ConversationSession.id)
├── agent_id: UUID (FK → Agent.id, nullable — null for user messages)
├── role: MessageRole (enum: user | assistant | system)
├── content: text
├── has_disclaimer: bool    (true if content has medical disclaimer appended)
├── metadata: JSON          (tool_calls, citations, latency_ms, etc.)
├── created_at: datetime (UTC)
└── is_deleted: bool (soft delete only)
```

**Invariants**:
- `role = assistant` MUST have `agent_id` set.
- If `role = assistant` and agent handles medical content, `has_disclaimer` MUST be `true`.
- `content` of deleted messages is overwritten with `[REDACTED]`; `is_deleted` stays `true`.

---

### Bounded Context: RAG

#### Entity: KnowledgeBase (Aggregate Root)
```
KnowledgeBase
├── id: UUID (PK)
├── owner_id: UUID (FK → User.id, role MUST be doctor)
├── name: str (max 100 chars)
├── description: str (optional, max 300 chars)
├── document_count: int (denormalized, updated on document add/remove)
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

**Invariants**:
- `owner_id` MUST reference a User with `role = DOCTOR`.
- A doctor MAY have multiple KnowledgeBases; each is personal and not shared.

#### Entity: Document
```
Document
├── id: UUID (PK)
├── knowledge_base_id: UUID (FK → KnowledgeBase.id)
├── filename: str
├── file_size_bytes: int
├── mime_type: str (e.g., "application/pdf", "text/plain")
├── status: DocumentStatus (enum: uploading | processing | ready | failed)
├── chunk_count: int (set after processing)
├── error_message: str (nullable, set if status = failed)
├── created_at: datetime (UTC)
└── processed_at: datetime (UTC, nullable)
```

#### Entity: DocumentChunk
```
DocumentChunk
├── id: UUID (PK)
├── document_id: UUID (FK → Document.id)
├── chunk_index: int
├── content: text
├── embedding: vector(1536)   (pgvector column, OpenAI text-embedding-3-small dimension)
├── token_count: int
└── metadata: JSON            (page_number, section_title, etc.)
```

**Index**: `CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)`

---

### Bounded Context: Audit (Cross-Cutting)

#### Entity: AuditLog (append-only)
```
AuditLog
├── id: UUID (PK)
├── actor_id: UUID (FK → User.id, nullable for system actions)
├── actor_role: UserRole (snapshot at time of action)
├── session_id: UUID (nullable, FK → ConversationSession.id)
├── action: AuditAction (enum — see below)
├── resource_type: str (e.g., "Message", "Document", "Agent")
├── resource_id: UUID
├── outcome: AuditOutcome (enum: success | failure | refused)
├── ip_address: str (anonymized: last octet zeroed)
├── created_at: datetime (UTC)
└── detail: JSON (action-specific metadata, e.g., refusal reason)
```

**AuditAction values**: `user.login`, `user.logout`, `message.sent`, `message.refused`,
`document.uploaded`, `document.deleted`, `agent.published`, `agent.archived`,
`knowledge_base.created`, `knowledge_base.deleted`, `batch.submitted`.

**Invariants**:
- AuditLog records are NEVER updated or deleted (append-only enforced at application layer + DB trigger).
- Retained for minimum 5 years (Constitution Principle V).

---

## Database Schema Summary

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Enums
CREATE TYPE user_role AS ENUM ('doctor', 'staff', 'admin');
CREATE TYPE agent_type AS ENUM ('formal', 'demo');
CREATE TYPE agent_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE document_status AS ENUM ('uploading', 'processing', 'ready', 'failed');
CREATE TYPE audit_outcome AS ENUM ('success', 'failure', 'refused');

-- Key indexes
-- users: idx on username (unique)
-- agents: idx on slug (unique), idx on status, idx on agent_type
-- messages: idx on conversation_id + created_at (compound)
-- document_chunks: HNSW index on embedding (vector_cosine_ops)
-- audit_logs: idx on actor_id + created_at, idx on resource_type + resource_id
```

## Redis Key Schemas

| Key Pattern | Value | TTL | Purpose |
|-------------|-------|-----|---------|
| `session:{session_id}:context` | JSON (LangGraph state) | 24h | Active conversation context cache |
| `user:{user_id}:token:{jti}` | `{exp_ts}` | = token TTL | Valid access token registry |
| `blacklist:token:{jti}` | `1` | = original token TTL | Revoked token blacklist (logout) |
| `refresh:{user_id}:{device_id}` | `{refresh_token_hash}` | 7d | Refresh token storage |
| `agent:catalog` | JSON list | 5min | Agent catalog cache (invalidated on publish) |
| `kb:{kb_id}:status` | `{doc_count}:{ready_count}` | None | KnowledgeBase processing status |
