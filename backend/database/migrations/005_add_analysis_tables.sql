-- Migration 005: Add analysis session tables
-- Created: 2024-08-02
-- Description: Add tables for tracking research analysis sessions and progress

-- Create analysis_sessions table
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(255),
    max_papers INTEGER DEFAULT 20,
    similarity_threshold VARCHAR(10) DEFAULT '0.5',
    enable_arxiv_fallback BOOLEAN DEFAULT TRUE,
    selected_agents TEXT[],
    papers_found INTEGER DEFAULT 0,
    papers_data JSONB,
    agent_insights JSONB,
    final_results JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    client_ip VARCHAR(45),
    user_agent TEXT
);

-- Create analysis_progress table
CREATE TABLE IF NOT EXISTS analysis_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    progress_percentage INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    current_papers JSONB,
    agent_insights JSONB,
    step_duration_ms INTEGER
);

-- Create indexes for analysis_sessions
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_status ON analysis_sessions(status);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_started_at ON analysis_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_client_ip ON analysis_sessions(client_ip);

-- Create indexes for analysis_progress
CREATE INDEX IF NOT EXISTS idx_analysis_progress_session_id ON analysis_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_progress_timestamp ON analysis_progress(timestamp);
CREATE INDEX IF NOT EXISTS idx_analysis_progress_step ON analysis_progress(step_name);

-- Add comments for documentation
COMMENT ON TABLE analysis_sessions IS 'Tracks research analysis sessions initiated by users';
COMMENT ON TABLE analysis_progress IS 'Records progress history for each analysis session';

COMMENT ON COLUMN analysis_sessions.query IS 'User research query/question';
COMMENT ON COLUMN analysis_sessions.status IS 'Current status: started, in_progress, completed, failed';
COMMENT ON COLUMN analysis_sessions.progress IS 'Progress percentage (0-100)';
COMMENT ON COLUMN analysis_sessions.current_step IS 'Current analysis step being executed';
COMMENT ON COLUMN analysis_sessions.selected_agents IS 'Array of selected AI agents for analysis';
COMMENT ON COLUMN analysis_sessions.papers_data IS 'JSON array of found papers metadata';
COMMENT ON COLUMN analysis_sessions.agent_insights IS 'JSON object of agent analysis results';
COMMENT ON COLUMN analysis_sessions.final_results IS 'JSON object of final analysis results';

COMMENT ON COLUMN analysis_progress.step_name IS 'Name of the analysis step';
COMMENT ON COLUMN analysis_progress.progress_percentage IS 'Progress at this step (0-100)';
COMMENT ON COLUMN analysis_progress.status IS 'Step status: running, completed, error';
COMMENT ON COLUMN analysis_progress.current_papers IS 'Papers found/processed at this step';
COMMENT ON COLUMN analysis_progress.agent_insights IS 'Agent insights generated at this step';
COMMENT ON COLUMN analysis_progress.step_duration_ms IS 'Duration of this step in milliseconds';