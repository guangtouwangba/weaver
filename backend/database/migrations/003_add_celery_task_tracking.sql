-- Migration: Add Celery task tracking to job_runs table
-- Description: Add task_id, progress tracking, and manual trigger support

-- Add new columns to job_runs table
ALTER TABLE job_runs ADD COLUMN task_id VARCHAR(255);
ALTER TABLE job_runs ADD COLUMN progress_percentage INTEGER DEFAULT 0;
ALTER TABLE job_runs ADD COLUMN current_step VARCHAR(255);
ALTER TABLE job_runs ADD COLUMN manual_trigger BOOLEAN DEFAULT FALSE;
ALTER TABLE job_runs ADD COLUMN user_params JSON;

-- Create indexes for new columns
CREATE INDEX idx_job_runs_task_id ON job_runs(task_id);
CREATE INDEX idx_job_runs_manual_trigger ON job_runs(manual_trigger);

-- Add unique constraint for task_id (allowing nulls)
CREATE UNIQUE INDEX idx_job_runs_task_id_unique ON job_runs(task_id) WHERE task_id IS NOT NULL;

-- Update existing records to set default values
UPDATE job_runs SET 
    progress_percentage = 0,
    manual_trigger = FALSE
WHERE progress_percentage IS NULL OR manual_trigger IS NULL;