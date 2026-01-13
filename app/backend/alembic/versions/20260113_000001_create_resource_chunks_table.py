"""Create resource_chunks table for unified chunk storage.

Revision ID: 20260113_000001
Revises: 20260111_000001
Create Date: 2026-01-13

This migration creates the unified resource_chunks table that stores chunks
from all resource types (documents, videos, web pages, notes, etc.) with
consistent schema for unified retrieval.

Features:
- resource_type field for filtering by content type
- metadata JSONB for type-specific data (page_number, timestamps, etc.)
- content_tsvector for hybrid search (vector + keyword)
- HNSW index for fast vector similarity search
- GIN index for full-text search
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR


# revision identifiers, used by Alembic.
revision = "20260113_000001"
down_revision = "20260111_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create resource_chunks table
    op.create_table(
        "resource_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=False, index=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("metadata", JSONB, server_default="{}", nullable=False),
        sa.Column("content_tsvector", TSVECTOR, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX idx_resource_chunks_embedding_hnsw 
        ON resource_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Create GIN index for full-text search
    op.execute("""
        CREATE INDEX idx_resource_chunks_content_tsvector 
        ON resource_chunks 
        USING GIN (content_tsvector)
    """)

    # Create trigger to auto-update tsvector on insert/update
    op.execute("""
        CREATE OR REPLACE FUNCTION resource_chunks_tsvector_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.content_tsvector := to_tsvector('english', COALESCE(NEW.content, ''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER resource_chunks_tsvector_update
        BEFORE INSERT OR UPDATE ON resource_chunks
        FOR EACH ROW EXECUTE FUNCTION resource_chunks_tsvector_trigger();
    """)

    # Create composite index for common query patterns
    op.create_index(
        "idx_resource_chunks_project_type",
        "resource_chunks",
        ["project_id", "resource_type"],
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS resource_chunks_tsvector_update ON resource_chunks")
    op.execute("DROP FUNCTION IF EXISTS resource_chunks_tsvector_trigger()")

    # Drop indexes
    op.drop_index("idx_resource_chunks_project_type", table_name="resource_chunks")
    op.execute("DROP INDEX IF EXISTS idx_resource_chunks_content_tsvector")
    op.execute("DROP INDEX IF EXISTS idx_resource_chunks_embedding_hnsw")

    # Drop table
    op.drop_table("resource_chunks")
