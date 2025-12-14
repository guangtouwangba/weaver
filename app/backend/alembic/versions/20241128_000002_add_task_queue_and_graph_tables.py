"""Add task_queue, entities, and relations tables for async processing and knowledge graph

Revision ID: 20241128_000002
Revises: 20241128_000001
Create Date: 2024-11-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241128_000002'
down_revision: Union[str, None] = '20241128_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create task_queue table for background job processing
    op.create_table(
        'task_queue',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='0'),
        sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer, nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_task_queue_status', 'task_queue', ['status'])
    op.create_index('ix_task_queue_task_type', 'task_queue', ['task_type'])
    op.create_index('ix_task_queue_scheduled_at', 'task_queue', ['scheduled_at'])
    
    # Create entities table for knowledge graph nodes
    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_entities_project_id', 'entities', ['project_id'])
    op.create_index('ix_entities_document_id', 'entities', ['document_id'])
    op.create_index('ix_entities_entity_type', 'entities', ['entity_type'])
    op.create_index('ix_entities_name', 'entities', ['name'])
    
    # Create relations table for knowledge graph edges
    op.create_table(
        'relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('weight', sa.Float, nullable=True, server_default='1.0'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_relations_project_id', 'relations', ['project_id'])
    op.create_index('ix_relations_source_entity_id', 'relations', ['source_entity_id'])
    op.create_index('ix_relations_target_entity_id', 'relations', ['target_entity_id'])
    op.create_index('ix_relations_relation_type', 'relations', ['relation_type'])


def downgrade() -> None:
    op.drop_table('relations')
    op.drop_table('entities')
    op.drop_table('task_queue')

