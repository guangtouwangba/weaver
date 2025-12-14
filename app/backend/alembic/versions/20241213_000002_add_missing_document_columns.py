"""Add missing document columns (original_filename, mime_type, updated_at)

Revision ID: 20241213_000002
Revises: 20241213_000001
Create Date: 2024-12-13

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241213_000002"
down_revision: Union[str, None] = "20241213_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add original_filename column
    op.add_column("documents", sa.Column("original_filename", sa.String(255), nullable=True))
    # Set default value for existing rows (copy from filename)
    op.execute("UPDATE documents SET original_filename = filename WHERE original_filename IS NULL")
    # Make it not nullable
    op.alter_column("documents", "original_filename", nullable=False)

    # Add mime_type column
    op.add_column("documents", sa.Column("mime_type", sa.String(100), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE documents SET mime_type = 'application/pdf' WHERE mime_type IS NULL")
    # Make it not nullable
    op.alter_column("documents", "mime_type", nullable=False)

    # Add updated_at column
    op.add_column(
        "documents",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
    )
    # Set default value for existing rows
    op.execute("UPDATE documents SET updated_at = created_at WHERE updated_at IS NULL")
    # Make it not nullable
    op.alter_column("documents", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("documents", "updated_at")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "original_filename")
