-- Migration 003: Add missing fields to job_runs table
-- This migration adds the missing fields that are defined in the SQLAlchemy model

-- Add task_id column to job_runs table
ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS task_id VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_job_runs_task_id ON job_runs(task_id);

-- Add progress tracking columns
ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS progress_percentage INTEGER DEFAULT 0;
ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS current_step VARCHAR(255);

-- Add manual trigger tracking columns
ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS manual_trigger BOOLEAN DEFAULT false;
ALTER TABLE job_runs ADD COLUMN IF NOT EXISTS user_params JSONB;

-- Create index for manual_trigger
CREATE INDEX IF NOT EXISTS idx_job_runs_manual_trigger ON job_runs(manual_trigger); 