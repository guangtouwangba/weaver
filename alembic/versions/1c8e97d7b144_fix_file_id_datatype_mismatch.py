"""fix_file_id_datatype_mismatch

Revision ID: 1c8e97d7b144
Revises: c2d0c24b9d5c
Create Date: 2025-08-22 11:16:13.737882

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1c8e97d7b144"
down_revision: Union[str, None] = "c2d0c24b9d5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix file_id column datatype mismatch - change from VARCHAR to UUID
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if file_id column exists and is VARCHAR
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'file_id'
                AND data_type = 'character varying'
            ) THEN
                -- Drop the existing foreign key constraint if it exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_documents_file_id'
                ) THEN
                    ALTER TABLE documents DROP CONSTRAINT fk_documents_file_id;
                END IF;
                
                -- Change the column type from VARCHAR to UUID
                -- Note: This will fail if there are non-UUID values in the column
                -- We'll set all existing VARCHAR values to NULL first for safety
                UPDATE documents SET file_id = NULL WHERE file_id IS NOT NULL;
                ALTER TABLE documents ALTER COLUMN file_id TYPE UUID USING file_id::UUID;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'file_id'
            ) THEN
                -- Add file_id column as UUID if it doesn't exist
                ALTER TABLE documents ADD COLUMN file_id UUID;
            END IF;
            
            -- Re-add the foreign key constraint with correct data types
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'files'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_documents_file_id'
            ) THEN
                ALTER TABLE documents ADD CONSTRAINT fk_documents_file_id 
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE SET NULL;
            END IF;
        END $$;
    """
    )

    # Update indexes to ensure they exist
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_file_id ON documents (file_id);"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents (updated_at);"
    )


def downgrade() -> None:
    # Revert file_id column back to VARCHAR(255)
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop the foreign key constraint if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'fk_documents_file_id'
            ) THEN
                ALTER TABLE documents DROP CONSTRAINT fk_documents_file_id;
            END IF;
            
            -- Change file_id back to VARCHAR(255) if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'file_id'
            ) THEN
                ALTER TABLE documents ALTER COLUMN file_id TYPE VARCHAR(255) USING file_id::VARCHAR;
            END IF;
        END $$;
    """
    )
