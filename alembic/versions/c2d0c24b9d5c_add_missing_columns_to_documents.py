"""add_missing_columns_to_documents

Revision ID: c2d0c24b9d5c
Revises: 2f34d9c08631
Create Date: 2025-08-22 11:15:14.609614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d0c24b9d5c'
down_revision: Union[str, None] = '2f34d9c08631'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add all missing columns to documents table if they don't exist
    op.execute("""
        DO $$
        BEGIN
            -- Add file_id column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'file_id'
            ) THEN
                ALTER TABLE documents ADD COLUMN file_id VARCHAR(255);
            END IF;
            
            -- Add file_path column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'file_path'
            ) THEN
                ALTER TABLE documents ADD COLUMN file_path VARCHAR(1000);
            END IF;
            
            -- Add file_size column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'file_size'
            ) THEN
                ALTER TABLE documents ADD COLUMN file_size BIGINT NOT NULL DEFAULT 0;
            END IF;
            
            -- Add status column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'status'
            ) THEN
                ALTER TABLE documents ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'pending';
            END IF;
            
            -- Add processing_status column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'processing_status'
            ) THEN
                ALTER TABLE documents ADD COLUMN processing_status VARCHAR(50);
            END IF;
            
            -- Add doc_metadata column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'doc_metadata'
            ) THEN
                ALTER TABLE documents ADD COLUMN doc_metadata JSON NOT NULL DEFAULT '{}';
            END IF;
            
            -- Add updated_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'updated_at'
            ) THEN
                ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
            END IF;
        END $$;
    """)
    
    # Note: Foreign key constraint will be added in a later migration
    # after fixing the data type mismatch between file_id and files.id
    
    # Create additional indexes if they don't exist
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_id ON documents (file_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents (updated_at);")


def downgrade() -> None:
    # Remove the columns we added
    # Note: Foreign key constraint handled in separate migration
    op.drop_index('idx_documents_updated_at', table_name='documents')
    op.drop_index('idx_documents_status', table_name='documents')
    op.drop_index('idx_documents_file_id', table_name='documents')
    
    op.drop_column('documents', 'updated_at')
    op.drop_column('documents', 'doc_metadata')
    op.drop_column('documents', 'processing_status')
    op.drop_column('documents', 'status')
    op.drop_column('documents', 'file_size')
    op.drop_column('documents', 'file_path')
    op.drop_column('documents', 'file_id')
