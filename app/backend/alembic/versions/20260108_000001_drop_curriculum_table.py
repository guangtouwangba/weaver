"""Drop curriculum table

Revision ID: 20260108_000001
Revises: 20250107_000003
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260108_000001'
down_revision: Union[str, None] = '20250107_000003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop curriculums table (feature was never used)
    op.drop_index('ix_curriculums_project_id', table_name='curriculums')
    op.drop_table('curriculums')


def downgrade() -> None:
    # Recreate curriculums table if needed
    op.create_table(
        'curriculums',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('steps', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('total_duration', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id')
    )
    op.create_index('ix_curriculums_project_id', 'curriculums', ['project_id'])
