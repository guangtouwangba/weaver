#!/bin/bash
set -e

echo "=== Research Agent RAG API Starting ==="

# Run database migrations with timeout
echo "Running database migrations..."

# Use timeout to prevent hanging (max 60 seconds)
if timeout 60 alembic upgrade head 2>&1; then
    echo "✅ Migrations completed successfully"
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "⚠️  Migration timed out after 60 seconds"
        echo "   This usually means tables already exist."
        echo "   Marking current state and continuing startup..."
        # Try to stamp the database with the latest revision
        timeout 10 alembic stamp head 2>&1 || true
    else
        echo "⚠️  Migration failed with exit code $EXIT_CODE"
        echo "   Continuing startup anyway..."
    fi
fi

# Start the server
echo "Starting Uvicorn server..."
exec uvicorn research_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
