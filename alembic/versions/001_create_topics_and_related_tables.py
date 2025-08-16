"""Create topics and related tables

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom types first
    resource_type_enum = postgresql.ENUM(
        'pdf', 'doc', 'docx', 'image', 'video', 'audio', 'text', 'url',
        name='resource_type_enum',
        create_type=False
    )
    resource_type_enum.create(op.get_bind(), checkfirst=True)
    
    parse_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed',
        name='parse_status_enum',
        create_type=False
    )
    parse_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create topics table
    op.create_table(
        'topics',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('name', sa.VARCHAR(255), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=True),
        sa.Column('category', sa.VARCHAR(50), nullable=True),
        
        # 学习分析字段
        sa.Column('core_concepts_discovered', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('concept_relationships', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('missing_materials_count', sa.INTEGER(), nullable=False, server_default='0'),
        
        # 关联字段
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('conversation_id', sa.VARCHAR(255), nullable=True),
        
        # 时间戳字段
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_accessed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 软删除字段
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.INTEGER(), nullable=False, autoincrement=True),
        sa.Column('name', sa.VARCHAR(50), nullable=False),
        sa.Column('category', sa.VARCHAR(30), nullable=True),
        sa.Column('description', sa.TEXT(), nullable=True),
        sa.Column('usage_count', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_tags_name')
    )
    
    # Create topic_tags junction table
    op.create_table(
        'topic_tags',
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        sa.Column('tag_id', sa.INTEGER(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_topic_tags_topic_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name='fk_topic_tags_tag_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('topic_id', 'tag_id')
    )
    
    # Create topic_resources table
    op.create_table(
        'topic_resources',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        
        # 文件信息
        sa.Column('original_name', sa.VARCHAR(255), nullable=False),
        sa.Column('file_name', sa.VARCHAR(255), nullable=False),
        sa.Column('file_path', sa.VARCHAR(500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.VARCHAR(100), nullable=True),
        
        # 资源类型
        sa.Column('resource_type', resource_type_enum, nullable=False),
        
        # 解析状态
        sa.Column('is_parsed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('parse_status', parse_status_enum, nullable=False, server_default=sa.text("'pending'")),
        sa.Column('parse_error', sa.TEXT(), nullable=True),
        
        # 内容信息
        sa.Column('total_pages', sa.INTEGER(), nullable=True),
        sa.Column('parsed_pages', sa.INTEGER(), nullable=False, server_default='0'),
        sa.Column('content_preview', sa.TEXT(), nullable=True),
        
        # 元数据
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        
        # 时间戳
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('parsed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 软删除
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_topic_resources_topic_id', ondelete='CASCADE')
    )
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.VARCHAR(255), nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=True),
        
        # 对话信息
        sa.Column('title', sa.VARCHAR(255), nullable=True),
        sa.Column('message_count', sa.INTEGER(), nullable=False, server_default='0'),
        
        # 对话数据
        sa.Column('conversation_data', postgresql.JSONB(), nullable=True),
        sa.Column('external_conversation_url', sa.TEXT(), nullable=True),
        
        # 时间戳
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_message_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # 软删除
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_conversations_topic_id', ondelete='SET NULL')
    )
    
    # Create indexes for performance
    op.create_index('idx_topics_name', 'topics', ['name'])
    op.create_index('idx_topics_category', 'topics', ['category'])
    op.create_index('idx_topics_user_id', 'topics', ['user_id'])
    op.create_index('idx_topics_conversation_id', 'topics', ['conversation_id'])
    op.create_index('idx_topics_created_at', 'topics', ['created_at'])
    op.create_index('idx_topics_is_deleted', 'topics', ['is_deleted'])
    
    op.create_index('idx_tags_category', 'tags', ['category'])
    op.create_index('idx_tags_usage_count', 'tags', ['usage_count'])
    
    op.create_index('idx_topic_resources_topic_id', 'topic_resources', ['topic_id'])
    op.create_index('idx_topic_resources_resource_type', 'topic_resources', ['resource_type'])
    op.create_index('idx_topic_resources_parse_status', 'topic_resources', ['parse_status'])
    op.create_index('idx_topic_resources_uploaded_at', 'topic_resources', ['uploaded_at'])
    op.create_index('idx_topic_resources_is_deleted', 'topic_resources', ['is_deleted'])
    
    # GIN索引用于JSONB字段快速查询 (注意：使用jsonb_ops操作符类)
    op.execute('CREATE INDEX idx_topic_resources_metadata_gin ON topic_resources USING gin (metadata jsonb_ops);')
    op.execute('CREATE INDEX idx_conversations_conversation_data_gin ON conversations USING gin (conversation_data jsonb_ops);')
    
    op.create_index('idx_conversations_topic_id', 'conversations', ['topic_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('idx_conversations_last_message_at', 'conversations', ['last_message_at'])
    op.create_index('idx_conversations_is_deleted', 'conversations', ['is_deleted'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_conversations_is_deleted', table_name='conversations')
    op.drop_index('idx_conversations_last_message_at', table_name='conversations')
    op.drop_index('idx_conversations_created_at', table_name='conversations')
    op.drop_index('idx_conversations_topic_id', table_name='conversations')
    op.execute('DROP INDEX IF EXISTS idx_conversations_conversation_data_gin;')
    op.execute('DROP INDEX IF EXISTS idx_topic_resources_metadata_gin;')
    op.drop_index('idx_topic_resources_is_deleted', table_name='topic_resources')
    op.drop_index('idx_topic_resources_uploaded_at', table_name='topic_resources')
    op.drop_index('idx_topic_resources_parse_status', table_name='topic_resources')
    op.drop_index('idx_topic_resources_resource_type', table_name='topic_resources')
    op.drop_index('idx_topic_resources_topic_id', table_name='topic_resources')
    op.drop_index('idx_tags_usage_count', table_name='tags')
    op.drop_index('idx_tags_category', table_name='tags')
    op.drop_index('idx_topics_is_deleted', table_name='topics')
    op.drop_index('idx_topics_created_at', table_name='topics')
    op.drop_index('idx_topics_conversation_id', table_name='topics')
    op.drop_index('idx_topics_user_id', table_name='topics')
    op.drop_index('idx_topics_category', table_name='topics')
    op.drop_index('idx_topics_name', table_name='topics')
    
    # Drop tables in reverse order
    op.drop_table('conversations')
    op.drop_table('topic_resources')
    op.drop_table('topic_tags')
    op.drop_table('tags')
    op.drop_table('topics')
    
    # Drop custom types
    postgresql.ENUM(name='parse_status_enum').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='resource_type_enum').drop(op.get_bind(), checkfirst=True)