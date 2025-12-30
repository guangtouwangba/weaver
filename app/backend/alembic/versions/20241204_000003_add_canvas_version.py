"""Add version field to canvases for optimistic locking

Revision ID: 20241204_000003
Revises: 20241204_000002
Create Date: 2024-12-04 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20241204_000003'
down_revision: Union[str, None] = '20241204_000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add version field to canvases table for optimistic locking."""
    
    # Add version column with default value 1
    op.add_column(
        'canvases',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )
    
    # Create index on version for better query performance
    op.create_index('idx_canvases_version', 'canvases', ['version'])


def downgrade() -> None:
    """Remove version field from canvases table."""
    
    # Drop index
    op.drop_index('idx_canvases_version', table_name='canvases')
    
    # Remove version column
    op.drop_column('canvases', 'version')






























