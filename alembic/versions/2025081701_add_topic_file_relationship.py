"""Add topic-file relationship to integrate file upload system with topics

Revision ID: 2025081701
Revises: 2025081601
Create Date: 2025-08-17 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2025081701"
down_revision = "2025081601"
branch_labels = None
depends_on = None


def upgrade():
    """Add topic relationship to files table for integration."""

    # Add topic_id to files table to link uploaded files to topics
    op.add_column("files", sa.Column("topic_id", sa.BigInteger(), nullable=True))

    # Add foreign key constraint to maintain referential integrity
    op.create_foreign_key(
        "fk_files_topic_id",
        "files",
        "topics",
        ["topic_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for efficient topic-file queries
    op.create_index("idx_files_topic_id", "files", ["topic_id"])

    # Add composite index for frequently used queries
    op.create_index("idx_files_topic_owner", "files", ["topic_id", "owner_id"])

    # Add index for files by topic and status
    op.create_index("idx_files_topic_status", "files", ["topic_id", "status"])


def downgrade():
    """Remove topic relationship from files table."""

    # Drop indexes first
    op.drop_index("idx_files_topic_status", table_name="files")
    op.drop_index("idx_files_topic_owner", table_name="files")
    op.drop_index("idx_files_topic_id", table_name="files")

    # Drop foreign key constraint
    op.drop_constraint("fk_files_topic_id", "files", type_="foreignkey")

    # Drop the column
    op.drop_column("files", "topic_id")
