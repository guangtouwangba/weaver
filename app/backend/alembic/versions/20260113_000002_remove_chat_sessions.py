"""Remove chat_sessions table and session_id from chat_messages.

Revision ID: 20260113_000002
Revises: 20260113_000001
Create Date: 2026-01-13

This migration removes the chat sessions feature, simplifying to a single
conversation history per project. The session_id column and chat_sessions
table are dropped.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260113_000002"
down_revision = "20260113_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop index on session_id
    op.execute(sa.text("DROP INDEX IF EXISTS idx_chat_messages_session_created"))

    # 2. Drop foreign key constraint
    op.execute(
        sa.text(
            """
            ALTER TABLE chat_messages 
            DROP CONSTRAINT IF EXISTS fk_chat_messages_session_id
            """
        )
    )

    # 3. Drop session_id column from chat_messages
    op.drop_column("chat_messages", "session_id")

    # 4. Drop chat_sessions indexes
    op.execute(sa.text("DROP INDEX IF EXISTS idx_chat_sessions_project_shared_last_message"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_chat_sessions_project_user_last_message"))

    # 5. Drop chat_sessions table
    op.drop_table("chat_sessions")


def downgrade() -> None:
    # 1. Recreate chat_sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False, server_default="New Conversation"),
        sa.Column("is_shared", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # 2. Create indexes
    op.create_index(
        "idx_chat_sessions_project_user_last_message",
        "chat_sessions",
        ["project_id", "user_id", "last_message_at"],
    )
    op.create_index(
        "idx_chat_sessions_project_shared_last_message",
        "chat_sessions",
        ["project_id", "is_shared", "last_message_at"],
    )

    # 3. Add session_id column back to chat_messages
    op.add_column(
        "chat_messages",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 4. Add foreign key constraint
    op.create_foreign_key(
        "fk_chat_messages_session_id",
        "chat_messages",
        "chat_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. Create index
    op.create_index(
        "idx_chat_messages_session_created",
        "chat_messages",
        ["session_id", "created_at"],
    )
