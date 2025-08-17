"""Add missing timestamp columns to topic_resources table

Revision ID: 2025081703
Revises: 2025081702
Create Date: 2025-08-17 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2025081703'
down_revision = '2025081702'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing BaseModel timestamp columns to topic_resources table."""
    
    # Add BaseModel timestamp columns that are missing
    op.add_column('topic_resources',
                  sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('topic_resources',
                  sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade():
    """Remove added timestamp columns."""
    
    # Drop added columns
    op.drop_column('topic_resources', 'updated_at')
    op.drop_column('topic_resources', 'created_at')