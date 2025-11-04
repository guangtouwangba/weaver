"""Add topic_contents table

Revision ID: 002
Revises: 001
Create Date: 2025-11-03 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create topic_contents table."""
    op.create_table(
        'topic_contents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(1000), nullable=True),
        sa.Column('document_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('understanding_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('estimated_time', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('highlights', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('last_viewed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_topic_contents_topic_id', 'topic_contents', ['topic_id'])
    op.create_index('ix_topic_contents_status', 'topic_contents', ['status'])
    op.create_index('ix_topic_contents_added_at', 'topic_contents', ['added_at'])


def downgrade() -> None:
    """Drop topic_contents table."""
    op.drop_index('ix_topic_contents_added_at', table_name='topic_contents')
    op.drop_index('ix_topic_contents_status', table_name='topic_contents')
    op.drop_index('ix_topic_contents_topic_id', table_name='topic_contents')
    op.drop_table('topic_contents')

