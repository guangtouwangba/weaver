#!/bin/bash

# Database setup script for Knowledge Platform
# This script starts the database and runs migrations

set -e

echo "🐘 Starting PostgreSQL database..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
  echo "  Waiting..."
done

echo "✅ PostgreSQL is ready!"

echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "✨ Database setup complete!"
echo ""
echo "📊 Database info:"
echo "  URL: postgresql://postgres:password@localhost:5432/knowledge_platform"
echo "  Tables: Run 'alembic current' to check migration status"
echo ""
echo "🚀 You can now start the API server with:"
echo "  uvicorn app:app --reload --port 8000"

