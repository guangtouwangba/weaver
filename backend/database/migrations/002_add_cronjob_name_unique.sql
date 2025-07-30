-- Migration 002: Add unique constraint to cronjobs name field
-- This migration adds a unique constraint to prevent duplicate job names

-- Add unique constraint to cronjobs name field
ALTER TABLE cronjobs ADD CONSTRAINT unique_cronjob_name UNIQUE (name);

-- Create index for better performance on name lookups
CREATE INDEX IF NOT EXISTS idx_cronjobs_name ON cronjobs(name); 