#!/bin/bash
# Worker start script for Zeabur deployment

set -e

echo "🚀 Starting ARQ Worker..."
echo "   Environment: ${ENVIRONMENT:-production}"
echo "   Redis URL: ${REDIS_URL:0:30}..."

# Start the ARQ worker
cd /app
python -m research_agent.worker.arq_main















