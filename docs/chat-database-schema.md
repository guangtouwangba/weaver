# Chat系统数据库设计

## 📋 概述

Chat系统的数据库设计基于现有的RAG系统架构，新增了5个核心表来支持聊天功能：

- `chat_sessions`: 聊天会话管理
- `chat_messages`: 聊天消息存储
- `chat_contexts`: 对话上下文管理
- `chat_references`: 文档引用管理
- `chat_streams`: 流式响应记录

## 🗄️ 数据表设计

### 1. 聊天会话表 (chat_sessions)

```sql
-- 聊天会话表
CREATE TABLE chat_sessions (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- 关联信息
    user_id BIGINT,  -- 关联用户ID (可选)
    topic_id BIGINT REFERENCES topics(id) ON DELETE SET NULL,  -- 关联主题
    
    -- 会话信息
    title VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    
    -- 配置信息
    model_config JSONB DEFAULT '{
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": true
    }',
    context_settings JSONB DEFAULT '{
        "max_context_length": 8000,
        "include_document_metadata": true,
        "context_window_strategy": "sliding",
        "relevance_threshold": 0.7
    }',
    
    -- 统计信息
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_topic_id ON chat_sessions(topic_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_activity ON chat_sessions(user_id, last_activity_at DESC);
CREATE INDEX idx_chat_sessions_created ON chat_sessions(created_at DESC);

-- 触发器：更新 updated_at
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 2. 聊天消息表 (chat_messages)

```sql
-- 聊天消息表
CREATE TABLE chat_messages (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- 关联信息
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    parent_message_id VARCHAR(255) REFERENCES chat_messages(message_id) ON DELETE SET NULL,
    
    -- 消息内容
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text' CHECK (content_type IN ('text', 'markdown', 'html', 'json')),
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    tokens INTEGER DEFAULT 0,
    
    -- LLM相关
    model VARCHAR(100),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    
    -- 状态信息
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'streaming', 'completed', 'failed')),
    error_message TEXT,
    
    -- 性能指标
    processing_time_ms INTEGER,
    retrieval_time_ms INTEGER,
    generation_time_ms INTEGER,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_parent_id ON chat_messages(parent_message_id);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);
CREATE INDEX idx_chat_messages_status ON chat_messages(status);
CREATE INDEX idx_chat_messages_session_created ON chat_messages(session_id, created_at DESC);
CREATE INDEX idx_chat_messages_content_gin ON chat_messages USING GIN(to_tsvector('english', content));

-- 触发器
CREATE TRIGGER update_chat_messages_updated_at
    BEFORE UPDATE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 触发器：更新会话统计
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE chat_sessions 
        SET 
            message_count = message_count + 1,
            total_tokens = total_tokens + COALESCE(NEW.tokens, 0),
            last_activity_at = NOW()
        WHERE session_id = NEW.session_id;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE chat_sessions 
        SET 
            total_tokens = total_tokens - COALESCE(OLD.tokens, 0) + COALESCE(NEW.tokens, 0),
            last_activity_at = NOW()
        WHERE session_id = NEW.session_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE chat_sessions 
        SET 
            message_count = message_count - 1,
            total_tokens = total_tokens - COALESCE(OLD.tokens, 0),
            last_activity_at = NOW()
        WHERE session_id = OLD.session_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_stats_trigger
    AFTER INSERT OR UPDATE OR DELETE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_stats();
```

### 3. 对话上下文表 (chat_contexts)

```sql
-- 对话上下文表
CREATE TABLE chat_contexts (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    context_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- 关联信息
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_id VARCHAR(255) REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    
    -- 上下文信息
    context_type VARCHAR(50) NOT NULL CHECK (context_type IN ('retrieval', 'conversation', 'system', 'tool')),
    context_data JSONB NOT NULL,
    relevance_score DECIMAL(5,4) DEFAULT 0.0000,
    
    -- 排序和权重
    context_order INTEGER DEFAULT 0,
    weight DECIMAL(3,2) DEFAULT 1.00,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX idx_chat_contexts_session_id ON chat_contexts(session_id);
CREATE INDEX idx_chat_contexts_message_id ON chat_contexts(message_id);
CREATE INDEX idx_chat_contexts_type ON chat_contexts(context_type);
CREATE INDEX idx_chat_contexts_relevance ON chat_contexts(session_id, relevance_score DESC);
CREATE INDEX idx_chat_contexts_order ON chat_contexts(session_id, context_order);
CREATE INDEX idx_chat_contexts_expires ON chat_contexts(expires_at) WHERE expires_at IS NOT NULL;

-- 清理过期上下文的函数
CREATE OR REPLACE FUNCTION cleanup_expired_contexts()
RETURNS void AS $$
BEGIN
    DELETE FROM chat_contexts 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 定期清理任务 (需要在应用层调度)
-- SELECT cleanup_expired_contexts();
```

### 4. 文档引用表 (chat_references)

```sql
-- 文档引用表
CREATE TABLE chat_references (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    reference_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- 关联信息
    message_id VARCHAR(255) NOT NULL REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    document_id VARCHAR(255) REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id VARCHAR(255) REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    -- 引用信息
    reference_type VARCHAR(50) NOT NULL CHECK (reference_type IN ('direct', 'context', 'related', 'citation')),
    relevance_score DECIMAL(5,4) NOT NULL,
    excerpt TEXT,
    
    -- 位置信息
    start_char INTEGER,
    end_char INTEGER,
    page_number INTEGER,
    
    -- 显示顺序
    display_order INTEGER DEFAULT 0,
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_chat_references_message_id ON chat_references(message_id);
CREATE INDEX idx_chat_references_document_id ON chat_references(document_id);
CREATE INDEX idx_chat_references_chunk_id ON chat_references(chunk_id);
CREATE INDEX idx_chat_references_relevance ON chat_references(message_id, relevance_score DESC);
CREATE INDEX idx_chat_references_type ON chat_references(reference_type);
CREATE INDEX idx_chat_references_display_order ON chat_references(message_id, display_order);
```

### 5. 流式响应表 (chat_streams)

```sql
-- 流式响应表 (可选，用于调试和分析)
CREATE TABLE chat_streams (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    
    -- 关联信息
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    message_id VARCHAR(255) REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    
    -- 流式信息
    chunk_index INTEGER NOT NULL,
    chunk_content TEXT,
    chunk_type VARCHAR(50) DEFAULT 'text' CHECK (chunk_type IN ('text', 'reference', 'metadata', 'error')),
    
    -- 状态信息
    is_final BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_chat_streams_stream_id ON chat_streams(stream_id);
CREATE INDEX idx_chat_streams_message_id ON chat_streams(message_id);
CREATE INDEX idx_chat_streams_chunk_order ON chat_streams(stream_id, chunk_index);

-- 分区策略 (按月分区，便于数据清理)
CREATE TABLE chat_streams_2024_01 PARTITION OF chat_streams
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE chat_streams_2024_02 PARTITION OF chat_streams
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 自动创建下个月分区的函数
CREATE OR REPLACE FUNCTION create_next_month_partition()
RETURNS void AS $$
DECLARE
    next_month DATE;
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    next_month := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
    partition_name := 'chat_streams_' || TO_CHAR(next_month, 'YYYY_MM');
    start_date := TO_CHAR(next_month, 'YYYY-MM-DD');
    end_date := TO_CHAR(next_month + INTERVAL '1 month', 'YYYY-MM-DD');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF chat_streams FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

## 🔄 数据库迁移脚本

### Alembic迁移文件

```python
# alembic/versions/xxx_add_chat_system.py

"""Add chat system tables

Revision ID: xxx_add_chat_system
Revises: xxx_previous_revision
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'xxx_add_chat_system'
down_revision = 'xxx_previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=True),
        sa.Column('topic_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('model_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # Create indexes for chat_sessions
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_topic_id', 'chat_sessions', ['topic_id'])
    op.create_index('idx_chat_sessions_status', 'chat_sessions', ['status'])
    op.create_index('idx_chat_sessions_activity', 'chat_sessions', ['user_id', 'last_activity_at'])
    op.create_index('idx_chat_sessions_created', 'chat_sessions', ['created_at'])
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('parent_message_id', sa.String(255), nullable=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens', sa.Integer(), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('retrieval_time_ms', sa.Integer(), nullable=True),
        sa.Column('generation_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_message_id'], ['chat_messages.message_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    
    # Create indexes for chat_messages
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_parent_id', 'chat_messages', ['parent_message_id'])
    op.create_index('idx_chat_messages_role', 'chat_messages', ['role'])
    op.create_index('idx_chat_messages_status', 'chat_messages', ['status'])
    op.create_index('idx_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'])
    
    # Create GIN index for full-text search
    op.execute("CREATE INDEX idx_chat_messages_content_gin ON chat_messages USING GIN(to_tsvector('english', content))")
    
    # Create chat_contexts table
    op.create_table('chat_contexts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('context_id', sa.String(255), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('message_id', sa.String(255), nullable=True),
        sa.Column('context_type', sa.String(50), nullable=False),
        sa.Column('context_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('relevance_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('context_order', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Numeric(3, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.message_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('context_id')
    )
    
    # Create indexes for chat_contexts
    op.create_index('idx_chat_contexts_session_id', 'chat_contexts', ['session_id'])
    op.create_index('idx_chat_contexts_message_id', 'chat_contexts', ['message_id'])
    op.create_index('idx_chat_contexts_type', 'chat_contexts', ['context_type'])
    op.create_index('idx_chat_contexts_relevance', 'chat_contexts', ['session_id', 'relevance_score'])
    op.create_index('idx_chat_contexts_order', 'chat_contexts', ['session_id', 'context_order'])
    op.create_index('idx_chat_contexts_expires', 'chat_contexts', ['expires_at'])
    
    # Create chat_references table
    op.create_table('chat_references',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reference_id', sa.String(255), nullable=False),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('document_id', sa.String(255), nullable=True),
        sa.Column('chunk_id', sa.String(255), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=False),
        sa.Column('relevance_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=True),
        sa.Column('end_char', sa.Integer(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.message_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_id')
    )
    
    # Create indexes for chat_references
    op.create_index('idx_chat_references_message_id', 'chat_references', ['message_id'])
    op.create_index('idx_chat_references_document_id', 'chat_references', ['document_id'])
    op.create_index('idx_chat_references_chunk_id', 'chat_references', ['chunk_id'])
    op.create_index('idx_chat_references_relevance', 'chat_references', ['message_id', 'relevance_score'])
    op.create_index('idx_chat_references_type', 'chat_references', ['reference_type'])
    op.create_index('idx_chat_references_display_order', 'chat_references', ['message_id', 'display_order'])
    
    # Create chat_streams table (partitioned)
    op.execute("""
        CREATE TABLE chat_streams (
            id BIGSERIAL,
            stream_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            message_id VARCHAR(255),
            chunk_index INTEGER NOT NULL,
            chunk_content TEXT,
            chunk_type VARCHAR(50) DEFAULT 'text',
            is_final BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (message_id) REFERENCES chat_messages(message_id) ON DELETE CASCADE
        ) PARTITION BY RANGE (created_at)
    """)
    
    # Create initial partitions
    op.execute("""
        CREATE TABLE chat_streams_2024_01 PARTITION OF chat_streams
        FOR VALUES FROM ('2024-01-01') TO ('2024-02-01')
    """)
    
    op.execute("""
        CREATE TABLE chat_streams_2024_02 PARTITION OF chat_streams
        FOR VALUES FROM ('2024-02-01') TO ('2024-03-01')
    """)
    
    # Create indexes for chat_streams
    op.create_index('idx_chat_streams_stream_id', 'chat_streams', ['stream_id'])
    op.create_index('idx_chat_streams_message_id', 'chat_streams', ['message_id'])
    op.create_index('idx_chat_streams_chunk_order', 'chat_streams', ['stream_id', 'chunk_index'])
    
    # Create triggers and functions
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER update_chat_sessions_updated_at
            BEFORE UPDATE ON chat_sessions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_chat_messages_updated_at
            BEFORE UPDATE ON chat_messages
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create session stats update function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_session_stats()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE chat_sessions 
                SET 
                    message_count = message_count + 1,
                    total_tokens = total_tokens + COALESCE(NEW.tokens, 0),
                    last_activity_at = NOW()
                WHERE session_id = NEW.session_id;
            ELSIF TG_OP = 'UPDATE' THEN
                UPDATE chat_sessions 
                SET 
                    total_tokens = total_tokens - COALESCE(OLD.tokens, 0) + COALESCE(NEW.tokens, 0),
                    last_activity_at = NOW()
                WHERE session_id = NEW.session_id;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE chat_sessions 
                SET 
                    message_count = message_count - 1,
                    total_tokens = total_tokens - COALESCE(OLD.tokens, 0),
                    last_activity_at = NOW()
                WHERE session_id = OLD.session_id;
            END IF;
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER update_session_stats_trigger
            AFTER INSERT OR UPDATE OR DELETE ON chat_messages
            FOR EACH ROW
            EXECUTE FUNCTION update_session_stats();
    """)

def downgrade():
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_session_stats_trigger ON chat_messages")
    op.execute("DROP TRIGGER IF EXISTS update_chat_messages_updated_at ON chat_messages")
    op.execute("DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_session_stats()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables
    op.drop_table('chat_streams')
    op.drop_table('chat_streams_2024_01')
    op.drop_table('chat_streams_2024_02')
    op.drop_table('chat_references')
    op.drop_table('chat_contexts')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
```

## 📊 性能优化建议

### 1. 分区策略

```sql
-- 按时间分区消息表 (大量数据时使用)
ALTER TABLE chat_messages PARTITION BY RANGE (created_at);

CREATE TABLE chat_messages_2024_q1 PARTITION OF chat_messages
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE chat_messages_2024_q2 PARTITION OF chat_messages
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

### 2. 定期清理策略

```sql
-- 清理旧的流式记录 (保留30天)
DELETE FROM chat_streams 
WHERE created_at < NOW() - INTERVAL '30 days';

-- 清理过期的上下文
DELETE FROM chat_contexts 
WHERE expires_at IS NOT NULL AND expires_at < NOW();

-- 清理删除状态的会话数据 (保留7天)
DELETE FROM chat_sessions 
WHERE status = 'deleted' AND updated_at < NOW() - INTERVAL '7 days';
```

### 3. 查询优化

```sql
-- 常用查询的性能优化
-- 1. 获取用户最近的会话
SELECT s.*, COUNT(m.id) as message_count
FROM chat_sessions s
LEFT JOIN chat_messages m ON s.session_id = m.session_id
WHERE s.user_id = $1 AND s.status = 'active'
GROUP BY s.id
ORDER BY s.last_activity_at DESC
LIMIT 20;

-- 2. 获取会话的最新消息
SELECT * FROM chat_messages 
WHERE session_id = $1 
ORDER BY created_at DESC 
LIMIT 50;

-- 3. 搜索消息内容
SELECT m.*, s.title
FROM chat_messages m
JOIN chat_sessions s ON m.session_id = s.session_id
WHERE s.user_id = $1 
  AND to_tsvector('english', m.content) @@ plainto_tsquery('english', $2)
ORDER BY m.created_at DESC;
```

## 🔧 维护脚本

### 数据库维护函数

```sql
-- 会话统计重建函数
CREATE OR REPLACE FUNCTION rebuild_session_stats()
RETURNS void AS $$
BEGIN
    UPDATE chat_sessions SET
        message_count = (
            SELECT COUNT(*) 
            FROM chat_messages 
            WHERE chat_messages.session_id = chat_sessions.session_id
        ),
        total_tokens = (
            SELECT COALESCE(SUM(tokens), 0)
            FROM chat_messages 
            WHERE chat_messages.session_id = chat_sessions.session_id
        ),
        last_activity_at = (
            SELECT MAX(created_at)
            FROM chat_messages 
            WHERE chat_messages.session_id = chat_sessions.session_id
        );
END;
$$ LANGUAGE plpgsql;

-- 数据一致性检查函数
CREATE OR REPLACE FUNCTION check_chat_data_consistency()
RETURNS TABLE(issue_type TEXT, issue_count BIGINT) AS $$
BEGIN
    -- 检查孤立的消息
    RETURN QUERY
    SELECT 'orphaned_messages'::TEXT, COUNT(*)
    FROM chat_messages m
    LEFT JOIN chat_sessions s ON m.session_id = s.session_id
    WHERE s.session_id IS NULL;
    
    -- 检查孤立的上下文
    RETURN QUERY
    SELECT 'orphaned_contexts'::TEXT, COUNT(*)
    FROM chat_contexts c
    LEFT JOIN chat_sessions s ON c.session_id = s.session_id
    WHERE s.session_id IS NULL;
    
    -- 检查孤立的引用
    RETURN QUERY
    SELECT 'orphaned_references'::TEXT, COUNT(*)
    FROM chat_references r
    LEFT JOIN chat_messages m ON r.message_id = m.message_id
    WHERE m.message_id IS NULL;
END;
$$ LANGUAGE plpgsql;
```

这个数据库设计文档提供了Chat系统完整的数据库架构，包括表结构、索引、触发器、迁移脚本和维护工具，确保系统的高性能和数据一致性。




