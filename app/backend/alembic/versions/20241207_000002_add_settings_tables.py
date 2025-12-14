"""Add global_settings and project_settings tables for configuration center.

Revision ID: 20241207_000002
Revises: 20241207_000001
Create Date: 2024-12-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20241207_000002"
down_revision: Union[str, None] = "20241207_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create global_settings table
    op.create_table(
        "global_settings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_global_settings_key"), "global_settings", ["key"], unique=False)
    op.create_index(
        op.f("ix_global_settings_category"), "global_settings", ["category"], unique=False
    )

    # Create project_settings table
    op.create_table(
        "project_settings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "key", name="uq_project_settings_project_key"),
    )
    op.create_index(
        op.f("ix_project_settings_project_id"), "project_settings", ["project_id"], unique=False
    )
    op.create_index(op.f("ix_project_settings_key"), "project_settings", ["key"], unique=False)

    # Insert default global settings from environment variables
    # These will be populated on first application start via the ConfigurationService
    # Here we just create placeholder entries for critical settings
    op.execute(
        """
        INSERT INTO global_settings (key, value, category, description)
        VALUES
            ('llm_model', '"openai/gpt-4o-mini"', 'model', 'Default LLM model for RAG queries'),
            ('embedding_model', '"openai/text-embedding-3-small"', 'model', 'Default embedding model for document vectorization'),
            ('rag_mode', '"traditional"', 'rag_strategy', 'RAG operation mode: traditional, long_context, or auto'),
            ('retrieval_top_k', '5', 'rag_strategy', 'Number of documents to retrieve'),
            ('retrieval_min_similarity', '0.0', 'rag_strategy', 'Minimum similarity threshold for retrieval'),
            ('use_hybrid_search', 'false', 'rag_strategy', 'Enable hybrid (vector + keyword) search'),
            ('intent_classification_enabled', 'true', 'advanced', 'Enable intent-based adaptive RAG strategies'),
            ('intent_cache_enabled', 'true', 'advanced', 'Cache intent classification results'),
            ('citation_format', '"both"', 'rag_strategy', 'Citation format: inline, structured, or both')
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_project_settings_key"), table_name="project_settings")
    op.drop_index(op.f("ix_project_settings_project_id"), table_name="project_settings")
    op.drop_table("project_settings")

    op.drop_index(op.f("ix_global_settings_category"), table_name="global_settings")
    op.drop_index(op.f("ix_global_settings_key"), table_name="global_settings")
    op.drop_table("global_settings")
