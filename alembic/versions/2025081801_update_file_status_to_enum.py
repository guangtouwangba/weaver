"""Update file status to use enum type

Revision ID: 2025081801
Revises: 2025081703
Create Date: 2025-08-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025081801'
down_revision = '2025081703'
branch_labels = None
depends_on = None


def upgrade():
    """Update status column to use enum type."""
    
    # Create the enum type
    file_status_enum = postgresql.ENUM(
        'uploading', 'available', 'processing', 'failed', 'deleted', 'quarantined',
        name='file_status_enum'
    )
    file_status_enum.create(op.get_bind())
    
    # Update existing integer values to string values
    # Map old integer values to new string values
    op.execute("""
        UPDATE files 
        SET status = CASE 
            WHEN status = 0 THEN 'uploading'
            WHEN status = 1 THEN 'available' 
            WHEN status = 2 THEN 'processing'
            WHEN status = 3 THEN 'available'  -- old 'processed' -> 'available'
            WHEN status = 4 THEN 'failed'
            WHEN status = 5 THEN 'deleted'
            ELSE 'uploading'  -- default for any other values
        END
    """)
    
    # Change column type to enum
    op.alter_column('files', 'status',
                    type_=file_status_enum,
                    postgresql_using="status::file_status_enum",
                    nullable=False,
                    server_default="'uploading'")


def downgrade():
    """Revert status column back to integer type."""
    
    # Update string values back to integer values
    op.execute("""
        UPDATE files 
        SET status = CASE 
            WHEN status = 'uploading' THEN 0
            WHEN status = 'available' THEN 1
            WHEN status = 'processing' THEN 2
            WHEN status = 'failed' THEN 4
            WHEN status = 'deleted' THEN 5
            WHEN status = 'quarantined' THEN 0  -- map to uploading
            ELSE 0  -- default
        END
    """)
    
    # Change column type back to integer
    op.alter_column('files', 'status',
                    type_=sa.Integer(),
                    nullable=False,
                    server_default="0")
    
    # Drop the enum type
    op.execute('DROP TYPE file_status_enum')
