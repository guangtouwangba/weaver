"""Add outputs table for storing generated mindmaps, summaries, etc.

Revision ID: 20241224_000001
Revises: 20241213_000003_add_highlights_table
Create Date: 2024-12-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241224_000001"
down_revision: Union[str, None] = "20241213_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create outputs table."""
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
        sa.Column("output_type", sa.String(50), nullable=False),  # 'mindmap', 'summary', etc.
        sa.Column(
            "document_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("status", sa.String(20), nullable=False, default="generating"),
        sa.Column("title", sa.String(255), nullable=True),  # Optional title
        sa.Column("data", postgresql.JSONB, nullable=True),  # Output data (nodes, edges, etc.)
        sa.Column("error_message", sa.Text, nullable=True),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # Create index on output_type for filtering
    op.create_index("ix_outputs_output_type", "outputs", ["output_type"])


def downgrade() -> None:
    """Drop outputs table."""
    op.drop_index("ix_outputs_output_type", table_name="outputs")
    op.drop_table("outputs")

