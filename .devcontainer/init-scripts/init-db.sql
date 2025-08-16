-- Initialize database for RAG system
-- This script runs when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS rag;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set search path
SET search_path = rag, public;

-- Grant permissions to rag_user
GRANT ALL PRIVILEGES ON SCHEMA rag TO rag_user;
GRANT ALL PRIVILEGES ON SCHEMA monitoring TO rag_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA rag TO rag_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA rag TO rag_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO rag_user;

-- Create initial tables (basic structure)
CREATE TABLE IF NOT EXISTS rag.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS rag.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embeddings dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS rag.knowledge_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_status ON rag.documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON rag.documents(created_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON rag.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON rag.documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_sessions_updated_at
    BEFORE UPDATE ON rag.knowledge_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();