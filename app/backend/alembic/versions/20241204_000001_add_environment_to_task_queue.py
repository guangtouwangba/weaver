"""Add environment column to task_queue for isolation

Revision ID: 20241204_000001
Revises: 20241202_000003
Create Date: 2024-12-04 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20241204_000001'
down_revision: Union[str, None] = '20241202_000003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add environment column to task_queue table for environment isolation."""
    
    # Add environment column with default value 'development'
    op.add_column(
        'task_queue',
        sa.Column('environment', sa.String(50), nullable=False, server_default='development')
    )
    
    # Create index on environment for faster filtering
    op.create_index('idx_task_queue_environment', 'task_queue', ['environment'])


def downgrade() -> None:
    """Remove environment column from task_queue table."""
    
    op.drop_index('idx_task_queue_environment', table_name='task_queue')
    op.drop_column('task_queue', 'environment')

