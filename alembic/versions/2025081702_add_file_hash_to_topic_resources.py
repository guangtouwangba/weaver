"""Add file_hash column to topic_resources table

Revision ID: 2025081702
Revises: 2025081701
Create Date: 2025-08-17 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2025081702"
down_revision = "2025081701"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to topic_resources table to match SQLAlchemy model."""

    # Add file_hash column for deduplication
    op.add_column(
        "topic_resources", sa.Column("file_hash", sa.VARCHAR(64), nullable=True)
    )

    # Add content_summary column
    op.add_column(
        "topic_resources", sa.Column("content_summary", sa.TEXT(), nullable=True)
    )

    # Add parse_attempts column
    op.add_column(
        "topic_resources",
        sa.Column("parse_attempts", sa.INTEGER(), nullable=False, server_default="0"),
    )

    # Add access control columns
    op.add_column(
        "topic_resources",
        sa.Column(
            "is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column(
        "topic_resources",
        sa.Column(
            "access_level",
            sa.VARCHAR(20),
            nullable=False,
            server_default=sa.text("'private'"),
        ),
    )

    # Add source_url column for web imports
    op.add_column("topic_resources", sa.Column("source_url", sa.TEXT(), nullable=True))

    # Add BaseModel timestamp columns that are missing
    op.add_column(
        "topic_resources",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column(
        "topic_resources",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Note: Keep existing 'metadata' column name for backward compatibility
    # The SQLAlchemy model maps 'resource_metadata' to the 'metadata' database column

    # Add unique constraint for file_hash (allows NULL values)
    op.create_unique_constraint(
        "uq_topic_resources_file_hash", "topic_resources", ["file_hash"]
    )

    # Create index for file_hash column for better query performance
    op.create_index("idx_topic_resources_file_hash", "topic_resources", ["file_hash"])


def downgrade():
    """Remove added columns and revert changes."""

    # Drop index first
    op.drop_index("idx_topic_resources_file_hash", table_name="topic_resources")

    # Drop unique constraint
    op.drop_constraint(
        "uq_topic_resources_file_hash", "topic_resources", type_="unique"
    )

    # Note: No column rename to revert since we didn't rename in upgrade

    # Drop added columns in reverse order
    op.drop_column("topic_resources", "updated_at")
    op.drop_column("topic_resources", "created_at")
    op.drop_column("topic_resources", "source_url")
    op.drop_column("topic_resources", "access_level")
    op.drop_column("topic_resources", "is_public")
    op.drop_column("topic_resources", "parse_attempts")
    op.drop_column("topic_resources", "content_summary")
    op.drop_column("topic_resources", "file_hash")
