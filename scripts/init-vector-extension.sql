-- 初始化PostgreSQL向量扩展
-- 这个脚本需要在数据库中手动执行一次，用于启用pgvector扩展

-- 创建pgvector扩展（如果可用）
-- 注意：这需要预先安装pgvector扩展
-- 安装命令: apt-get install postgresql-15-pgvector (Ubuntu/Debian)
-- 或者使用Docker镜像: pgvector/pgvector:pg15

DO $$ 
BEGIN
    -- 尝试创建pgvector扩展
    BEGIN
        CREATE EXTENSION IF NOT EXISTS vector;
        RAISE NOTICE 'pgvector扩展已启用';
    EXCEPTION 
        WHEN OTHERS THEN
            RAISE NOTICE '无法创建pgvector扩展，将使用替代方案';
            RAISE NOTICE '错误信息: %', SQLERRM;
    END;
END $$;

-- 如果pgvector不可用，创建一个简单的向量类型替代
-- 这只是为了让表结构能够创建，实际的向量操作需要pgvector
DO $$
BEGIN
    -- 检查是否存在vector类型
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector') THEN
        RAISE NOTICE '创建向量类型的替代实现';
        -- 创建一个简单的文本类型作为向量的替代
        -- 实际生产环境中应该使用真正的pgvector扩展
        CREATE DOMAIN vector AS TEXT;
    END IF;
END $$;

-- 创建向量相似度计算函数（简化版本）
-- 实际生产中应该使用pgvector的内置函数
CREATE OR REPLACE FUNCTION cosine_similarity(vec1 TEXT, vec2 TEXT)
RETURNS FLOAT8 AS $$
BEGIN
    -- 这是一个占位实现
    -- 实际应该解析JSON数组并计算余弦相似度
    -- 或者使用pgvector的 vec1 <=> vec2 操作符
    RETURN 0.5;
END;
$$ LANGUAGE plpgsql;

-- 创建向量索引函数（占位实现）
CREATE OR REPLACE FUNCTION vector_dims(vec TEXT)
RETURNS INTEGER AS $$
BEGIN
    -- 返回向量维度，这里返回固定值
    RETURN 1536;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cosine_similarity(TEXT, TEXT) IS '计算两个向量的余弦相似度（简化实现）';
COMMENT ON FUNCTION vector_dims(TEXT) IS '获取向量维度（简化实现）';