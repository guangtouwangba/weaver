"""Add highlights table for PDF annotations

Revision ID: 20241213_000003
Revises: 20241213_000002
Create Date: 2024-12-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241213_000003"
down_revision: Union[str, None] = "20241213_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "highlights",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(20), nullable=False, server_default="yellow"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("rects", JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    # Create index on document_id for faster lookups
    op.create_index("ix_highlights_document_id", "highlights", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_highlights_document_id")
    op.drop_table("highlights")

















