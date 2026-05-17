"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Reusable enum references — create_type=False because we create them explicitly below
_userrole = postgresql.ENUM("doctor", "staff", "admin", name="userrole", create_type=False)
_agenttype = postgresql.ENUM("formal", "demo", name="agenttype", create_type=False)
_agentstatus = postgresql.ENUM("draft", "published", "archived", name="agentstatus", create_type=False)
_messagerole = postgresql.ENUM("user", "assistant", "system", name="messagerole", create_type=False)
_docstatus = postgresql.ENUM("uploading", "processing", "ready", "failed", name="documentstatus", create_type=False)
_batchstatus = postgresql.ENUM("pending", "processing", "completed", "partial_failure", name="batchstatus", create_type=False)
_itemstatus = postgresql.ENUM("pending", "success", "failed", name="itemstatus", create_type=False)
_auditoutcome = postgresql.ENUM("success", "failure", "refused", name="auditoutcome", create_type=False)
_auditaction = postgresql.ENUM(
    "user.login", "user.logout", "message.sent", "message.refused",
    "document.uploaded", "document.deleted", "agent.published", "agent.archived",
    "knowledge_base.created", "knowledge_base.deleted", "batch.submitted",
    "knowledge_base.queried", "session.updated",
    name="auditaction",
    create_type=False,
)


def upgrade() -> None:
    # Extensions are created in env.py before migrations run

    # Create all enum types explicitly (once)
    bind = op.get_bind()
    for e in [
        postgresql.ENUM("doctor", "staff", "admin", name="userrole"),
        postgresql.ENUM("formal", "demo", name="agenttype"),
        postgresql.ENUM("draft", "published", "archived", name="agentstatus"),
        postgresql.ENUM("user", "assistant", "system", name="messagerole"),
        postgresql.ENUM("uploading", "processing", "ready", "failed", name="documentstatus"),
        postgresql.ENUM("pending", "processing", "completed", "partial_failure", name="batchstatus"),
        postgresql.ENUM("pending", "success", "failed", name="itemstatus"),
        postgresql.ENUM("success", "failure", "refused", name="auditoutcome"),
        postgresql.ENUM(
            "user.login", "user.logout", "message.sent", "message.refused",
            "document.uploaded", "document.deleted", "agent.published", "agent.archived",
            "knowledge_base.created", "knowledge_base.deleted", "batch.submitted",
            "knowledge_base.queried", "session.updated",
            name="auditaction",
        ),
    ]:
        e.create(bind)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", _userrole, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("agent_type", _agenttype, nullable=False),
        sa.Column("capabilities", sa.JSON, nullable=False),
        sa.Column("workflow_config", sa.JSON, nullable=False),
        sa.Column("allowed_roles", sa.JSON, nullable=False),
        sa.Column("status", _agentstatus, nullable=False),
        sa.Column("version", sa.String(20), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_agents_status", "agents", ["status"])
    op.create_index("ix_agents_type", "agents", ["agent_type"])

    op.create_table(
        "agent_publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_at", sa.DateTime, nullable=False),
        sa.Column("version_snapshot", sa.JSON, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_table(
        "publishing_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("submitted_at", sa.DateTime, nullable=False),
        sa.Column("status", _batchstatus, nullable=False),
        sa.Column("total_count", sa.Integer, default=0),
        sa.Column("success_count", sa.Integer, default=0),
        sa.Column("failure_count", sa.Integer, default=0),
    )

    op.create_table(
        "publishing_batch_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("publishing_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_config", sa.JSON, nullable=False),
        sa.Column("status", _itemstatus, nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
    )

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "conversation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("active_agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("context_snapshot", sa.JSON, nullable=False),
        sa.Column("rag_enabled", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_activity_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversation_sessions.id"), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("role", _messagerole, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("has_disclaimer", sa.Boolean, default=False),
        sa.Column("metadata", sa.JSON, nullable=False),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])

    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("document_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("status", _docstatus, nullable=False),
        sa.Column("chunk_count", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("processed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("token_count", sa.Integer, default=0),
        sa.Column("metadata", sa.JSON, nullable=False),
    )
    # HNSW index for cosine similarity search
    op.execute(
        "CREATE INDEX ix_doc_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_role", _userrole, nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", _auditaction, nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", _auditoutcome, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("detail", sa.JSON, nullable=False),
    )
    op.create_index("ix_audit_actor_created", "audit_logs", ["actor_id", "created_at"])
    op.create_index("ix_audit_resource", "audit_logs", ["resource_type", "resource_id"])

    # Append-only protection trigger for audit_logs
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs are append-only and cannot be modified or deleted';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation()")
    for table in [
        "audit_logs", "document_chunks", "documents", "knowledge_bases",
        "messages", "conversation_sessions", "conversations",
        "publishing_batch_items", "publishing_batches",
        "agent_publications", "agents", "users",
    ]:
        op.drop_table(table)
    for enum_name in [
        "auditaction", "auditoutcome", "itemstatus", "batchstatus",
        "documentstatus", "messagerole", "agentstatus", "agenttype", "userrole",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
