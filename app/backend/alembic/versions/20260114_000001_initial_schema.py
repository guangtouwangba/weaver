"""Initial schema - clean slate.

Revision ID: 20260114_000001
Revises:
Create Date: 2026-01-14

This migration creates all tables from scratch after removing legacy migrations.
Tables included:
- projects, documents, resource_chunks
- canvases, chat_messages, chat_memories, chat_summaries
- task_queue, pending_cleanups, outputs
- url_contents, highlights, comments
- tags, inbox_items, inbox_item_tags
- api_keys, global_settings, project_settings, user_settings
- evaluation_logs

Tables removed (not included):
- document_chunks (replaced by resource_chunks)
- entities, relations (knowledge graph - unused)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20260114_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ==========================================================================
    # Core Tables
    # ==========================================================================

    # Projects table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False, server_default="application/pdf"),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("graph_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("full_content", sa.Text, nullable=True),
        sa.Column("content_token_count", sa.Integer, nullable=True),
        sa.Column("parsing_metadata", postgresql.JSONB, nullable=True),
        sa.Column("thumbnail_path", sa.String(512), nullable=True),
        sa.Column("thumbnail_status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


    # Resource Chunks table (unified chunks for all resource types)
    op.create_table(
        "resource_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("metadata", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("content_tsvector", postgresql.TSVECTOR, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create HNSW index for vector similarity search on resource_chunks
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_resource_chunks_embedding_hnsw
        ON resource_chunks
        USING hnsw ((embedding::vector(1536)) vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Create GIN index for full-text search on resource_chunks
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_resource_chunks_content_tsvector
        ON resource_chunks
        USING gin (content_tsvector)
        """
    )

    # ==========================================================================
    # Canvas & Chat Tables
    # ==========================================================================

    # Canvases table
    op.create_table(
        "canvases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_canvases_project_id", "canvases", ["project_id"])

    # Chat Messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("sources", postgresql.JSONB, nullable=True),
        sa.Column("context_refs", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Chat Memories table (Long-Term Episodic Memory)
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
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("memory_metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create HNSW index for chat_memories
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_chat_memories_embedding_hnsw
        ON chat_memories
        USING hnsw ((embedding::vector(1536)) vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Chat Summaries table (Short-Term Working Memory)
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
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("summary", sa.Text, nullable=False, server_default=""),
        sa.Column("summarized_message_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


    # ==========================================================================
    # Background Processing Tables
    # ==========================================================================

    # Task Queue table
    op.create_table(
        "task_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("environment", sa.String(50), nullable=False, server_default="development", index=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Pending Cleanups table
    op.create_table(
        "pending_cleanups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("storage_type", sa.String(50), nullable=False, server_default="both"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # ==========================================================================
    # Output Generation Tables
    # ==========================================================================

    # Outputs table
    op.create_table(
        "outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("output_type", sa.String(50), nullable=False, index=True),
        sa.Column("source_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="generating"),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("data", postgresql.JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # ==========================================================================
    # URL Content & Annotation Tables
    # ==========================================================================

    # URL Contents table
    op.create_table(
        "url_contents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.Text, nullable=False, unique=True, index=True),
        sa.Column("normalized_url", sa.Text, nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("meta_data", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=True),
    )

    # Highlights table
    op.create_table(
        "highlights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("start_offset", sa.Integer, nullable=False),
        sa.Column("end_offset", sa.Integer, nullable=False),
        sa.Column("color", sa.String(20), nullable=False, server_default="yellow"),
        sa.Column("type", sa.String(20), nullable=False, server_default="highlight"),
        sa.Column("text_content", sa.Text, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("rects", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Comments table
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column(
            "highlight_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("highlights.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("author_id", sa.String(255), nullable=True),
        sa.Column("author_name", sa.String(255), nullable=False, server_default="Anonymous"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


    # ==========================================================================
    # Inbox & Collection Tables
    # ==========================================================================

    # Tags table
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(20), nullable=False, server_default="blue"),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", "user_id", name="uq_tags_name_user"),
    )

    # Inbox Items table
    op.create_table(
        "inbox_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("meta_data", postgresql.JSONB, server_default="{}", nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_read", sa.Boolean, server_default="false", nullable=False),
        sa.Column("is_processed", sa.Boolean, server_default="false", nullable=False),
        sa.Column("user_id", sa.String(255), nullable=True),
    )

    # Inbox Item Tags association table
    op.create_table(
        "inbox_item_tags",
        sa.Column(
            "inbox_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inbox_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # API Keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ==========================================================================
    # Settings Tables
    # ==========================================================================

    # Global Settings table
    op.create_table(
        "global_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("category", sa.String(100), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_encrypted", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Project Settings table
    op.create_table(
        "project_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("key", sa.String(255), nullable=False, index=True),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_encrypted", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("project_id", "key", name="uq_project_settings_project_key"),
    )

    # User Settings table
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("key", sa.String(255), nullable=False, index=True),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_encrypted", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "key", name="uq_user_settings_user_key"),
    )

    # ==========================================================================
    # Evaluation Tables
    # ==========================================================================

    # Evaluation Logs table
    op.create_table(
        "evaluation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("test_case_id", sa.String(100), nullable=True),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("ground_truth", sa.Text, nullable=True),
        sa.Column("chunking_strategy", sa.String(50), nullable=True),
        sa.Column("retrieval_mode", sa.String(50), nullable=True),
        sa.Column("retrieved_contexts", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("generated_answer", sa.Text, nullable=True),
        sa.Column("metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("evaluation_type", sa.String(50), nullable=False, server_default="realtime"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table("evaluation_logs")
    op.drop_table("user_settings")
    op.drop_table("project_settings")
    op.drop_table("global_settings")
    op.drop_table("api_keys")
    op.drop_table("inbox_item_tags")
    op.drop_table("inbox_items")
    op.drop_table("tags")
    op.drop_table("comments")
    op.drop_table("highlights")
    op.drop_table("url_contents")
    op.drop_table("outputs")
    op.drop_table("pending_cleanups")
    op.drop_table("task_queue")
    op.drop_table("chat_summaries")
    op.drop_table("chat_memories")
    op.drop_table("chat_messages")
    op.drop_table("canvases")
    op.drop_table("resource_chunks")
    op.drop_table("documents")
    op.drop_table("projects")

    # Drop pgvector extension
    op.execute("DROP EXTENSION IF EXISTS vector")
