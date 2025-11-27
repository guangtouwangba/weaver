-- Fix missing file_path column in documents table
-- Run this in Supabase SQL Editor if you encounter:
-- "sqlalchemy.exc.ProgrammingError: column documents.file_path does not exist"

DO $$ 
BEGIN
    -- Check if file_path column exists
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
        RAISE NOTICE 'file_path column already exists, no action needed.';
    END IF;
END $$;

-- Verify the change
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'documents' 
AND column_name = 'file_path';

