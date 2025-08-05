-- Cloud Job System Database Schema
-- Simplified schema for cloud-native job execution

-- Drop existing tables if they exist (for migration)
-- DROP TABLE IF EXISTS cloud_job_executions;
-- DROP TABLE IF EXISTS cloud_jobs;

-- Create cloud_jobs table
CREATE TABLE IF NOT EXISTS cloud_jobs (
    job_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    config TEXT NOT NULL DEFAULT '{}',  -- JSON config as TEXT for SQLite compatibility
    status TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'locked', 'success', 'failed', 'disabled')),
    description TEXT DEFAULT '',
    max_retries INTEGER DEFAULT 3,
    current_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_execution TIMESTAMP NULL,
    
    -- Lock mechanism fields
    locked_at TIMESTAMP NULL,
    locked_by TEXT NULL,                -- Instance ID that locked the job
    lock_expires_at TIMESTAMP NULL
);

-- Create cloud_job_executions table
CREATE TABLE IF NOT EXISTS cloud_job_executions (
    execution_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,
    duration_seconds REAL NULL,
    result TEXT NULL DEFAULT '{}',      -- JSON result as TEXT
    error_message TEXT NULL,
    instance_id TEXT NULL,             -- Instance that executed the job
    FOREIGN KEY (job_id) REFERENCES cloud_jobs (job_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_status ON cloud_jobs(status);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_status_retries ON cloud_jobs(status, current_retries, max_retries);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_lock_expires ON cloud_jobs(lock_expires_at);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_type ON cloud_jobs(job_type);

CREATE INDEX IF NOT EXISTS idx_cloud_job_executions_job_id ON cloud_job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_cloud_job_executions_status ON cloud_job_executions(status);
CREATE INDEX IF NOT EXISTS idx_cloud_job_executions_started_at ON cloud_job_executions(started_at);

-- Create a view for available jobs (waiting or failed but retriable)
CREATE VIEW IF NOT EXISTS available_jobs AS
SELECT * FROM cloud_jobs 
WHERE (status = 'waiting' OR (status = 'failed' AND current_retries < max_retries))
  AND (lock_expires_at IS NULL OR lock_expires_at < datetime('now'))
ORDER BY 
    CASE 
        WHEN status = 'waiting' THEN 0 
        WHEN status = 'failed' THEN 1 
        ELSE 2 
    END,
    created_at ASC;

-- Create a view for job statistics
CREATE VIEW IF NOT EXISTS job_statistics AS
SELECT 
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'waiting' THEN 1 ELSE 0 END) as waiting_jobs,
    SUM(CASE WHEN status = 'locked' THEN 1 ELSE 0 END) as locked_jobs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_jobs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
    SUM(CASE WHEN status = 'disabled' THEN 1 ELSE 0 END) as disabled_jobs
FROM cloud_jobs;