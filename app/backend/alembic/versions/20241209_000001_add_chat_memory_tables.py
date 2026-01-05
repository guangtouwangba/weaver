"""Add chat_memories and chat_summaries tables for RAG memory optimization.

Revision ID: 20241209_000001
Revises: 20241208_000001
Create Date: 2024-12-09

This migration adds:
- chat_memories: Long-term episodic memory with vector embeddings for semantic retrieval
- chat_summaries: Short-term working memory for session summaries
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241209_000001"
down_revision: str = "20241208_000001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # Create chat_memories table for long-term episodic memory
    op.create_table(
        "chat_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("memory_metadata", postgresql.JSONB, nullable=True, default=dict),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create index on embedding for vector similarity search
    op.execute(
        """
        CREATE INDEX idx_chat_memories_embedding
        ON chat_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """
    )

    # Create chat_summaries table for short-term working memory
    op.create_table(
        "chat_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("summary", sa.Text, nullable=False, default=""),
        sa.Column("summarized_message_count", sa.Integer, nullable=False, default=0),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    # Drop index first
    op.execute("DROP INDEX IF EXISTS idx_chat_memories_embedding;")
    # Drop tables
    op.drop_table("chat_summaries")
    op.drop_table("chat_memories")






















