# Database Migration Guide

## Overview

This guide explains how to handle database schema changes and migrations for Weaver.

## Local Development

### Running Migrations

To apply all pending migrations to your local database:

```bash
make migrate
```

Or manually:

```bash
cd app/backend
../../venv/bin/python3 -m alembic upgrade head
```

### Creating New Migrations

When you modify SQLAlchemy models, create a new migration:

```bash
make migration
# Enter a descriptive message when prompted
```

Or manually:

```bash
cd app/backend
../../venv/bin/python3 -m alembic revision --autogenerate -m "your_message_here"
```

## Production Deployment (Zeabur)

### Current Issue: Missing `file_path` Column

If you encounter this error:

```
sqlalchemy.exc.ProgrammingError: column documents.file_path does not exist
```

This means the production database schema is out of sync.

### Solution 1: Run Migration via Supabase SQL Editor

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Run the following SQL:

```sql
-- Add file_path column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='documents' AND column_name='file_path'
    ) THEN
        -- Add column as nullable first
        ALTER TABLE documents ADD COLUMN file_path VARCHAR(512);
        
        -- Update existing rows (use filename as default)
        UPDATE documents SET file_path = filename WHERE file_path IS NULL;
        
        -- Make column non-nullable
        ALTER TABLE documents ALTER COLUMN file_path SET NOT NULL;
    END IF;
END $$;
```

### Solution 2: Run Migration via Backend Container

If you have SSH access to the Zeabur container:

```bash
# SSH into the container
zeabur ssh <service-name>

# Run migrations
cd /app
alembic upgrade head
```

### Solution 3: Automated Migration on Startup

The backend's `start-prod.sh` script can be updated to run migrations automatically:

```bash
#!/bin/bash
set -e

echo "=== Weaver API Starting ==="

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the server
echo "Starting Uvicorn server..."
exec uvicorn research_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
```

⚠️ **Note**: Automatic migrations on startup can be risky in production. Use with caution.

## Migration History

### 20241126_000001 - Initial Schema
- Created `projects`, `documents`, `document_chunks`, `canvases` tables
- Enabled pgvector extension
- Created vector index for similarity search

### 20241127_000001 - Add file_path to documents
- Added `file_path` column to `documents` table
- Handles existing data by using `filename` as default
- Required for document upload and retrieval functionality

## Best Practices

1. **Always test migrations locally first**
   ```bash
   make migrate
   ```

2. **Backup production database before major migrations**
   - Use Supabase's backup feature
   - Or export data manually

3. **Review auto-generated migrations**
   - Alembic's `--autogenerate` is smart but not perfect
   - Always review the generated migration file
   - Test with sample data

4. **Use descriptive migration messages**
   ```bash
   make migration
   # Good: "add_user_preferences_table"
   # Bad: "update"
   ```

5. **Never edit existing migrations**
   - Once deployed, migrations are immutable
   - Create a new migration to fix issues

## Troubleshooting

### Migration fails with "relation already exists"

The table or column already exists. Options:
- Skip the migration (if safe)
- Modify migration to check existence first
- Manually fix the database state

### Migration fails with "column does not exist"

The migration depends on a column that doesn't exist:
- Ensure all previous migrations ran successfully
- Check migration order (`down_revision` in migration files)

### Rollback a migration

```bash
cd app/backend
../../venv/bin/python3 -m alembic downgrade -1  # Rollback 1 migration
../../venv/bin/python3 -m alembic downgrade <revision>  # Rollback to specific revision
```

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Supabase SQL Editor](https://supabase.com/docs/guides/database/overview)

