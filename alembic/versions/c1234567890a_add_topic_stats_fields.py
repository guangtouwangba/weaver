"""add_topic_stats_fields

Revision ID: c1234567890a
Revises: 9908bf557982
Create Date: 2025-08-16 14:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1234567890a"
down_revision: Union[str, None] = "9908bf557982"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing statistics fields to topics table."""

    # Check if columns already exist before adding them
    conn = op.get_bind()

    # Check if total_resources column exists
    result = conn.execute(
        sa.text(
            """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'topics' AND column_name = 'total_resources'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "topics",
            sa.Column(
                "total_resources", sa.Integer(), nullable=True, server_default="0"
            ),
        )

    # Check if total_conversations column exists
    result = conn.execute(
        sa.text(
            """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'topics' AND column_name = 'total_conversations'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "topics",
            sa.Column(
                "total_conversations", sa.Integer(), nullable=True, server_default="0"
            ),
        )

    # Check if core_concepts_discovered column exists
    result = conn.execute(
        sa.text(
            """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'topics' AND column_name = 'core_concepts_discovered'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "topics",
            sa.Column(
                "core_concepts_discovered",
                sa.Integer(),
                nullable=True,
                server_default="0",
            ),
        )

    # Check if concept_relationships column exists
    result = conn.execute(
        sa.text(
            """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'topics' AND column_name = 'concept_relationships'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "topics",
            sa.Column(
                "concept_relationships", sa.Integer(), nullable=True, server_default="0"
            ),
        )

    # Check if missing_materials_count column exists
    result = conn.execute(
        sa.text(
            """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'topics' AND column_name = 'missing_materials_count'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "topics",
            sa.Column(
                "missing_materials_count",
                sa.Integer(),
                nullable=True,
                server_default="0",
            ),
        )

    # Check if last_accessed_at column exists
    result = conn.execute(
        sa.text(
            """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'topics' AND column_name = 'last_accessed_at'
    """
        )
    )

    if not result.fetchone():
        op.add_column(
            "topics",
            sa.Column(
                "last_accessed_at",
                sa.TIMESTAMP(timezone=True),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )


def downgrade() -> None:
    """Remove the added statistics fields."""

    # Drop columns (only if they exist)
    conn = op.get_bind()

    # List of columns to potentially drop
    columns_to_drop = [
        "total_resources",
        "total_conversations",
        "core_concepts_discovered",
        "concept_relationships",
        "missing_materials_count",
        "last_accessed_at",
    ]

    for column in columns_to_drop:
        result = conn.execute(
            sa.text(
                f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'topics' AND column_name = '{column}'
        """
            )
        )

        if result.fetchone():
            op.drop_column("topics", column)
