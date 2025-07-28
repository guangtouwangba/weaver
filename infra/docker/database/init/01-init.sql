-- Research Agent Database Initialization Script
-- This script sets up the initial database schema for the research agent system

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create cronjobs table
CREATE TABLE IF NOT EXISTS cronjobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    query VARCHAR(500) NOT NULL,
    schedule VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create job_runs table for tracking execution history
CREATE TABLE IF NOT EXISTS job_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cronjob_id UUID REFERENCES cronjobs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    papers_processed INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create papers table for storing paper metadata
CREATE TABLE IF NOT EXISTS papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    arxiv_id VARCHAR(50) UNIQUE,
    doi VARCHAR(100) UNIQUE,
    title TEXT NOT NULL,
    authors TEXT[],
    abstract TEXT,
    categories TEXT[],
    published_date DATE,
    vector_id VARCHAR(255), -- Reference to vector database
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create paper_embeddings table for storing embeddings
CREATE TABLE IF NOT EXISTS paper_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    embedding_model VARCHAR(100) NOT NULL,
    embedding_data BYTEA, -- Binary embedding data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_sessions table for storing chat history
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_query TEXT NOT NULL,
    agent_response TEXT,
    papers_referenced UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cronjobs_active ON cronjobs(is_active);
CREATE INDEX IF NOT EXISTS idx_job_runs_cronjob_id ON job_runs(cronjob_id);
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_runs_started_at ON job_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_published_date ON papers(published_date);
CREATE INDEX IF NOT EXISTS idx_papers_title_gin ON papers USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_papers_abstract_gin ON papers USING gin(to_tsvector('english', abstract));
CREATE INDEX IF NOT EXISTS idx_paper_embeddings_paper_id ON paper_embeddings(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_embeddings_model ON paper_embeddings(embedding_model);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_cronjobs_updated_at BEFORE UPDATE ON cronjobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_papers_updated_at BEFORE UPDATE ON papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing
INSERT INTO cronjobs (name, description, query, schedule, is_active) VALUES
('AI Research Monitor', 'Monitor latest AI research papers', 'AI machine learning', '0 */6 * * *', true),
('NLP Research Tracker', 'Track natural language processing research', 'natural language processing', '0 */12 * * *', true),
('Computer Vision Updates', 'Monitor computer vision research', 'computer vision deep learning', '0 0 */2 * *', true)
ON CONFLICT DO NOTHING;

-- Create a view for job statistics
CREATE OR REPLACE VIEW job_statistics AS
SELECT 
    c.id as cronjob_id,
    c.name as cronjob_name,
    COUNT(jr.id) as total_runs,
    COUNT(CASE WHEN jr.status = 'completed' THEN 1 END) as completed_runs,
    COUNT(CASE WHEN jr.status = 'failed' THEN 1 END) as failed_runs,
    COUNT(CASE WHEN jr.status = 'running' THEN 1 END) as running_runs,
    COALESCE(AVG(CASE WHEN jr.status = 'completed' THEN EXTRACT(EPOCH FROM (jr.completed_at - jr.started_at)) END), 0) as avg_duration_seconds,
    COALESCE(SUM(jr.papers_processed), 0) as total_papers_processed
FROM cronjobs c
LEFT JOIN job_runs jr ON c.id = jr.cronjob_id
GROUP BY c.id, c.name;

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO research_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO research_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO research_user; 