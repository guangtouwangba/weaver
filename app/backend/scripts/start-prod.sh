#!/bin/bash
set -e

echo "=== Research Agent RAG API Starting ==="

# Run database migrations automatically
echo "Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    echo "⚠️  Migration failed, but continuing startup..."
    echo "   Check logs and run migrations manually if needed"
fi

# Start the server
echo "Starting Uvicorn server..."
exec uvicorn research_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
