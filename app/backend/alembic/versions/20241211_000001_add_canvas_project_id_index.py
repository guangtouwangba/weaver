"""Add explicit B-tree index on canvases.project_id for query performance.

Revision ID: 20241211_000001
Revises: 20241209_000002
Create Date: 2024-12-11

This migration adds:
- Explicit B-tree index on canvases.project_id to ensure query performance
- Note: UNIQUE constraint already creates an implicit index, but this ensures
  optimal query plans for SELECT ... WHERE project_id = ? FOR UPDATE queries
"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241211_000001"
down_revision: str = "20241209_000002"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # Create explicit B-tree index on project_id for query performance
    # Using IF NOT EXISTS to avoid errors if index already exists
    # (UNIQUE constraint may have already created an index)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_canvases_project_id_btree 
        ON canvases (project_id)
        """
    )


def downgrade() -> None:
    # Drop the index if it exists
    op.execute("DROP INDEX IF EXISTS idx_canvases_project_id_btree")




