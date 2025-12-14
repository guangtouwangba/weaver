"""Add data column to canvases

Revision ID: 20241127_000002
Revises: 20241127_000001
Create Date: 2024-11-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20241127_000002'
down_revision: Union[str, None] = '20241127_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if data column exists before adding
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='canvases' AND column_name='data'
    """))
    
    if not result.fetchone():
        # Add data column
        op.add_column('canvases', 
            sa.Column('data', postgresql.JSONB, nullable=False, server_default='{}')
        )
        
        # Migrate existing data from nodes/edges/viewport to data column
        # This handles the old schema where canvas data was split into separate columns
        conn.execute(sa.text("""
            UPDATE canvases 
            SET data = jsonb_build_object(
                'nodes', COALESCE(nodes, '[]'::jsonb),
                'edges', COALESCE(edges, '[]'::jsonb),
                'viewport', COALESCE(viewport, '{}'::jsonb)
            )
            WHERE data = '{}'::jsonb
        """))


def downgrade() -> None:
    op.drop_column('canvases', 'data')

