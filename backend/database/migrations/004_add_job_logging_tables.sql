-- Migration: Add job logging and status tracking tables
-- Date: 2025-07-31
-- Description: Add comprehensive logging and status tracking for job runs

-- Create job_logs table
CREATE TABLE IF NOT EXISTS job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_run_id UUID NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    level VARCHAR(10) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    logger_name VARCHAR(255),
    message TEXT NOT NULL,
    details JSONB,
    step VARCHAR(255),
    paper_id VARCHAR(255),
    error_code VARCHAR(50),
    duration_ms INTEGER
);

-- Create job_status_history table
CREATE TABLE IF NOT EXISTS job_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_run_id UUID NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    reason TEXT,
    details JSONB
);

-- Create job_metrics table
CREATE TABLE IF NOT EXISTS job_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_run_id UUID NOT NULL REFERENCES job_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value INTEGER NOT NULL,
    metric_type VARCHAR(20) DEFAULT 'counter' CHECK (metric_type IN ('counter', 'gauge', 'histogram')),
    labels JSONB
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_job_logs_job_run_id ON job_logs(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_logs_timestamp ON job_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_job_logs_level ON job_logs(level);
CREATE INDEX IF NOT EXISTS idx_job_logs_step ON job_logs(step);
CREATE INDEX IF NOT EXISTS idx_job_logs_paper_id ON job_logs(paper_id);
CREATE INDEX IF NOT EXISTS idx_job_logs_job_run_level ON job_logs(job_run_id, level);
CREATE INDEX IF NOT EXISTS idx_job_logs_job_run_timestamp ON job_logs(job_run_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_job_status_history_job_run_id ON job_status_history(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_status_history_timestamp ON job_status_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_job_status_history_to_status ON job_status_history(to_status);

CREATE INDEX IF NOT EXISTS idx_job_metrics_job_run_id ON job_metrics(job_run_id);
CREATE INDEX IF NOT EXISTS idx_job_metrics_timestamp ON job_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_job_metrics_name ON job_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_job_metrics_job_run_name ON job_metrics(job_run_id, metric_name);

-- Add comments for documentation
COMMENT ON TABLE job_logs IS 'Structured logs for job runs with partitioning support';
COMMENT ON TABLE job_status_history IS 'Status change history for job runs';
COMMENT ON TABLE job_metrics IS 'Real-time metrics for job runs';

COMMENT ON COLUMN job_logs.level IS 'Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL';
COMMENT ON COLUMN job_logs.step IS 'Current execution step';
COMMENT ON COLUMN job_logs.paper_id IS 'Related paper if applicable';
COMMENT ON COLUMN job_logs.duration_ms IS 'Duration of the operation in milliseconds';

COMMENT ON COLUMN job_status_history.from_status IS 'Previous status (null for initial status)';
COMMENT ON COLUMN job_status_history.to_status IS 'New status';
COMMENT ON COLUMN job_status_history.reason IS 'Reason for status change';

COMMENT ON COLUMN job_metrics.metric_name IS 'Name of the metric (e.g., papers_processed, embedding_errors)';
COMMENT ON COLUMN job_metrics.metric_type IS 'Type of metric: counter, gauge, histogram';
COMMENT ON COLUMN job_metrics.labels IS 'Key-value pairs for metric dimensions'; 