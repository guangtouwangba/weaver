"""Extend highlights model.

Revision ID: 20241230_000001
Revises: 20241229_000001
Create Date: 2024-12-30

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20241230_000001"
down_revision = "20241229_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add type and text_content columns to highlights table
    op.add_column(
        "highlights", sa.Column("type", sa.String(20), nullable=False, server_default="highlight")
    )
    op.add_column("highlights", sa.Column("text_content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("highlights", "text_content")
    op.drop_column("highlights", "type")
