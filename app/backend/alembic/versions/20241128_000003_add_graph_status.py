"""Add graph_status to documents table

Revision ID: 20241128_000003
Revises: 20241128_000002
Create Date: 2024-11-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20241128_000003'
down_revision: Union[str, None] = '20241128_000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add graph_status column to documents table
    # Default to 'pending' for new rows
    # For existing rows, we'll update them based on current status in a separate step if needed,
    # but for now defaulting to 'ready' for existing completed docs is safer, or just 'pending'.
    # Since we're adding it nullable first, we can populate it.
    
    op.add_column('documents', sa.Column('graph_status', sa.String(50), nullable=False, server_default='pending'))
    
    # Create index for performance
    op.create_index('ix_documents_graph_status', 'documents', ['graph_status'])


def downgrade() -> None:
    op.drop_index('ix_documents_graph_status', table_name='documents')
    op.drop_column('documents', 'graph_status')

