"""Add evaluation log table

Revision ID: 20241202_000003
Revises: 20241202_000002
Create Date: 2024-12-02 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241202_000003'
down_revision: Union[str, None] = '20241202_000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create evaluation_logs table for storing RAG evaluation results."""
    
    op.create_table(
        'evaluation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True),
        
        # Test case information
        sa.Column('test_case_id', sa.String(100), nullable=True),  # Null for real-time evaluation
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('ground_truth', sa.Text(), nullable=True),  # Only for offline evaluation
        
        # Retrieval information
        sa.Column('chunking_strategy', sa.String(50), nullable=True),
        sa.Column('retrieval_mode', sa.String(50), nullable=True),  # 'vector', 'hybrid', etc.
        sa.Column('retrieved_contexts', postgresql.JSONB(), nullable=False),  # List of retrieved context strings
        
        # Generation information
        sa.Column('generated_answer', sa.Text(), nullable=True),
        
        # Evaluation metrics (Ragas)
        sa.Column('metrics', postgresql.JSONB(), nullable=False),
        # Example: {"faithfulness": 0.95, "answer_relevancy": 0.88, "context_precision": 0.92}
        
        # Metadata
        sa.Column('evaluation_type', sa.String(50), nullable=False, server_default='realtime'),  # 'realtime' or 'offline'
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_evaluation_logs_project_id', 'evaluation_logs', ['project_id'])
    op.create_index('idx_evaluation_logs_created_at', 'evaluation_logs', ['created_at'])
    op.create_index('idx_evaluation_logs_evaluation_type', 'evaluation_logs', ['evaluation_type'])
    op.create_index('idx_evaluation_logs_chunking_strategy', 'evaluation_logs', ['chunking_strategy'])


def downgrade() -> None:
    """Drop evaluation_logs table."""
    
    op.drop_index('idx_evaluation_logs_chunking_strategy', table_name='evaluation_logs')
    op.drop_index('idx_evaluation_logs_evaluation_type', table_name='evaluation_logs')
    op.drop_index('idx_evaluation_logs_created_at', table_name='evaluation_logs')
    op.drop_index('idx_evaluation_logs_project_id', table_name='evaluation_logs')
    op.drop_table('evaluation_logs')

