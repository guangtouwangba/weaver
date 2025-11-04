-- Database initialization script
-- This file is executed when the PostgreSQL container first starts

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- Just add any custom initialization here

-- Set timezone
SET timezone = 'UTC';

-- Add any extensions you might need in the future
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Log successful initialization
DO $$ 
BEGIN
  RAISE NOTICE 'Knowledge Platform database initialized successfully';
END $$;

