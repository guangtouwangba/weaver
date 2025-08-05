-- Fix RLS policy to allow anonymous write access
-- Run this in your Supabase SQL Editor

-- Drop the existing restrictive policy
DROP POLICY IF EXISTS "Authenticated write access" ON papers;

-- Create a new policy that allows anonymous write access
-- Note: This is suitable for development/personal projects
-- For production, consider using service role key or custom authentication
CREATE POLICY "Allow anonymous write access" ON papers
    FOR ALL TO anon, authenticated
    USING (true)
    WITH CHECK (true);

-- Verify the policy is created
SELECT * FROM pg_policies WHERE tablename = 'papers';