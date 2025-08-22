"""add_content_type_to_documents

Revision ID: 2f34d9c08631
Revises: cac027415fb8
Create Date: 2025-08-22 10:53:58.367451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f34d9c08631'
down_revision: Union[str, None] = 'cac027415fb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add content_type column to documents table if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'content_type'
            ) THEN
                ALTER TABLE documents ADD COLUMN content_type VARCHAR(50) NOT NULL DEFAULT 'text';
            END IF;
        END $$;
    """)
    
    # Create document_chunks table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id VARCHAR(255) NOT NULL,
            document_id VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            start_char INTEGER,
            end_char INTEGER,
            embedding_vector TEXT,
            chunk_metadata JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id),
            CONSTRAINT fk_document_chunks_document_id FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        );
    """)
    
    # Create indexes if they don't exist
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_content_type ON documents (content_type);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks (document_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index ON document_chunks (chunk_index);")


def downgrade() -> None:
    # Remove content_type column from documents table
    op.drop_column('documents', 'content_type')
    
    # Drop document_chunks table
    op.drop_table('document_chunks')
