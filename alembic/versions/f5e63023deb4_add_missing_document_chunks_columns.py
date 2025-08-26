"""add_missing_document_chunks_columns

Revision ID: f5e63023deb4
Revises: 1c8e97d7b144
Create Date: 2025-08-26 11:27:01.877420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5e63023deb4'
down_revision: Union[str, None] = '1c8e97d7b144'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 确保document_chunks表存在并包含所有必要的列
    
    # 首先检查表是否存在，如果不存在则创建
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
    
    # 添加缺失的列（如果它们不存在）
    try:
        # 检查并添加start_char列
        op.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' AND column_name = 'start_char'
                ) THEN
                    ALTER TABLE document_chunks ADD COLUMN start_char INTEGER;
                END IF;
            END $$;
        """)
        
        # 检查并添加end_char列
        op.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' AND column_name = 'end_char'
                ) THEN
                    ALTER TABLE document_chunks ADD COLUMN end_char INTEGER;
                END IF;
            END $$;
        """)
        
        # 检查并添加embedding_vector列
        op.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' AND column_name = 'embedding_vector'
                ) THEN
                    ALTER TABLE document_chunks ADD COLUMN embedding_vector TEXT;
                END IF;
            END $$;
        """)
        
        # 检查并添加chunk_metadata列
        op.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' AND column_name = 'chunk_metadata'
                ) THEN
                    ALTER TABLE document_chunks ADD COLUMN chunk_metadata JSON NOT NULL DEFAULT '{}';
                END IF;
            END $$;
        """)
        
        # 检查并添加created_at列
        op.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'document_chunks' AND column_name = 'created_at'
                ) THEN
                    ALTER TABLE document_chunks ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
                END IF;
            END $$;
        """)
        
    except Exception as e:
        print(f"Warning: Could not add some columns: {e}")
    
    # 创建索引（如果不存在）
    try:
        op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks (document_id);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index ON document_chunks (chunk_index);")
    except Exception as e:
        print(f"Warning: Could not create indexes: {e}")


def downgrade() -> None:
    # 注意：这个迁移不应该删除列，因为我们不确定它们是否在之前的迁移中创建的
    pass
