"""add_missing_fields_to_topics

Revision ID: 9908bf557982
Revises: 002
Create Date: 2025-08-16 11:21:47.016302

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9908bf557982"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create topic_status_enum type if it doesn't exist
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE topic_status_enum AS ENUM ('active', 'archived', 'draft', 'completed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    # Add missing fields to topics table
    op.add_column(
        "topics",
        sa.Column(
            "status",
            sa.Enum(
                "active", "archived", "draft", "completed", name="topic_status_enum"
            ),
            nullable=True,
            server_default="active",
        ),
    )
    op.add_column(
        "topics", sa.Column("parent_topic_id", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "topics", sa.Column("settings", sa.JSON(), nullable=True, server_default="{}")
    )
    op.add_column(
        "topics",
        sa.Column("total_resources", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "topics",
        sa.Column(
            "total_conversations", sa.Integer(), nullable=True, server_default="0"
        ),
    )

    # Add foreign key constraint for parent_topic_id
    op.create_foreign_key(
        "fk_topics_parent_topic_id",
        "topics",
        "topics",
        ["parent_topic_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create index for parent_topic_id
    op.create_index("idx_topics_parent_topic_id", "topics", ["parent_topic_id"])

    # Create index for status
    op.create_index("idx_topics_status", "topics", ["status"])

    # Create composite index for user_id and status
    op.create_index("idx_topics_user_status", "topics", ["user_id", "status"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_topics_user_status", table_name="topics")
    op.drop_index("idx_topics_status", table_name="topics")
    op.drop_index("idx_topics_parent_topic_id", table_name="topics")

    # Drop foreign key constraint
    op.drop_constraint("fk_topics_parent_topic_id", "topics", type_="foreignkey")

    # Drop columns
    op.drop_column("topics", "settings")
    op.drop_column("topics", "parent_topic_id")
    op.drop_column("topics", "status")
    op.drop_column("topics", "total_resources")
    op.drop_column("topics", "total_conversations")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS topic_status_enum;")
