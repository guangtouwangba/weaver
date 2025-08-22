"""create_documents_table

Revision ID: cac027415fb8
Revises: 5483b8e32acc
Create Date: 2025-08-22 10:52:24.009406

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "cac027415fb8"
down_revision: Union[str, None] = "5483b8e32acc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(50), nullable=False),
        # File association
        sa.Column("file_id", sa.String(255), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        # Processing status
        sa.Column("status", sa.String(50), nullable=False, server_default="'pending'"),
        sa.Column("processing_status", sa.String(50), nullable=True),
        # Metadata
        sa.Column(
            "doc_metadata", postgresql.JSON(), nullable=False, server_default="{}"
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["file_id"], ["files.id"], name="fk_documents_file_id", ondelete="SET NULL"
        ),
    )

    # Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(255), nullable=False),
        sa.Column("document_id", sa.String(255), nullable=False),
        # Content information
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=True),
        sa.Column("end_char", sa.Integer(), nullable=True),
        # Vector embedding (using Text for now, can be changed to VECTOR if pgvector is available)
        sa.Column("embedding_vector", sa.Text(), nullable=True),
        # Metadata
        sa.Column(
            "chunk_metadata", postgresql.JSON(), nullable=False, server_default="{}"
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_document_chunks_document_id",
            ondelete="CASCADE",
        ),
    )

    # Create indexes for performance
    op.create_index("idx_documents_file_id", "documents", ["file_id"])
    op.create_index("idx_documents_status", "documents", ["status"])
    op.create_index("idx_documents_content_type", "documents", ["content_type"])
    op.create_index("idx_documents_created_at", "documents", ["created_at"])

    op.create_index(
        "idx_document_chunks_document_id", "document_chunks", ["document_id"]
    )
    op.create_index(
        "idx_document_chunks_chunk_index", "document_chunks", ["chunk_index"]
    )

    # Create GIN indexes for JSON metadata fields
    op.execute(
        "CREATE INDEX idx_documents_doc_metadata_gin ON documents USING gin (doc_metadata);"
    )
    op.execute(
        "CREATE INDEX idx_document_chunks_chunk_metadata_gin ON document_chunks USING gin (chunk_metadata);"
    )


def downgrade() -> None:
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_chunk_metadata_gin;")
    op.execute("DROP INDEX IF EXISTS idx_documents_doc_metadata_gin;")

    op.drop_index("idx_document_chunks_chunk_index", table_name="document_chunks")
    op.drop_index("idx_document_chunks_document_id", table_name="document_chunks")

    op.drop_index("idx_documents_created_at", table_name="documents")
    op.drop_index("idx_documents_content_type", table_name="documents")
    op.drop_index("idx_documents_status", table_name="documents")
    op.drop_index("idx_documents_file_id", table_name="documents")

    # Drop tables
    op.drop_table("document_chunks")
    op.drop_table("documents")
