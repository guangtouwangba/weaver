"""Add long context mode fields to documents and document_chunks

Revision ID: 20241204_000002
Revises: 20241204_000001
Create Date: 2024-12-04 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241204_000002'
down_revision: Union[str, None] = '20241204_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add long context mode fields to documents and document_chunks tables."""
    
    # Add fields to documents table
    op.add_column(
        'documents',
        sa.Column('full_content', sa.Text(), nullable=True)
    )
    op.add_column(
        'documents',
        sa.Column('content_token_count', sa.Integer(), nullable=True)
    )
    op.add_column(
        'documents',
        sa.Column('parsing_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Add citation and positioning fields to document_chunks table
    op.add_column(
        'document_chunks',
        sa.Column('char_start', sa.Integer(), nullable=True)
    )
    op.add_column(
        'document_chunks',
        sa.Column('char_end', sa.Integer(), nullable=True)
    )
    op.add_column(
        'document_chunks',
        sa.Column('paragraph_index', sa.Integer(), nullable=True)
    )
    op.add_column(
        'document_chunks',
        sa.Column('sentence_index', sa.Integer(), nullable=True)
    )
    
    # Create indexes for better query performance
    op.create_index('idx_documents_content_token_count', 'documents', ['content_token_count'])
    op.create_index('idx_document_chunks_char_start', 'document_chunks', ['char_start'])
    op.create_index('idx_document_chunks_char_end', 'document_chunks', ['char_end'])


def downgrade() -> None:
    """Remove long context mode fields from documents and document_chunks tables."""
    
    # Drop indexes
    op.drop_index('idx_document_chunks_char_end', table_name='document_chunks')
    op.drop_index('idx_document_chunks_char_start', table_name='document_chunks')
    op.drop_index('idx_documents_content_token_count', table_name='documents')
    
    # Remove fields from document_chunks table
    op.drop_column('document_chunks', 'sentence_index')
    op.drop_column('document_chunks', 'paragraph_index')
    op.drop_column('document_chunks', 'char_end')
    op.drop_column('document_chunks', 'char_start')
    
    # Remove fields from documents table
    op.drop_column('documents', 'parsing_metadata')
    op.drop_column('documents', 'content_token_count')
    op.drop_column('documents', 'full_content')


