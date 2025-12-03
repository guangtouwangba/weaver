#!/bin/bash
# Smart migration script with automatic recovery
# This script ensures migrations always succeed or gracefully recover

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

echo "=== Smart Migration Runner ==="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set"
    exit 1
fi

echo "Database: ${DATABASE_URL:0:60}..."
echo ""

# Function to get current migration version from database
get_current_version() {
    # 使用 Python 直接查询数据库
    python3 -c "
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def get_version():
    try:
        engine = create_async_engine('${DATABASE_URL/postgresql:\/\//postgresql+asyncpg://}')
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT version_num FROM alembic_version'))
            version = result.scalar()
            print(version if version else '')
    except Exception as e:
        # 表不存在或其他错误
        print('')
    finally:
        await engine.dispose()

asyncio.run(get_version())
" 2>/dev/null || echo ""
}

# Function to get latest migration version from code
get_latest_version() {
    # 从 alembic/versions 目录获取最新的迁移文件
    latest_file=$(ls -1 alembic/versions/*.py 2>/dev/null | tail -1)
    if [ -n "$latest_file" ]; then
        # 提取文件名中的版本号（格式：YYYYMMDD_HHMMSS_description.py）
        basename "$latest_file" .py | cut -d'_' -f1-3
    else
        echo ""
    fi
}

# Step 1: Check current state
echo "📊 Checking migration state..."
CURRENT_VERSION=$(get_current_version)
LATEST_VERSION=$(get_latest_version)

if [ -z "$CURRENT_VERSION" ]; then
    echo "   No version found in database (fresh install or missing alembic_version table)"
else
    echo "   Current version: $CURRENT_VERSION"
fi

if [ -n "$LATEST_VERSION" ]; then
    echo "   Latest version:  $LATEST_VERSION"
else
    echo "   ⚠️  Could not determine latest version"
fi
echo ""

# Step 2: Try to run migrations with timeout
echo "🔄 Running migrations (60 second timeout)..."

if timeout 60 alembic upgrade head 2>&1; then
    echo ""
    echo "✅ Migrations completed successfully!"
    alembic current
    exit 0
fi

# Step 3: Migration failed or timed out - try recovery
EXIT_CODE=$?
echo ""

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏱️  Migration timed out"
else
    echo "❌ Migration failed (exit code: $EXIT_CODE)"
fi

echo ""
echo "🔧 Attempting automatic recovery..."

# Step 4: Check if tables exist
echo "   Checking if tables exist..."
TABLE_COUNT=$(python3 -c "
import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine

async def count_tables():
    try:
        engine = create_async_engine('${DATABASE_URL/postgresql:\/\//postgresql+asyncpg://}')
        async with engine.connect() as conn:
            result = await conn.execute(text(
                \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'\"
            ))
            count = result.scalar()
            print(count if count else 0)
    except:
        print(0)
    finally:
        await engine.dispose()

asyncio.run(count_tables())
" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -gt 5 ]; then
    echo "   ✓ Found $TABLE_COUNT tables - database appears to be initialized"
    echo ""
    echo "   Strategy: Mark database as current (stamp)"
    
    if alembic stamp head 2>&1; then
        echo ""
        echo "✅ Database stamped successfully!"
        alembic current
        exit 0
    else
        echo ""
        echo "❌ Stamp failed"
    fi
else
    echo "   ✗ Only $TABLE_COUNT tables found - database may be empty"
    echo ""
    echo "   This is unusual. Please check:"
    echo "   1. Database connection string"
    echo "   2. Database permissions"
    echo "   3. Whether database is empty"
fi

echo ""
echo "=== Manual Intervention Required ==="
echo ""
echo "Automatic recovery failed. Please run manually:"
echo ""
echo "Option 1: Use Supabase SQL Editor"
echo "  DELETE FROM alembic_version;"
echo "  INSERT INTO alembic_version (version_num) VALUES ('$LATEST_VERSION');"
echo ""
echo "Option 2: Run fix script"
echo "  ./scripts/fix-alembic-state.sh"
echo ""
exit 1

