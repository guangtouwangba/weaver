"""Add file upload system tables

Revision ID: 2025081601
Revises: c1234567890a
Create Date: 2025-08-16 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025081601'
down_revision = 'c1234567890a'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types for file management (with checkfirst to avoid duplicates)
    file_status_enum = postgresql.ENUM(
        'uploading', 'available', 'processing', 'failed', 'archived', 'deleted',
        name='file_status_enum'
    )
    file_status_enum.create(op.get_bind(), checkfirst=True)
    
    access_level_enum = postgresql.ENUM(
        'private', 'public_read', 'shared', 'authenticated',
        name='access_level_enum'
    )
    access_level_enum.create(op.get_bind(), checkfirst=True)
    
    upload_status_enum = postgresql.ENUM(
        'initiated', 'in_progress', 'completed', 'failed', 'expired', 'cancelled',
        name='upload_status_enum'
    )
    upload_status_enum.create(op.get_bind(), checkfirst=True)

    # Create upload_sessions table first (no foreign key dependencies)
    op.create_table('upload_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('expected_size', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=200), nullable=False),
        sa.Column('chunk_size', sa.Integer(), nullable=True),
        sa.Column('max_chunks', sa.Integer(), nullable=True),
        sa.Column('status', upload_status_enum, nullable=False),
        sa.Column('uploaded_chunks', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('failed_chunks', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('storage_key', sa.String(length=1000), nullable=False),
        sa.Column('upload_id', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        # BaseModel columns
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create files table
    op.create_table('files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', sa.String(length=255), nullable=True),
        sa.Column('original_name', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(length=200), nullable=False),
        sa.Column('file_hash', sa.String(length=128), nullable=True),
        sa.Column('storage_bucket', sa.String(length=100), nullable=False),
        sa.Column('storage_key', sa.String(length=1000), nullable=False),
        sa.Column('storage_region', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', file_status_enum, nullable=False),
        sa.Column('access_level', access_level_enum, nullable=False),
        sa.Column('access_expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('allowed_users', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('allowed_groups', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('max_downloads', sa.Integer(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('last_accessed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('upload_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('custom_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # BaseModel columns
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['upload_session_id'], ['upload_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create access_policies table
    op.create_table('access_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_access_level', access_level_enum, nullable=False),
        sa.Column('base_expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('base_allowed_users', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('base_allowed_groups', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('base_max_downloads', sa.Integer(), nullable=True),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('applies_to_file_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('applies_to_categories', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('applies_to_content_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('applies_to_owners', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('applied_count', sa.Integer(), nullable=False),
        sa.Column('last_applied_at', sa.TIMESTAMP(timezone=True), nullable=True),
        # BaseModel columns
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create file_access_logs table
    op.create_table('file_access_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('access_granted', sa.Boolean(), nullable=False),
        sa.Column('denial_reason', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referer', sa.Text(), nullable=True),
        sa.Column('request_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('file_name_at_access', sa.String(length=500), nullable=True),
        sa.Column('file_size_at_access', sa.BigInteger(), nullable=True),
        sa.Column('access_level_at_access', access_level_enum, nullable=True),
        sa.Column('access_timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('additional_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # BaseModel columns
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create file_stats table
    op.create_table('file_stats',
        sa.Column('stat_date', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('stat_type', sa.String(length=50), nullable=False),
        sa.Column('dimension', sa.String(length=100), nullable=False),
        sa.Column('dimension_value', sa.String(length=255), nullable=False),
        sa.Column('total_files', sa.Integer(), nullable=True),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('total_downloads', sa.Integer(), nullable=True),
        sa.Column('new_files', sa.Integer(), nullable=True),
        sa.Column('deleted_files', sa.Integer(), nullable=True),
        sa.Column('files_by_status', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('files_by_access_level', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('files_by_content_type', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('avg_file_size_mb', sa.Float(), nullable=True),
        sa.Column('avg_downloads_per_file', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('stat_date', 'stat_type', 'dimension', 'dimension_value')
    )

    # Create indexes for files table
    op.create_index('idx_files_owner_id', 'files', ['owner_id'])
    op.create_index('idx_files_status', 'files', ['status'])
    op.create_index('idx_files_access_level', 'files', ['access_level'])
    op.create_index('idx_files_content_type', 'files', ['content_type'])
    op.create_index('idx_files_category', 'files', ['category'])
    op.create_index('idx_files_created_at', 'files', ['created_at'])
    op.create_index('idx_files_last_accessed_at', 'files', ['last_accessed_at'])
    op.create_index('idx_files_file_size', 'files', ['file_size'])
    op.create_index('idx_files_storage_key', 'files', ['storage_key'])
    op.create_index('idx_files_is_deleted', 'files', ['is_deleted'])
    op.create_index('idx_files_owner_status', 'files', ['owner_id', 'status'])
    op.create_index('idx_files_status_access', 'files', ['status', 'access_level'])
    
    # GIN indexes for arrays and JSONB
    op.create_index('idx_files_tags_gin', 'files', ['tags'], postgresql_using='gin')
    op.create_index('idx_files_metadata_gin', 'files', ['custom_metadata'], postgresql_using='gin')
    
    # Create indexes for upload_sessions table
    op.create_index('idx_upload_sessions_file_id', 'upload_sessions', ['file_id'])
    op.create_index('idx_upload_sessions_user_id', 'upload_sessions', ['user_id'])
    op.create_index('idx_upload_sessions_status', 'upload_sessions', ['status'])
    op.create_index('idx_upload_sessions_expires_at', 'upload_sessions', ['expires_at'])
    op.create_index('idx_upload_sessions_created_at', 'upload_sessions', ['created_at'])
    op.create_index('idx_upload_sessions_is_deleted', 'upload_sessions', ['is_deleted'])
    op.create_index('idx_upload_sessions_user_status', 'upload_sessions', ['user_id', 'status'])
    op.create_index('idx_upload_sessions_file_status', 'upload_sessions', ['file_id', 'status'])
    
    # Create indexes for access_policies table
    op.create_index('idx_access_policies_name', 'access_policies', ['name'])
    op.create_index('idx_access_policies_is_active', 'access_policies', ['is_active'])
    op.create_index('idx_access_policies_priority', 'access_policies', ['priority'])
    op.create_index('idx_access_policies_base_access_level', 'access_policies', ['base_access_level'])
    op.create_index('idx_access_policies_is_deleted', 'access_policies', ['is_deleted'])
    
    # GIN indexes for access policies
    op.create_index('idx_access_policies_file_ids_gin', 'access_policies', ['applies_to_file_ids'], postgresql_using='gin')
    op.create_index('idx_access_policies_categories_gin', 'access_policies', ['applies_to_categories'], postgresql_using='gin')
    op.create_index('idx_access_policies_content_types_gin', 'access_policies', ['applies_to_content_types'], postgresql_using='gin')
    op.create_index('idx_access_policies_conditions_gin', 'access_policies', ['conditions'], postgresql_using='gin')
    
    # Create indexes for file_access_logs table
    op.create_index('idx_file_access_logs_file_id', 'file_access_logs', ['file_id'])
    op.create_index('idx_file_access_logs_user_id', 'file_access_logs', ['user_id'])
    op.create_index('idx_file_access_logs_action', 'file_access_logs', ['action'])
    op.create_index('idx_file_access_logs_access_timestamp', 'file_access_logs', ['access_timestamp'])
    op.create_index('idx_file_access_logs_ip_address', 'file_access_logs', ['ip_address'])
    op.create_index('idx_file_access_logs_access_granted', 'file_access_logs', ['access_granted'])
    op.create_index('idx_file_access_logs_file_timestamp', 'file_access_logs', ['file_id', 'access_timestamp'])
    op.create_index('idx_file_access_logs_user_timestamp', 'file_access_logs', ['user_id', 'access_timestamp'])
    op.create_index('idx_file_access_logs_action_timestamp', 'file_access_logs', ['action', 'access_timestamp'])
    op.create_index('idx_file_access_logs_data_gin', 'file_access_logs', ['additional_data'], postgresql_using='gin')
    
    # Create indexes for file_stats table
    op.create_index('idx_file_stats_date_type', 'file_stats', ['stat_date', 'stat_type'])
    op.create_index('idx_file_stats_dimension', 'file_stats', ['dimension', 'dimension_value'])
    op.create_index('idx_file_stats_computed_at', 'file_stats', ['computed_at'])

    # Enable trigram extension for full-text search (if not already enabled)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    
    # Create trigram index for file name search
    op.create_index('idx_files_name_fts', 'files', ['original_name'], 
                   postgresql_using='gin', 
                   postgresql_ops={'original_name': 'gin_trgm_ops'})

    # Set default values for new columns
    op.execute("ALTER TABLE upload_sessions ALTER COLUMN uploaded_size SET DEFAULT 0;")
    op.execute("ALTER TABLE upload_sessions ALTER COLUMN retry_count SET DEFAULT 0;")
    op.execute("ALTER TABLE upload_sessions ALTER COLUMN status SET DEFAULT 'initiated';")
    op.execute("ALTER TABLE files ALTER COLUMN status SET DEFAULT 'uploading';")
    op.execute("ALTER TABLE files ALTER COLUMN access_level SET DEFAULT 'private';")
    op.execute("ALTER TABLE files ALTER COLUMN download_count SET DEFAULT 0;")
    op.execute("ALTER TABLE access_policies ALTER COLUMN is_active SET DEFAULT true;")
    op.execute("ALTER TABLE access_policies ALTER COLUMN priority SET DEFAULT 0;")
    op.execute("ALTER TABLE access_policies ALTER COLUMN applied_count SET DEFAULT 0;")
    op.execute("ALTER TABLE file_access_logs ALTER COLUMN access_granted SET DEFAULT true;")


def downgrade():
    # Drop indexes first
    op.drop_index('idx_files_name_fts', table_name='files')
    op.drop_index('idx_file_stats_computed_at', table_name='file_stats')
    op.drop_index('idx_file_stats_dimension', table_name='file_stats')
    op.drop_index('idx_file_stats_date_type', table_name='file_stats')
    op.drop_index('idx_file_access_logs_data_gin', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_action_timestamp', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_user_timestamp', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_file_timestamp', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_access_granted', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_ip_address', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_access_timestamp', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_action', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_user_id', table_name='file_access_logs')
    op.drop_index('idx_file_access_logs_file_id', table_name='file_access_logs')
    op.drop_index('idx_access_policies_conditions_gin', table_name='access_policies')
    op.drop_index('idx_access_policies_content_types_gin', table_name='access_policies')
    op.drop_index('idx_access_policies_categories_gin', table_name='access_policies')
    op.drop_index('idx_access_policies_file_ids_gin', table_name='access_policies')
    op.drop_index('idx_access_policies_is_deleted', table_name='access_policies')
    op.drop_index('idx_access_policies_base_access_level', table_name='access_policies')
    op.drop_index('idx_access_policies_priority', table_name='access_policies')
    op.drop_index('idx_access_policies_is_active', table_name='access_policies')
    op.drop_index('idx_access_policies_name', table_name='access_policies')
    op.drop_index('idx_upload_sessions_file_status', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_user_status', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_is_deleted', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_created_at', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_expires_at', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_status', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_user_id', table_name='upload_sessions')
    op.drop_index('idx_upload_sessions_file_id', table_name='upload_sessions')
    op.drop_index('idx_files_metadata_gin', table_name='files')
    op.drop_index('idx_files_tags_gin', table_name='files')
    op.drop_index('idx_files_status_access', table_name='files')
    op.drop_index('idx_files_owner_status', table_name='files')
    op.drop_index('idx_files_is_deleted', table_name='files')
    op.drop_index('idx_files_storage_key', table_name='files')
    op.drop_index('idx_files_file_size', table_name='files')
    op.drop_index('idx_files_last_accessed_at', table_name='files')
    op.drop_index('idx_files_created_at', table_name='files')
    op.drop_index('idx_files_category', table_name='files')
    op.drop_index('idx_files_content_type', table_name='files')
    op.drop_index('idx_files_access_level', table_name='files')
    op.drop_index('idx_files_status', table_name='files')
    op.drop_index('idx_files_owner_id', table_name='files')
    
    # Drop tables
    op.drop_table('file_stats')
    op.drop_table('file_access_logs')
    op.drop_table('access_policies')
    op.drop_table('files')
    op.drop_table('upload_sessions')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS upload_status_enum;")
    op.execute("DROP TYPE IF EXISTS access_level_enum;")
    op.execute("DROP TYPE IF EXISTS file_status_enum;")