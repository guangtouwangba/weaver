# Docker Container Import Fixes

This document explains the fixes applied to resolve the Docker container import errors.

## Problem

The container was failing with the error:
```
ImportError: cannot import name 'PaperDatabase' from 'simple_paper_fetcher'
```

## Root Cause

The issue occurred because:

1. **Outdated Docker Entrypoint**: The `docker-entrypoint.sh` script was still trying to import the old `PaperDatabase` class that was removed during the Supabase integration migration.

2. **Python Cache Files**: Cached `.pyc` files in `__pycache__` directories contained references to the old class structure.

3. **Missing Dependencies**: The container was missing the `supabase` library and `python-dotenv` dependencies needed for the new database adapter.

## Fixes Applied

### 1. Updated Docker Entrypoint Script

**File**: `docker-entrypoint.sh`

**Before** (lines 24-31):
```bash
python -c "
import sys
sys.path.append('backend')
from simple_paper_fetcher import PaperDatabase
db = PaperDatabase('papers.db')
print('Database initialized successfully')
"
```

**After** (lines 24-51):
```bash
python -c "
import os
import yaml
from dotenv import load_dotenv
import sys
sys.path.append('backend')

# Load environment variables
load_dotenv()

# Load config with environment variable substitution
def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    def replace_env_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
    return yaml.safe_load(content)

# Initialize database using the new adapter
from database.database_adapter import create_database_manager
config = load_config()
db_manager = create_database_manager(config)
print(f'Database initialized successfully using {type(db_manager.adapter).__name__}')
print(f'Current paper count: {db_manager.get_paper_count()}')
"
```

### 2. Updated Dockerfile

**Added cache cleanup**:
```dockerfile
# Remove any Python cache files
RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
```

### 3. Enhanced .dockerignore

The `.dockerignore` file already contained proper cache exclusions:
```
__pycache__
*.pyc
*.pyo
*.pyd
```

### 4. Updated Dependencies

**File**: `requirements-simple.txt`

Added:
```
# Environment variables
python-dotenv==1.0.1

# Database - SQLite is built into Python
# Supabase SDK (optional, only needed when using Supabase backend)
supabase==2.9.1
```

### 5. Created Test Scripts

**File**: `scripts/test_import.py`
- Tests all critical imports
- Simulates Docker entrypoint initialization
- Validates both SQLite and Supabase adapters

**File**: `scripts/build_and_test.sh`
- Automated Docker build and test script
- Validates container functionality
- Provides clear success/failure feedback

## Verification

To verify the fixes work:

1. **Test imports locally**:
   ```bash
   python scripts/test_import.py
   ```

2. **Build and test Docker image**:
   ```bash
   scripts/build_and_test.sh
   ```

3. **Manual Docker test**:
   ```bash
   docker build -t arxiv-paper-fetcher:latest .
   docker run --rm arxiv-paper-fetcher:latest test
   ```

## Expected Output

After fixes, the container should start successfully and show:
```
[2025-08-05 01:18:10] Starting ArXiv Paper Fetcher container...
[2025-08-05 01:18:10] Configuration file found ✓
[2025-08-05 01:18:10] Initializing database...
✓ Database initialized successfully using SupabaseAdapter
✓ Current paper count: X
[2025-08-05 01:18:11] Testing ArXiv API connection...
Connection test successful - found X papers
```

## Database Adapter Selection

The system now automatically selects the appropriate database adapter:

- **Supabase**: If `SUPABASE_URL` and `SUPABASE_ANON_KEY` environment variables are set
- **SQLite**: Falls back to local SQLite database for development

## Container Usage

### With Supabase (Cloud Database)

```bash
# Set environment variables
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_ANON_KEY=your_anon_key_here

# Run container
docker run --rm \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  -v $(pwd)/config.yaml:/app/config.yaml \
  arxiv-paper-fetcher:latest
```

### With SQLite (Local Database)

```bash
# Run container with local database
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/papers.db:/app/papers.db \
  arxiv-paper-fetcher:latest
```

## Troubleshooting

If you still encounter import errors:

1. **Clear all cache files**:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
   ```

2. **Rebuild Docker image without cache**:
   ```bash
   docker build --no-cache -t arxiv-paper-fetcher:latest .
   ```

3. **Check dependencies**:
   ```bash
   pip install -r requirements-simple.txt
   ```

4. **Test imports**:
   ```bash
   python scripts/test_import.py
   ```

## Summary

The fixes ensure that:
- ✅ No references to the old `PaperDatabase` class
- ✅ Proper unified database adapter usage
- ✅ All required dependencies are installed
- ✅ Cache files are properly cleaned
- ✅ Both Supabase and SQLite adapters work in containers
- ✅ Environment variable configuration is supported
- ✅ Comprehensive testing scripts are available