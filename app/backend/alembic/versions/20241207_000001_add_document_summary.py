"""Add summary column to documents

Revision ID: 20241207_000001
Revises: 20241204_000003
Create Date: 2024-12-07 00:00:01.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241207_000001"
down_revision: Union[str, None] = "20241204_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add summary column to documents table."""
    op.add_column("documents", sa.Column("summary", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove summary column from documents table."""
    op.drop_column("documents", "summary")
