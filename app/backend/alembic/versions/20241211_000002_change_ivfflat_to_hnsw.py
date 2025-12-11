"""Change vector indexes from IVFFlat to HNSW for better delete performance.

Revision ID: 20241211_000002
Revises: 20241211_000001
Create Date: 2024-12-11

This migration changes:
- ix_document_chunks_embedding: IVFFlat -> HNSW
- idx_chat_memories_embedding: IVFFlat -> HNSW

HNSW indexes have better delete performance compared to IVFFlat because:
- IVFFlat requires cluster maintenance on every delete operation
- HNSW uses a graph structure that handles deletions more gracefully
- HNSW also typically provides better query performance
"""

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241211_000002"
down_revision: str = "20241211_000001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # Drop old IVFFlat index on document_chunks (if exists)
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding")

    # Create new HNSW index on document_chunks
    # m=16: number of connections per layer (default is 16, good balance)
    # ef_construction=64: size of dynamic candidate list during construction
    # Using IF NOT EXISTS to make migration idempotent (safe to re-run)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )

    # Drop old IVFFlat index on chat_memories (if exists)
    op.execute("DROP INDEX IF EXISTS idx_chat_memories_embedding")

    # Create new HNSW index on chat_memories
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_memories_embedding
        ON chat_memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    # Drop HNSW indexes
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding")
    op.execute("DROP INDEX IF EXISTS idx_chat_memories_embedding")

    # Recreate IVFFlat indexes (using IF NOT EXISTS for idempotency)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding
        ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_memories_embedding
        ON chat_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )
