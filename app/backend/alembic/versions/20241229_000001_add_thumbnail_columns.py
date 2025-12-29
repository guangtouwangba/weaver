"""Add thumbnail columns to documents table.

Revision ID: 20241229_000001
Revises: 20241224_000001
Create Date: 2024-12-29

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20241229_000001"
down_revision = "20241224_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add thumbnail columns to documents table
    op.add_column("documents", sa.Column("thumbnail_path", sa.String(512), nullable=True))
    op.add_column("documents", sa.Column("thumbnail_status", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "thumbnail_status")
    op.drop_column("documents", "thumbnail_path")
