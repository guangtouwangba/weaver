"""Rename outputs.document_ids to source_ids.

Revision ID: 20260111_000001
Revises: 20260110_000001_add_user_id_to_projects
Create Date: 2026-01-11

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260111_000001"
down_revision: Union[str, None] = "20260110_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename document_ids column to source_ids."""
    op.alter_column(
        "outputs",
        "document_ids",
        new_column_name="source_ids",
    )


def downgrade() -> None:
    """Rename source_ids column back to document_ids."""
    op.alter_column(
        "outputs",
        "source_ids",
        new_column_name="document_ids",
    )
