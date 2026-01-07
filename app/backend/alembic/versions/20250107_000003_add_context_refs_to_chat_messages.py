"""Add context_refs column to chat_messages table.

Revision ID: 20250107_000003
Revises: 20250107_000002
Create Date: 2025-01-07

This migration adds a context_refs JSONB column to store context references
(URL IDs, node IDs, node metadata) attached to user messages.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "20250107_000003"
down_revision: Union[str, None] = "20250107_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add context_refs column to chat_messages table."""
    op.add_column(
        "chat_messages",
        sa.Column("context_refs", JSONB, nullable=True),
    )


def downgrade() -> None:
    """Remove context_refs column from chat_messages table."""
    op.drop_column("chat_messages", "context_refs")

