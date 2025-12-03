-- Fix Alembic Migration Version
-- Run this in Supabase SQL Editor

-- Step 1: Check current state
SELECT * FROM alembic_version;

-- Step 2: Delete old version (if any)
DELETE FROM alembic_version;

-- Step 3: Insert correct latest version
-- IMPORTANT: Use the full revision ID: 20241202_000003 (NOT 20241202_000003_add)
INSERT INTO alembic_version (version_num) 
VALUES ('20241202_000003');

-- Step 4: Verify
SELECT * FROM alembic_version;

-- Expected output:
-- version_num      
-- -----------------
-- 20241202_000003
--
-- (1 row)

