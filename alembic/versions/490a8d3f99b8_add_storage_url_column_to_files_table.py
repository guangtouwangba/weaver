"""Add storage_url column to files table

Revision ID: 490a8d3f99b8
Revises: 2025081801
Create Date: 2025-08-20 13:45:02.911212

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "490a8d3f99b8"
down_revision: Union[str, None] = "2025081801"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add storage_url column to files table and fix model compatibility"""

    # Add the missing storage_url column
    op.add_column(
        "files", sa.Column("storage_url", sa.String(length=2000), nullable=True)
    )

    # Also need to handle the ID type mismatch between UUID and String
    # The current database has UUID primary key, but model expects String
    # We'll keep UUID but add a comment for clarity
    op.execute(
        "COMMENT ON COLUMN files.id IS 'Primary key as UUID, mapped to String in application'"
    )

    # Add any missing columns that the model expects
    # The model expects these but they may not exist in all cases

    # Add processing_status if it doesn't exist
    try:
        op.add_column(
            "files", sa.Column("processing_status", sa.String(length=50), nullable=True)
        )
    except Exception:
        # Column might already exist, ignore
        pass

    # Add error_message if it doesn't exist
    try:
        op.add_column("files", sa.Column("error_message", sa.Text(), nullable=True))
    except Exception:
        # Column might already exist, ignore
        pass

    # Add file_metadata if it doesn't exist (maps to custom_metadata)
    try:
        op.add_column("files", sa.Column("file_metadata", sa.JSON(), nullable=True))
    except Exception:
        # Column might already exist, ignore
        pass

    # Add user_id if it doesn't exist (maps to owner_id)
    try:
        op.add_column("files", sa.Column("user_id", sa.BigInteger(), nullable=True))
    except Exception:
        # Column might already exist, ignore
        pass


def downgrade() -> None:
    """Remove storage_url column and related changes"""

    # Remove the columns we added
    op.drop_column("files", "storage_url")

    try:
        op.drop_column("files", "processing_status")
    except Exception:
        pass

    try:
        op.drop_column("files", "error_message")
    except Exception:
        pass

    try:
        op.drop_column("files", "file_metadata")
    except Exception:
        pass

    try:
        op.drop_column("files", "user_id")
    except Exception:
        pass
