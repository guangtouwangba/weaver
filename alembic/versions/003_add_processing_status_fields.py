"""Add processing_status and processing_error fields to topic_contents

Revision ID: 003
Revises: 002
Create Date: 2025-11-03 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add processing_status and processing_error columns."""
    # Add processing_status column with default value
    op.add_column(
        'topic_contents',
        sa.Column('processing_status', sa.String(), nullable=False, server_default='not_started')
    )
    
    # Add processing_error column
    op.add_column(
        'topic_contents',
        sa.Column('processing_error', sa.Text(), nullable=True)
    )
    
    # Create index on processing_status for efficient filtering
    op.create_index(
        'ix_topic_contents_processing_status',
        'topic_contents',
        ['processing_status']
    )


def downgrade() -> None:
    """Remove processing_status and processing_error columns."""
    op.drop_index('ix_topic_contents_processing_status', table_name='topic_contents')
    op.drop_column('topic_contents', 'processing_error')
    op.drop_column('topic_contents', 'processing_status')

