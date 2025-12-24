"""Add progress tracking fields to documents table.

Revision ID: 20241213_000001
Revises: 20241211_000003
Create Date: 2024-12-13

This migration adds progress tracking fields for SSE real-time updates:
- processing_stage: Current processing stage (extracting/chunking/embedding)
- progress_percent: Progress percentage (0.0 - 100.0)
- progress_message: Optional detailed progress message
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241213_000001"
down_revision: Union[str, None] = "20241211_000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add progress tracking columns to documents table."""
    # processing_stage: Current stage of document processing
    op.add_column(
        "documents",
        sa.Column("processing_stage", sa.String(50), nullable=True),
    )
    
    # progress_percent: Progress percentage (0.0 - 100.0)
    op.add_column(
        "documents",
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0.0"),
    )
    
    # progress_message: Optional detailed progress message
    op.add_column(
        "documents",
        sa.Column("progress_message", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Remove progress tracking columns from documents table."""
    op.drop_column("documents", "progress_message")
    op.drop_column("documents", "progress_percent")
    op.drop_column("documents", "processing_stage")












