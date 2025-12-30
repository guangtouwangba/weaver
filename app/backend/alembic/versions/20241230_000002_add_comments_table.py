"""Add comments table.

Revision ID: 20241230_000002
Revises: 20241230_000001
Create Date: 2024-12-30

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "20241230_000002"
down_revision = "20241230_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create comments table
    op.create_table(
        "comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column(
            "highlight_id",
            UUID(as_uuid=True),
            sa.ForeignKey("highlights.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author_id", sa.String(255), nullable=True),
        sa.Column("author_name", sa.String(255), nullable=False, server_default="Anonymous"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Add indexes for common queries
    op.create_index("ix_comments_document_id", "comments", ["document_id"])
    op.create_index("ix_comments_parent_id", "comments", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_parent_id", table_name="comments")
    op.drop_index("ix_comments_document_id", table_name="comments")
    op.drop_table("comments")
