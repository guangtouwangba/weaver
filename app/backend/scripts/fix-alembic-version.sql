-- Fix Alembic version table
-- Use this when migrations are stuck and tables already exist

-- Step 1: Check if alembic_version table exists
-- If this query returns no rows, the table doesn't exist and migrations should work
SELECT * FROM alembic_version;

-- Step 2: If table exists but is empty or has wrong version, update it
-- Get the latest migration version from alembic/versions directory
-- Current latest: 20241202_000003_add_evaluation_log

-- Delete old version (if any)
DELETE FROM alembic_version;

-- Insert latest version
INSERT INTO alembic_version (version_num) 
VALUES ('20241202_000003_add_evaluation_log');

-- Step 3: Verify
SELECT * FROM alembic_version;

-- Expected output:
-- version_num                      
-- ---------------------------------
-- 20241202_000003_add_evaluation_log

