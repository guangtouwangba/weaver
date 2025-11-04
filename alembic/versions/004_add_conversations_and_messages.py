"""Add conversations and messages tables

Revision ID: 004
Revises: 003
Create Date: 2025-11-04 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create conversations and messages tables."""
    
    # 1. Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
    )
    
    # 2. Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sources', postgresql.ARRAY(sa.Text()), nullable=True),
        # Reserved for future: embedding field for semantic search
        # sa.Column('embedding', postgresql.VECTOR(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_message_role'),
    )
    
    # 3. Create indexes for conversations
    op.create_index('ix_conversations_topic_id', 'conversations', ['topic_id', 'updated_at'], postgresql_using='btree')
    op.create_index('ix_conversations_updated_at', 'conversations', ['updated_at'], postgresql_using='btree')
    
    # 4. Create indexes for messages
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id', 'created_at'], postgresql_using='btree')
    op.create_index('ix_messages_created_at', 'messages', ['created_at'], postgresql_using='btree')
    op.create_index('ix_messages_role', 'messages', ['role', 'created_at'], postgresql_using='btree')
    
    # 5. Create trigger to auto-update conversation statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION update_conversation_stats()
        RETURNS TRIGGER AS $$
        BEGIN
            UPDATE conversations
            SET 
                message_count = message_count + 1,
                last_message_at = NEW.created_at,
                updated_at = NOW()
            WHERE id = NEW.conversation_id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_update_conversation_stats
        AFTER INSERT ON messages
        FOR EACH ROW EXECUTE FUNCTION update_conversation_stats();
    """)


def downgrade() -> None:
    """Drop conversations and messages tables."""
    
    # 1. Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trigger_update_conversation_stats ON messages;")
    op.execute("DROP FUNCTION IF EXISTS update_conversation_stats();")
    
    # 2. Drop indexes for messages
    op.drop_index('ix_messages_role', table_name='messages')
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    
    # 3. Drop indexes for conversations
    op.drop_index('ix_conversations_updated_at', table_name='conversations')
    op.drop_index('ix_conversations_topic_id', table_name='conversations')
    
    # 4. Drop tables
    op.drop_table('messages')
    op.drop_table('conversations')

