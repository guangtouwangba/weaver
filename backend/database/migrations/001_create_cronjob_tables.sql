-- Migration 001: Create cronjob system tables
-- This migration creates the necessary tables for the cronjob system with vector DB and embedding support

-- Create cronjobs table
CREATE TABLE IF NOT EXISTS cronjobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    keywords TEXT[] NOT NULL,
    cron_expression VARCHAR(100),
    interval_hours INTEGER,
    enabled BOOLEAN DEFAULT true,
    max_papers_per_run INTEGER DEFAULT 50,
    embedding_provider VARCHAR(50) DEFAULT 'openai',
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    vector_db_provider VARCHAR(50) DEFAULT 'chroma',
    vector_db_config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for cronjobs table
CREATE INDEX IF NOT EXISTS idx_cronjobs_enabled ON cronjobs(enabled);
CREATE INDEX IF NOT EXISTS idx_cronjobs_provider ON cronjobs(embedding_provider, vector_db_provider);

-- Create job_runs table
CREATE TABLE IF NOT EXISTS job_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES cronjobs(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    papers_found INTEGER DEFAULT 0,
    papers_processed INTEGER DEFAULT 0,
    papers_skipped INTEGER DEFAULT 0,
    papers_embedded INTEGER DEFAULT 0,
    embedding_errors INTEGER DEFAULT 0,
    vector_db_errors INTEGER DEFAULT 0,
    error_message TEXT,
    execution_log JSONB
);

-- Create indexes for job_runs table
CREATE INDEX IF NOT EXISTS idx_job_runs_job_id ON job_runs(job_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_runs_started_at ON job_runs(started_at);

-- Create enhanced papers table (or alter existing one)
CREATE TABLE IF NOT EXISTS papers (
    id VARCHAR(255) PRIMARY KEY,
    arxiv_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT,
    summary TEXT,
    categories TEXT[] NOT NULL,
    published TIMESTAMP NOT NULL,
    pdf_url VARCHAR(500),
    entry_id VARCHAR(500),
    doi VARCHAR(255),
    embedding_provider VARCHAR(50),
    embedding_model VARCHAR(100),
    vector_id VARCHAR(255),
    embedding_status VARCHAR(20) DEFAULT 'pending',
    embedding_error TEXT,
    last_embedded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create constraints and indexes for papers table
ALTER TABLE papers ADD CONSTRAINT IF NOT EXISTS unique_arxiv_id UNIQUE (arxiv_id);
ALTER TABLE papers ADD CONSTRAINT IF NOT EXISTS unique_doi UNIQUE (doi) WHERE doi IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_papers_embedding_status ON papers(embedding_status);
CREATE INDEX IF NOT EXISTS idx_papers_embedding_provider ON papers(embedding_provider);
CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published);
CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers USING GIN(categories);

-- Create vector_db_configs table
CREATE TABLE IF NOT EXISTS vector_db_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for vector_db_configs table
CREATE INDEX IF NOT EXISTS idx_vector_db_configs_provider ON vector_db_configs(provider);
CREATE INDEX IF NOT EXISTS idx_vector_db_configs_default ON vector_db_configs(is_default);

-- Create embedding_configs table
CREATE TABLE IF NOT EXISTS embedding_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    config JSONB,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for embedding_configs table
CREATE INDEX IF NOT EXISTS idx_embedding_configs_provider ON embedding_configs(provider);
CREATE INDEX IF NOT EXISTS idx_embedding_configs_default ON embedding_configs(is_default);

-- Insert default configurations
INSERT INTO vector_db_configs (name, provider, config, is_default) VALUES 
('Default ChromaDB', 'chroma', '{"db_path": "./data/vector_db", "collection_name": "research-papers"}', true)
ON CONFLICT DO NOTHING;

INSERT INTO embedding_configs (name, provider, model_name, config, is_default) VALUES 
('Default HuggingFace', 'huggingface', 'all-MiniLM-L6-v2', '{"batch_size": 32}', true)
ON CONFLICT DO NOTHING;