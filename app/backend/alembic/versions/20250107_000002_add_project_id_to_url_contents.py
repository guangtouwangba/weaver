"""Add project_id to url_contents table.

Revision ID: 20250107_000002
Revises: 20250107_000001
Create Date: 2025-01-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "20250107_000002"
down_revision: Union[str, None] = "20250107_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add project_id column to url_contents table."""
    op.add_column(
        "url_contents",
        sa.Column("project_id", UUID(as_uuid=True), nullable=True),
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        "fk_url_contents_project_id",
        "url_contents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    
    # Create index for faster lookups by project
    op.create_index(
        "ix_url_contents_project_id",
        "url_contents",
        ["project_id"],
    )


def downgrade() -> None:
    """Remove project_id column from url_contents table."""
    op.drop_index("ix_url_contents_project_id", table_name="url_contents")
    op.drop_constraint("fk_url_contents_project_id", "url_contents", type_="foreignkey")
    op.drop_column("url_contents", "project_id")

