"""Add TSVector column for hybrid search

Revision ID: 20241202_000002
Revises: 20241202_000001
Create Date: 2024-12-02 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241202_000002'
down_revision: Union[str, None] = '20241202_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add TSVector column and GIN index for full-text search."""
    
    # Add content_tsvector column
    op.add_column(
        'document_chunks',
        sa.Column('content_tsvector', postgresql.TSVECTOR(), nullable=True)
    )
    
    # Create GIN index for full-text search
    op.execute("""
        CREATE INDEX idx_document_chunks_content_tsvector 
        ON document_chunks 
        USING GIN (content_tsvector)
    """)
    
    # Create trigger to automatically update tsvector on insert/update
    op.execute("""
        CREATE TRIGGER tsvector_update_trigger
        BEFORE INSERT OR UPDATE ON document_chunks
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(
            content_tsvector,
            'pg_catalog.english',
            content
        )
    """)
    
    # Populate existing rows
    op.execute("""
        UPDATE document_chunks
        SET content_tsvector = to_tsvector('english', content)
        WHERE content IS NOT NULL
    """)


def downgrade() -> None:
    """Remove TSVector column and related objects."""
    
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS tsvector_update_trigger ON document_chunks")
    
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_tsvector")
    
    # Drop column
    op.drop_column('document_chunks', 'content_tsvector')

