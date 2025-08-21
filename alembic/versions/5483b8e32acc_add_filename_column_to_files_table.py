"""add_filename_column_to_files_table

Revision ID: 5483b8e32acc
Revises: 490a8d3f99b8
Create Date: 2025-08-21 21:07:02.515884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5483b8e32acc'
down_revision: Union[str, None] = '490a8d3f99b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加filename字段到files表"""
    # 添加filename列
    op.add_column('files', sa.Column('filename', sa.String(length=255), nullable=True))
    
    # 将original_name的值复制到filename字段
    op.execute("UPDATE files SET filename = original_name WHERE filename IS NULL")
    
    # 设置filename为NOT NULL
    op.alter_column('files', 'filename', nullable=False)
    
    # 为filename字段创建索引
    op.create_index('idx_files_filename', 'files', ['filename'])


def downgrade() -> None:
    """回滚filename字段的添加"""
    # 删除索引
    op.drop_index('idx_files_filename', table_name='files')
    
    # 删除filename列
    op.drop_column('files', 'filename')
