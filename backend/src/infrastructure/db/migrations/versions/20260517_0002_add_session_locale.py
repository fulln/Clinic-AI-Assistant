"""add conversation session locale

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_sessions",
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="zh-CN"),
    )
    op.execute("UPDATE conversation_sessions SET locale = 'zh-CN' WHERE locale IS NULL")
    op.alter_column("conversation_sessions", "locale", server_default=None)


def downgrade() -> None:
    op.drop_column("conversation_sessions", "locale")
