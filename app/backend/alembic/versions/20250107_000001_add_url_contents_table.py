"""Add url_contents table for storing extracted URL content.

Revision ID: 20250107_000001
Revises: 20250103_000001
Create Date: 2025-01-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "20250107_000001"
down_revision: Union[str, None] = "20241230_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create url_contents table."""
    op.create_table(
        "url_contents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.Text(), nullable=False, unique=True),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        # Extracted content
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        # Platform-specific metadata
        sa.Column("meta_data", JSONB, server_default="{}", nullable=False),
        # Processing status
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
        # User ownership
        sa.Column("user_id", sa.String(255), nullable=True),
    )

    # Create indexes for faster lookups
    op.create_index("ix_url_contents_url", "url_contents", ["url"], unique=True)
    op.create_index("ix_url_contents_normalized_url", "url_contents", ["normalized_url"])
    op.create_index("ix_url_contents_platform", "url_contents", ["platform"])
    op.create_index("ix_url_contents_status", "url_contents", ["status"])
    op.create_index("ix_url_contents_user_id", "url_contents", ["user_id"])


def downgrade() -> None:
    """Drop url_contents table."""
    op.drop_index("ix_url_contents_user_id", table_name="url_contents")
    op.drop_index("ix_url_contents_status", table_name="url_contents")
    op.drop_index("ix_url_contents_platform", table_name="url_contents")
    op.drop_index("ix_url_contents_normalized_url", table_name="url_contents")
    op.drop_index("ix_url_contents_url", table_name="url_contents")
    op.drop_table("url_contents")

