-- =============================================================================
-- 完整数据库设置脚本
-- 包含：所有表创建 + pgvector 扩展 + embedding 字段
-- =============================================================================

-- 1. 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 创建 topics 表
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    goal_type VARCHAR(50) NOT NULL,
    progress_status VARCHAR(50) NOT NULL DEFAULT 'NOT_STARTED',
    progress_percentage INTEGER DEFAULT 0,
    tags TEXT[],
    total_contents INTEGER DEFAULT 0,
    completed_contents INTEGER DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_topics_goal_type ON topics(goal_type);
CREATE INDEX IF NOT EXISTS ix_topics_progress_status ON topics(progress_status);
CREATE INDEX IF NOT EXISTS ix_topics_created_at ON topics(created_at);

-- 3. 创建 topic_contents 表
CREATE TABLE IF NOT EXISTS topic_contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    document_id UUID,
    title VARCHAR(200) NOT NULL,
    content_source VARCHAR(50) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    file_type VARCHAR(50),
    content_status VARCHAR(50) NOT NULL DEFAULT 'UPLOADED',
    processing_status VARCHAR(50) NOT NULL DEFAULT 'NOT_STARTED',
    processing_error TEXT,
    notes TEXT,
    uploaded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_topic_contents_topic_id ON topic_contents(topic_id);
CREATE INDEX IF NOT EXISTS ix_topic_contents_document_id ON topic_contents(document_id);
CREATE INDEX IF NOT EXISTS ix_topic_contents_content_status ON topic_contents(content_status);

-- 4. 创建 conversations 表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    title VARCHAR(200),
    message_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_conversations_topic_id ON conversations(topic_id, updated_at);
CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations(created_at);

-- 5. 创建 messages 表（带 embedding 字段）
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources TEXT[],
    embedding vector(1536),  -- pgvector embedding 字段
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS ix_messages_role ON messages(role, created_at);

-- 6. 创建向量索引（用于快速相似度搜索）
CREATE INDEX IF NOT EXISTS idx_messages_embedding 
ON messages USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 7. 创建触发器函数：更新对话统计
CREATE OR REPLACE FUNCTION update_conversation_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新消息计数和最后消息时间
    UPDATE conversations
    SET message_count = message_count + 1,
        last_message_at = NEW.created_at,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. 创建触发器
DROP TRIGGER IF EXISTS trigger_update_conversation_stats ON messages;
CREATE TRIGGER trigger_update_conversation_stats
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_stats();

-- 9. 创建 alembic_version 表（如果使用 Alembic）
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- 10. 验证安装
SELECT 'pgvector 扩展' as 项目, 
       CASE WHEN EXISTS (
           SELECT 1 FROM pg_extension WHERE extname = 'vector'
       ) THEN '✅ 已安装' ELSE '❌ 未安装' END as 状态;

SELECT 'topics 表' as 项目,
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.tables 
           WHERE table_name = 'topics'
       ) THEN '✅ 已创建' ELSE '❌ 未创建' END as 状态;

SELECT 'conversations 表' as 项目,
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.tables 
           WHERE table_name = 'conversations'
       ) THEN '✅ 已创建' ELSE '❌ 未创建' END as 状态;

SELECT 'messages 表' as 项目,
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.tables 
           WHERE table_name = 'messages'
       ) THEN '✅ 已创建' ELSE '❌ 未创建' END as 状态;

SELECT 'embedding 字段' as 项目,
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'messages' AND column_name = 'embedding'
       ) THEN '✅ 已创建' ELSE '❌ 未创建' END as 状态;

SELECT 'embedding 索引' as 项目,
       CASE WHEN EXISTS (
           SELECT 1 FROM pg_indexes 
           WHERE tablename = 'messages' AND indexname = 'idx_messages_embedding'
       ) THEN '✅ 已创建' ELSE '❌ 未创建' END as 状态;

-- 完成
SELECT '🎉 数据库设置完成！' as 消息;

