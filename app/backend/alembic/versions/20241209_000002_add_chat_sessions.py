"""Add chat_sessions table for multi-conversation support.

Revision ID: 20241209_000002
Revises: 20241209_000001
Create Date: 2024-12-09

This migration adds:
- chat_sessions: Table for managing multiple chat conversations per project
- session_id column to chat_messages for linking messages to sessions
- Data migration to create default sessions for existing messages
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241209_000002"
down_revision: str = "20241209_000001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # 1. Create chat_sessions table
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
        # NULL = shared session, has value = private session for that user/device
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False, default="New Conversation"),
        # Redundant field for easier querying: True = shared, False = private
        sa.Column("is_shared", sa.Boolean, nullable=False, default=True),
        # Timestamp of last message for sorting sessions
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    # Create composite indexes for efficient querying
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

    # 2. Add session_id column to chat_messages (nullable initially for migration)
    op.add_column(
        "chat_messages",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 3. Create default shared sessions for each project that has chat messages
    op.execute(
        sa.text(
            """
            INSERT INTO chat_sessions (id, project_id, user_id, title, is_shared, last_message_at, created_at, updated_at)
            SELECT 
                gen_random_uuid(),
                project_id,
                NULL,
                'Default Conversation',
                TRUE,
                MAX(created_at),
                MIN(created_at),
                NOW()
            FROM chat_messages
            GROUP BY project_id
            """
        )
    )

    # 4. Link existing messages to their project's default session
    op.execute(
        sa.text(
            """
            UPDATE chat_messages cm
            SET session_id = cs.id
            FROM chat_sessions cs
            WHERE cm.project_id = cs.project_id
            AND cs.title = 'Default Conversation'
            AND cs.is_shared = TRUE
            AND cm.session_id IS NULL
            """
        )
    )

    # 5. Add foreign key constraint after data migration
    op.create_foreign_key(
        "fk_chat_messages_session_id",
        "chat_messages",
        "chat_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 6. Create index on session_id for efficient querying
    op.create_index(
        "idx_chat_messages_session_created",
        "chat_messages",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    # Use raw SQL with IF EXISTS to handle partial migration state safely
    # This allows downgrade to work even if migration was partially applied

    # 1. Drop index on chat_messages (if exists)
    op.execute(sa.text("DROP INDEX IF EXISTS idx_chat_messages_session_created"))

    # 2. Drop foreign key (if exists)
    op.execute(
        sa.text(
            """
            ALTER TABLE chat_messages 
            DROP CONSTRAINT IF EXISTS fk_chat_messages_session_id
            """
        )
    )

    # 3. Drop session_id column (if exists)
    op.execute(
        sa.text(
            """
            ALTER TABLE chat_messages 
            DROP COLUMN IF EXISTS session_id
            """
        )
    )

    # 4. Drop chat_sessions indexes (if exist)
    op.execute(sa.text("DROP INDEX IF EXISTS idx_chat_sessions_project_shared_last_message"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_chat_sessions_project_user_last_message"))

    # 5. Drop chat_sessions table (if exists)
    op.execute(sa.text("DROP TABLE IF EXISTS chat_sessions"))






