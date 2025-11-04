"""Create topics table

Revision ID: 001
Revises: 
Create Date: 2024-11-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create topics table."""
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("goal_type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("completion_progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_contents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("understood_contents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("practiced_contents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    
    # Create indices
    op.create_index("ix_topics_name", "topics", ["name"])
    op.create_index("ix_topics_goal_type", "topics", ["goal_type"])
    op.create_index("ix_topics_status", "topics", ["status"])


def downgrade() -> None:
    """Drop topics table."""
    op.drop_index("ix_topics_status", table_name="topics")
    op.drop_index("ix_topics_goal_type", table_name="topics")
    op.drop_index("ix_topics_name", table_name="topics")
    op.drop_table("topics")

