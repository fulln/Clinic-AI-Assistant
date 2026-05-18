import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime


class AuditAction(str, enum.Enum):
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    MESSAGE_SENT = "message.sent"
    MESSAGE_REFUSED = "message.refused"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    AGENT_PUBLISHED = "agent.published"
    AGENT_ARCHIVED = "agent.archived"
    KNOWLEDGE_BASE_CREATED = "knowledge_base.created"
    KNOWLEDGE_BASE_DELETED = "knowledge_base.deleted"
    BATCH_SUBMITTED = "batch.submitted"
    KB_QUERIED = "knowledge_base.queried"
    SESSION_UPDATED = "session.updated"


class AuditOutcome(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    REFUSED = "refused"


@dataclass
class AuditLog:
    action: AuditAction
    resource_type: str
    outcome: AuditOutcome
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    actor_id: uuid.UUID | None = None
    actor_role: str | None = None
    session_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None
    ip_address: str | None = None
    detail: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
