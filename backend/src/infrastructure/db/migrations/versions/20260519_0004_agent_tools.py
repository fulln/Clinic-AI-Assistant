"""agent tools (rag-as-tool refactor)

Adds:
  - agents.tools (JSON list): enabled tool names per agent
  - agents.max_tool_turns (int): cap on tool-call loop

Removes:
  - agents.rag_enabled

Data migration: rows with rag_enabled = true get tools = ["knowledge_base_search"].

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New columns
    op.add_column(
        "agents",
        sa.Column("tools", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "agents",
        sa.Column(
            "max_tool_turns",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
    )

    # Backfill tools from rag_enabled.
    op.execute(
        "UPDATE agents SET tools = '[\"knowledge_base_search\"]'::json "
        "WHERE rag_enabled = true"
    )

    # Drop server defaults — app code controls defaults from now on.
    op.alter_column("agents", "tools", server_default=None)
    op.alter_column("agents", "max_tool_turns", server_default=None)

    # Drop the old rag_enabled column.
    op.drop_column("agents", "rag_enabled")


def downgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "rag_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Restore rag_enabled = true for any agent that has knowledge_base_search in tools.
    op.execute(
        "UPDATE agents SET rag_enabled = true "
        "WHERE tools::text LIKE '%knowledge_base_search%'"
    )
    op.alter_column("agents", "rag_enabled", server_default=None)
    op.drop_column("agents", "max_tool_turns")
    op.drop_column("agents", "tools")
