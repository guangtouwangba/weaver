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

### ✅ Automatic Migrations (Recommended)

**The backend is now configured to run migrations automatically on startup.**

Both `start.sh` (local dev) and `start-prod.sh` (production) will:
1. Run `alembic upgrade head` before starting the server
2. Log success or failure
3. Continue startup even if migration fails (for debugging)

This means:
- ✅ New deployments automatically get the latest schema
- ✅ No manual intervention needed for most migrations
- ✅ Migration status is logged for debugging

### Manual Migration Options

If you need to run migrations manually or troubleshoot issues:

#### Solution 1: Run Migration via Supabase SQL Editor

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

#### Solution 3: Automated Migration on Startup (Already Configured ✅)

The backend's startup scripts (`start.sh` and `start-prod.sh`) are **already configured** to run migrations automatically.

Current implementation:
- Runs `alembic upgrade head` before server startup
- Logs migration success/failure
- Continues startup even on failure (for debugging)
- Non-blocking for quick iteration

**No action needed** - this is the default behavior.

⚠️ **Production Note**: 
- Automatic migrations work well for most schema changes
- For risky migrations (data transformations, large tables), consider running manually first
- Always test migrations in staging before production

## Supabase Integration

### Syncing Alembic Migrations with Supabase

The project uses **two migration systems**:
1. **Alembic** (app/backend/alembic/versions/) - For backend development
2. **Supabase Migrations** - For Supabase platform

#### Workflow

1. **Create migration locally**
   ```bash
   make migration
   # Or: cd app/backend && alembic revision --autogenerate -m "your_message"
   ```

2. **Test locally**
   ```bash
   make migrate
   ```

3. **Deploy to Supabase**
   
   Option A: Automatic (via start-prod.sh on deployment)
   - Just deploy, migrations run automatically
   
   Option B: Manual (via Supabase MCP)
   - Use the Supabase MCP tool to apply migrations
   - Example: `mcp_supabase_apply_migration`

4. **Or run SQL directly in Supabase**
   - Copy the migration SQL
   - Run in Supabase SQL Editor
   - Useful for quick fixes or one-time operations

### Example: Adding a New Column

```bash
# 1. Modify the model (e.g., add column to DocumentModel)
# 2. Generate migration
make migration  # Enter: "add_new_column_to_documents"

# 3. Review generated migration in alembic/versions/
# 4. Test locally
make migrate

# 5. Commit and push
git add app/backend/alembic/versions/*.py
git commit -m "feat: add new column to documents"
git push

# 6. Deploy - migration runs automatically!
```

## Migration History

### 20241202_000002 - Add TSVector for Hybrid Search
- Added `content_tsvector` column to `document_chunks` table
- Created GIN index for full-text search performance
- Added trigger for automatic tsvector updates
- Required for hybrid search (vector + keyword) functionality

### 20241202_000001 - Add Curriculum Table
- Created `curriculum` table for learning paths
- Required for personalized learning features

### 20241128_000003 - Add Graph Status
- Added status tracking for knowledge graph extraction

### 20241128_000002 - Add Task Queue and Graph Tables
- Created async task queue for background processing
- Added knowledge graph tables

### 20241128_000001 - Add Chat Messages Table
- Created `chat_messages` table for conversation history
- Required for RAG with chat context

### 20241127_000002 - Add Data Column to Canvases
- Added `data` column to store canvas state
- Required for TLDraw integration

### 20241127_000001 - Add file_path to Documents
- Added `file_path` column to `documents` table
- Handles existing data by using `filename` as default
- Required for document upload and retrieval functionality

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

