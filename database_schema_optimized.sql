-- Optimized Database Schema Design  
-- Fixed all issues in the original SQL and added performance optimizations

-- ======================
-- 1. Create Enum Types (must be defined before use)
-- ======================

CREATE TYPE resource_type_enum AS ENUM (
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    'image', 'video', 'audio', 'text', 'url', 'archive'
);

CREATE TYPE parse_status_enum AS ENUM (
    'pending', 'processing', 'completed', 'failed', 'skipped'
);

CREATE TYPE topic_status_enum AS ENUM (
    'active', 'archived', 'draft', 'completed'
);

-- ======================
-- 2. Topics Table
-- ======================

CREATE TABLE topics (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    status topic_status_enum DEFAULT 'active',
    
    -- 学习分析统计
    core_concepts_discovered INTEGER DEFAULT 0 CHECK (core_concepts_discovered >= 0),
    concept_relationships INTEGER DEFAULT 0 CHECK (concept_relationships >= 0),
    missing_materials_count INTEGER DEFAULT 0 CHECK (missing_materials_count >= 0),
    
    -- 统计信息
    total_resources INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    
    -- 关联信息
    user_id BIGINT,
    conversation_id VARCHAR(255),
    parent_topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,
    
    -- 配置信息
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- ======================
-- 3. Tags Table
-- ======================

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(30),
    description TEXT,
    color VARCHAR(7), -- Color code for frontend display
    usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- ======================
-- 4. Topic-Tags Association Table
-- ======================

CREATE TABLE topic_tags (
    topic_id BIGINT REFERENCES topics(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT, -- User ID who added the tag
    PRIMARY KEY (topic_id, tag_id)
);

-- ======================
-- 5. Topic Resources Table
-- ======================

CREATE TABLE topic_resources (
    id BIGSERIAL PRIMARY KEY,
    topic_id BIGINT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    
    -- 文件基本信息
    original_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT CHECK (file_size > 0),
    mime_type VARCHAR(100),
    file_hash VARCHAR(64) UNIQUE, -- 用于去重
    
    -- 资源分类
    resource_type resource_type_enum NOT NULL,
    source_url TEXT, -- If resource imported from URL
    
    -- 解析状态
    is_parsed BOOLEAN DEFAULT FALSE,
    parse_status parse_status_enum DEFAULT 'pending',
    parse_error TEXT,
    parse_attempts INTEGER DEFAULT 0,
    
    -- 内容信息
    total_pages INTEGER,
    parsed_pages INTEGER DEFAULT 0,
    content_preview TEXT,
    content_summary TEXT,
    
    -- Metadata (using JSONB for efficient queries)
    metadata JSONB DEFAULT '{}',
    
    -- 权限和访问控制
    is_public BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private',
    
    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- 约束
    CONSTRAINT chk_parsed_pages CHECK (parsed_pages <= total_pages OR total_pages IS NULL)
);

-- ======================
-- 6. Conversations Table
-- ======================

CREATE TABLE conversations (
    id VARCHAR(255) PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,
    
    -- Conversation basic information
    title VARCHAR(255),
    description TEXT,
    message_count INTEGER DEFAULT 0 CHECK (message_count >= 0),
    
    -- Conversation data storage (supports multiple storage methods)
    conversation_data JSONB,
    external_conversation_url TEXT,
    storage_type VARCHAR(20) DEFAULT 'internal', -- internal, external, hybrid
    
    -- 对话统计
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    
    -- Tags and classification
    conversation_tags TEXT[], -- Simple tag array
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- ======================
-- 7. Performance Optimization Indexes
-- ======================

-- Topics table indexes
CREATE INDEX idx_topics_name ON topics(name) WHERE is_deleted = FALSE;
CREATE INDEX idx_topics_category ON topics(category) WHERE is_deleted = FALSE;
CREATE INDEX idx_topics_status ON topics(status) WHERE is_deleted = FALSE;
CREATE INDEX idx_topics_user_id ON topics(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_topics_conversation_id ON topics(conversation_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_topics_created_at ON topics(created_at DESC);
CREATE INDEX idx_topics_last_accessed_at ON topics(last_accessed_at DESC);
CREATE INDEX idx_topics_parent_topic_id ON topics(parent_topic_id) WHERE parent_topic_id IS NOT NULL;

-- 复合索引用于常见查询
CREATE INDEX idx_topics_user_status ON topics(user_id, status) WHERE is_deleted = FALSE;

-- Tags table indexes
CREATE INDEX idx_tags_category ON tags(category) WHERE is_deleted = FALSE;
CREATE INDEX idx_tags_usage_count ON tags(usage_count DESC);
CREATE INDEX idx_tags_name_gin ON tags USING gin(name gin_trgm_ops); -- 支持模糊搜索

-- Topic Resources表索引
CREATE INDEX idx_topic_resources_topic_id ON topic_resources(topic_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_topic_resources_resource_type ON topic_resources(resource_type);
CREATE INDEX idx_topic_resources_parse_status ON topic_resources(parse_status);
CREATE INDEX idx_topic_resources_uploaded_at ON topic_resources(uploaded_at DESC);
CREATE INDEX idx_topic_resources_file_hash ON topic_resources(file_hash) WHERE file_hash IS NOT NULL;

-- 复合索引
CREATE INDEX idx_topic_resources_topic_parse ON topic_resources(topic_id, parse_status) WHERE is_deleted = FALSE;

-- JSONB索引用于元数据查询
CREATE INDEX idx_topic_resources_metadata_gin ON topic_resources USING gin(metadata);

-- Conversations table indexes
CREATE INDEX idx_conversations_topic_id ON conversations(topic_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at DESC);
CREATE INDEX idx_conversations_storage_type ON conversations(storage_type);

-- 复合索引
CREATE INDEX idx_conversations_topic_last_message ON conversations(topic_id, last_message_at DESC) WHERE is_deleted = FALSE;

-- JSONB索引
CREATE INDEX idx_conversations_data_gin ON conversations USING gin(conversation_data);
CREATE INDEX idx_conversations_tags_gin ON conversations USING gin(conversation_tags);

-- ======================
-- 8. Trigger Functions
-- ======================

-- 更新updated_at字段的通用函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 更新last_accessed_at字段的函数
CREATE OR REPLACE FUNCTION update_last_accessed_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 标签使用统计函数
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE tags SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 主题统计更新函数
CREATE OR REPLACE FUNCTION update_topic_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE topics SET 
            total_resources = total_resources + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.topic_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE topics SET 
            total_resources = total_resources - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.topic_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Soft delete函数
CREATE OR REPLACE FUNCTION soft_delete_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.is_deleted = TRUE;
    NEW.deleted_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ======================
-- 9. Create Triggers
-- ======================

-- Updated_at triggers
CREATE TRIGGER trigger_topics_updated_at 
    BEFORE UPDATE ON topics 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_tags_updated_at 
    BEFORE UPDATE ON tags 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 标签使用统计触发器
CREATE TRIGGER trigger_tag_usage_count
    AFTER INSERT OR DELETE ON topic_tags
    FOR EACH ROW
    EXECUTE FUNCTION update_tag_usage_count();

-- Topic statistics trigger
CREATE TRIGGER trigger_topic_stats
    AFTER INSERT OR DELETE ON topic_resources
    FOR EACH ROW
    EXECUTE FUNCTION update_topic_stats();

-- ======================
-- 10. Views (for easier queries)
-- ======================

-- 活跃主题视图
CREATE VIEW active_topics AS
SELECT 
    t.*,
    COUNT(DISTINCT tr.id) as resource_count,
    COUNT(DISTINCT c.id) as conversation_count,
    ARRAY_AGG(DISTINCT tg.name) FILTER (WHERE tg.name IS NOT NULL) as tag_names
FROM topics t
LEFT JOIN topic_resources tr ON t.id = tr.topic_id AND tr.is_deleted = FALSE
LEFT JOIN conversations c ON t.id = c.topic_id AND c.is_deleted = FALSE
LEFT JOIN topic_tags tt ON t.id = tt.topic_id
LEFT JOIN tags tg ON tt.tag_id = tg.id AND tg.is_deleted = FALSE
WHERE t.is_deleted = FALSE AND t.status = 'active'
GROUP BY t.id;

-- 主题详情视图 (包含统计信息)
CREATE VIEW topic_details AS
SELECT 
    t.*,
    COUNT(DISTINCT tr.id) as actual_resource_count,
    COUNT(DISTINCT c.id) as actual_conversation_count,
    COUNT(DISTINCT tr.id) FILTER (WHERE tr.parse_status = 'completed') as parsed_resources,
    AVG(tr.file_size) as avg_file_size,
    MAX(tr.uploaded_at) as last_resource_upload,
    MAX(c.last_message_at) as last_conversation_activity
FROM topics t
LEFT JOIN topic_resources tr ON t.id = tr.topic_id AND tr.is_deleted = FALSE
LEFT JOIN conversations c ON t.id = c.topic_id AND c.is_deleted = FALSE
WHERE t.is_deleted = FALSE
GROUP BY t.id;

-- ======================
-- 11. Initial Data (optional)
-- ======================

-- 插入默认标签
INSERT INTO tags (name, category, description, color) VALUES
('important', 'priority', 'Mark content as important', '#FF4136'),
('in_progress', 'status', 'Projects in progress', '#FF851B'),
('completed', 'status', 'Completed projects', '#2ECC40'),
('reference', 'type', 'Reference materials', '#0074D9'),
('draft', 'status', 'Draft status', '#AAAAAA')
ON CONFLICT (name) DO NOTHING;

-- ======================
-- 12. Security Policies (Row Level Security - if needed)
-- ======================

-- 启用RLS (enable as needed)
-- ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE topic_resources ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- 创建策略示例 (limit access based on user_id)
-- CREATE POLICY topic_user_policy ON topics
--     FOR ALL
--     TO authenticated_user
--     USING (user_id = current_user_id());

-- ======================
-- 13. Comments and Documentation
-- ======================

COMMENT ON TABLE topics IS 'Topics table - stores main topics for knowledge management';
COMMENT ON TABLE tags IS 'Tags table - tag system for classifying and organizing content';
COMMENT ON TABLE topic_tags IS 'Topic-tags association table - many-to-many relationship';
COMMENT ON TABLE topic_resources IS 'Topic resources table - stores files and resources related to topics';
COMMENT ON TABLE conversations IS 'Conversations table - stores conversation records related to topics';

COMMENT ON COLUMN topics.core_concepts_discovered IS 'Number of core concepts discovered';
COMMENT ON COLUMN topics.concept_relationships IS 'Number of concept relationships';
COMMENT ON COLUMN topics.missing_materials_count IS 'Number of missing materials';
COMMENT ON COLUMN topic_resources.file_hash IS 'File hash value for deduplication';
COMMENT ON COLUMN topic_resources.metadata IS 'File metadata in JSONB format';
COMMENT ON COLUMN conversations.conversation_data IS 'Conversation data in JSONB format';