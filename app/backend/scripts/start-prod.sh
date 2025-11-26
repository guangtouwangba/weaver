#!/bin/bash
set -e

echo "=== Research Agent RAG API Starting ==="

# Note: Database migrations are managed via Supabase MCP
# Tables and pgvector extension are already set up in Supabase

# Start the server
echo "Starting Uvicorn server..."
exec uvicorn research_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
