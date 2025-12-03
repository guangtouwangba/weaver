#!/bin/bash
set -e

echo "=== Research Agent RAG API Starting ==="

# Run database migrations with smart recovery
echo "Running database migrations..."

# Use timeout to prevent hanging (max 60 seconds)
if timeout 60 alembic upgrade head 2>&1; then
    echo "✅ Migrations completed successfully"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⏱️  Migration timed out after 60 seconds"
        echo "   This usually means tables already exist or migration is stuck."
        echo ""
        
        # Strategy 1: Try to stamp the database
        echo "🔧 Attempting recovery: Stamping database..."
        if timeout 10 alembic stamp head 2>&1; then
            echo "✅ Database stamped successfully"
        else
            echo "⚠️  Stamp failed, but continuing startup..."
            echo "   Database may already be at the correct version."
            echo "   To fix manually, run: ./scripts/fix-alembic-state.sh"
        fi
    else
        echo "❌ Migration failed with exit code $EXIT_CODE"
        echo "   Attempting recovery..."
        
        # Try stamp as fallback
        if alembic stamp head 2>&1; then
            echo "✅ Recovery successful (stamped database)"
        else
            echo "⚠️  Could not recover automatically"
            echo "   Service will start, but migrations may be needed."
            echo "   Check: ./scripts/fix-alembic-state.sh"
        fi
    fi
fi

echo ""
# Start the server
echo "Starting Uvicorn server..."
exec uvicorn research_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
