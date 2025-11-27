-- Fix production database schema mismatches
-- Run this in Supabase SQL Editor if you encounter schema-related errors

BEGIN;

-- ============================================================
-- Fix 1: Add file_path column to documents table
-- ============================================================
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'documents' 
        AND column_name = 'file_path'
    ) THEN
        RAISE NOTICE 'Adding file_path column to documents table...';
        
        -- Add column as nullable first
        ALTER TABLE documents ADD COLUMN file_path VARCHAR(512);
        
        -- Update existing rows (use filename as default path)
        UPDATE documents 
        SET file_path = filename 
        WHERE file_path IS NULL;
        
        -- Make column non-nullable
        ALTER TABLE documents 
        ALTER COLUMN file_path SET NOT NULL;
        
        RAISE NOTICE 'file_path column added successfully!';
    ELSE
        RAISE NOTICE 'file_path column already exists in documents table.';
    END IF;
END $$;

-- ============================================================
-- Fix 2: Add data column to canvases table
-- ============================================================
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'canvases' 
        AND column_name = 'data'
    ) THEN
        RAISE NOTICE 'Adding data column to canvases table...';
        
        -- Add data column with default empty object
        ALTER TABLE canvases 
        ADD COLUMN data JSONB NOT NULL DEFAULT '{}'::jsonb;
        
        -- Migrate existing data from nodes/edges/viewport to data column
        -- (for old schema compatibility)
        UPDATE canvases 
        SET data = jsonb_build_object(
            'nodes', COALESCE(nodes, '[]'::jsonb),
            'edges', COALESCE(edges, '[]'::jsonb),
            'viewport', COALESCE(viewport, '{}'::jsonb)
        )
        WHERE data = '{}'::jsonb;
        
        RAISE NOTICE 'data column added and data migrated successfully!';
    ELSE
        RAISE NOTICE 'data column already exists in canvases table.';
    END IF;
END $$;

COMMIT;

-- ============================================================
-- Verification
-- ============================================================
SELECT 'documents table columns:' as info;
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'documents' 
ORDER BY ordinal_position;

SELECT 'canvases table columns:' as info;
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'canvases' 
ORDER BY ordinal_position;

SELECT '✅ Schema fixes applied successfully!' as result;

