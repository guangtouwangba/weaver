-- Supabase Job Scheduling System Schema
-- Run this SQL in your Supabase SQL Editor

-- Drop existing tables if they exist (optional - uncomment if needed)
-- DROP TABLE IF EXISTS job_executions;
-- DROP TABLE IF EXISTS jobs;

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    schedule_expression TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused', 'deleted')),
    description TEXT DEFAULT '',
    timeout_seconds INTEGER DEFAULT 3600,
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_execution TIMESTAMP WITH TIME ZONE NULL,
    next_execution TIMESTAMP WITH TIME ZONE NULL
);

-- Create job executions table
CREATE TABLE IF NOT EXISTS job_executions (
    execution_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled', 'timeout')),
    started_at TIMESTAMP WITH TIME ZONE NULL,
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds REAL NULL,
    result JSONB NULL DEFAULT '{}'::jsonb,
    error_message TEXT NULL,
    retry_attempt INTEGER DEFAULT 0,
    logs TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_next_execution ON jobs(next_execution);
CREATE INDEX IF NOT EXISTS idx_jobs_status_next_execution ON jobs(status, next_execution);
CREATE INDEX IF NOT EXISTS idx_jobs_config_gin ON jobs USING gin(config);

CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
CREATE INDEX IF NOT EXISTS idx_job_executions_created_at ON job_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_status ON job_executions(job_id, status);
CREATE INDEX IF NOT EXISTS idx_job_executions_result_gin ON job_executions USING gin(result);

-- Enable Row Level Security
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_executions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for anonymous access
-- Note: Adjust these policies according to your security requirements

-- Jobs table policies
CREATE POLICY IF NOT EXISTS "Allow anonymous read access on jobs" ON jobs
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY IF NOT EXISTS "Allow anonymous write access on jobs" ON jobs
    FOR ALL TO anon, authenticated
    USING (true)
    WITH CHECK (true);

-- Job executions table policies  
CREATE POLICY IF NOT EXISTS "Allow anonymous read access on job_executions" ON job_executions
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY IF NOT EXISTS "Allow anonymous write access on job_executions" ON job_executions
    FOR ALL TO anon, authenticated
    USING (true)
    WITH CHECK (true);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER IF NOT EXISTS update_jobs_updated_at 
    BEFORE UPDATE ON jobs
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample jobs for testing (optional)
INSERT INTO jobs (job_id, name, job_type, schedule_expression, config, description) VALUES 
('sample-paper-fetch', 'Daily Paper Fetch', 'paper_fetch', '0 9 * * *', '{"max_papers": 100, "keywords": ["AI", "ML"]}', 'Fetch new papers daily at 9 AM'),
('sample-maintenance', 'Weekly Cleanup', 'maintenance', '0 2 * * 0', '{"cleanup_days": 30}', 'Weekly cleanup of old data')
ON CONFLICT (job_id) DO NOTHING;