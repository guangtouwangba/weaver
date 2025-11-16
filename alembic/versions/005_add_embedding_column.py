"""Add embedding column to messages table

Revision ID: 005
Revises: 004
Create Date: 2025-11-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add embedding column to messages table and enable pgvector extension."""
    
    # 1. Enable pgvector extension if not already enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 2. Add embedding column to messages table
    op.execute("""
        ALTER TABLE messages 
        ADD COLUMN embedding vector(1536);
    """)
    
    # 3. Create index for vector similarity search (using HNSW for better performance)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_embedding 
        ON messages 
        USING hnsw (embedding vector_cosine_ops);
    """)


def downgrade() -> None:
    """Remove embedding column from messages table."""
    
    # 1. Drop the index
    op.execute("DROP INDEX IF EXISTS idx_messages_embedding;")
    
    # 2. Drop the embedding column
    op.execute("ALTER TABLE messages DROP COLUMN IF EXISTS embedding;")
    
    # Note: We don't drop the vector extension as other tables might be using it




