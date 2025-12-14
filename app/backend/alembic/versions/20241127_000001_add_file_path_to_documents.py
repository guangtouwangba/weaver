"""Add file_path to documents

Revision ID: 20241127_000001
Revises: 20241126_000001
Create Date: 2024-11-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20241127_000001'
down_revision: Union[str, None] = '20241126_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column exists before adding
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='documents' AND column_name='file_path'
    """))
    
    if not result.fetchone():
        # Add file_path column if it doesn't exist
        op.add_column('documents', sa.Column('file_path', sa.String(512), nullable=True))
        
        # Update existing rows with a default value (filename as file_path)
        op.execute("""
            UPDATE documents 
            SET file_path = filename 
            WHERE file_path IS NULL
        """)
        
        # Make the column non-nullable after populating it
        op.alter_column('documents', 'file_path', nullable=False)


def downgrade() -> None:
    op.drop_column('documents', 'file_path')

