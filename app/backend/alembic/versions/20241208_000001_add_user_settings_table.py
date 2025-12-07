"""Add user_settings table.

Revision ID: 20241208_000001
Revises: 20241207_000002
Create Date: 2024-12-08

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241208_000001"
down_revision: str = "20241207_000002"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # Create user_settings table
    # Note: index=True in Column already creates indexes, no need for separate create_index calls
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("key", sa.String(255), nullable=False, index=True),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_encrypted", sa.Boolean, nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "key", name="uq_user_settings_user_key"),
    )


def downgrade() -> None:
    # drop_table will automatically drop indexes created with index=True
    op.drop_table("user_settings")
