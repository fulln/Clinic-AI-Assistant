import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid():
    return uuid.uuid4()


def _now():
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    STAFF = "staff"
    ADMIN = "admin"


class AgentType(str, enum.Enum):
    FORMAL = "formal"
    DEMO = "demo"


class AgentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"


class ItemStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class AuditOutcome(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    REFUSED = "refused"


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


# ---------------------------------------------------------------------------
# Auth Bounded Context
# ---------------------------------------------------------------------------

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now
    )

    conversations: Mapped[list["ConversationModel"]] = relationship(back_populates="user")
    knowledge_bases: Mapped[list["KnowledgeBaseModel"]] = relationship(back_populates="owner")
    audit_logs: Mapped[list["AuditLogModel"]] = relationship(back_populates="actor")


# ---------------------------------------------------------------------------
# Agent Bounded Context
# ---------------------------------------------------------------------------

class AgentModel(Base):
    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agents_status", "status"),
        Index("ix_agents_type", "agent_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    workflow_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    allowed_roles: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, values_callable=lambda x: [e.value for e in x]), default=AgentStatus.DRAFT, nullable=False
    )
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    system_prompt_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt_zh: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    max_tool_turns: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    llm_max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now
    )

    publications: Mapped[list["AgentPublicationModel"]] = relationship(back_populates="agent")


class AgentPublicationModel(Base):
    __tablename__ = "agent_publications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    published_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    version_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent: Mapped["AgentModel"] = relationship(back_populates="publications")


# ---------------------------------------------------------------------------
# Publishing Bounded Context
# ---------------------------------------------------------------------------

class PublishingBatchModel(Base):
    __tablename__ = "publishing_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, values_callable=lambda x: [e.value for e in x]), default=BatchStatus.PENDING, nullable=False
    )
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)

    items: Mapped[list["PublishingBatchItemModel"]] = relationship(back_populates="batch")


class PublishingBatchItemModel(Base):
    __tablename__ = "publishing_batch_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("publishing_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, values_callable=lambda x: [e.value for e in x]), default=ItemStatus.PENDING, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True
    )

    batch: Mapped["PublishingBatchModel"] = relationship(back_populates="items")


# ---------------------------------------------------------------------------
# Conversation Bounded Context
# ---------------------------------------------------------------------------

class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now
    )

    user: Mapped["UserModel"] = relationship(back_populates="conversations")
    sessions: Mapped[list["ConversationSessionModel"]] = relationship(
        back_populates="conversation"
    )
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="conversation")


class ConversationSessionModel(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    active_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True
    )
    context_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    locale: Mapped[str] = mapped_column(String(10), default="zh-CN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)

    conversation: Mapped["ConversationModel"] = relationship(back_populates="sessions")
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="session")


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.id"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    has_disclaimer: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)

    conversation: Mapped["ConversationModel"] = relationship(back_populates="messages")
    session: Mapped["ConversationSessionModel"] = relationship(back_populates="messages")


# ---------------------------------------------------------------------------
# RAG Bounded Context
# ---------------------------------------------------------------------------

class KnowledgeBaseModel(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, onupdate=_now
    )

    owner: Mapped["UserModel"] = relationship(back_populates="knowledge_bases")
    documents: Mapped[list["DocumentModel"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, values_callable=lambda x: [e.value for e in x]), default=DocumentStatus.UPLOADING, nullable=False
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=_now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    knowledge_base: Mapped["KnowledgeBaseModel"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunkModel"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        # HNSW index created in migration; declared here for reference only
        # Index("ix_doc_chunks_embedding", "embedding", postgresql_using="hnsw",
        #       postgresql_with={"m": 16, "ef_construction": 64},
        #       postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    document: Mapped["DocumentModel"] = relationship(back_populates="chunks")


# ---------------------------------------------------------------------------
# Audit Bounded Context (cross-cutting, append-only)
# ---------------------------------------------------------------------------

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_actor_created", "actor_id", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    actor_role: Mapped[UserRole | None] = mapped_column(Enum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, values_callable=lambda x: [e.value for e in x]), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    outcome: Mapped[AuditOutcome] = mapped_column(Enum(AuditOutcome, values_callable=lambda x: [e.value for e in x]), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=_now, server_default=func.now()
    )
    detail: Mapped[dict] = mapped_column(JSON, default=dict)

    actor: Mapped["UserModel | None"] = relationship(back_populates="audit_logs")
