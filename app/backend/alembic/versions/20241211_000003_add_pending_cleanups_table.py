"""Add pending_cleanups table for async file deletion.

Revision ID: 20241211_000003
Revises: 20241211_000002
Create Date: 2024-12-11

This migration adds the pending_cleanups table to support async file deletion:
- Files are deleted asynchronously after document deletion
- This table serves as a fallback queue for failed deletions
- A scheduled job periodically retries failed cleanups
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "20241211_000003"
down_revision: str = "20241211_000002"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "pending_cleanups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("storage_type", sa.String(50), nullable=False, server_default="both"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_id", UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=True),
    )

    # Index for finding pending cleanups that need retry
    op.create_index(
        "ix_pending_cleanups_attempts",
        "pending_cleanups",
        ["attempts", "max_attempts"],
    )

    # Index for cleanup by creation time
    op.create_index(
        "ix_pending_cleanups_created_at",
        "pending_cleanups",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pending_cleanups_created_at", table_name="pending_cleanups")
    op.drop_index("ix_pending_cleanups_attempts", table_name="pending_cleanups")
    op.drop_table("pending_cleanups")
