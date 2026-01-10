"""Add user_id column to projects table for multi-tenant support.

Revision ID: 20260110_000001
Revises: 20260108_000001
Create Date: 2026-01-10
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260110_000001"
down_revision = "20260108_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to projects table
    op.add_column(
        "projects",
        sa.Column("user_id", sa.String(255), nullable=True),
    )
    # Add index for efficient user-based queries
    op.create_index("ix_projects_user_id", "projects", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_column("projects", "user_id")
