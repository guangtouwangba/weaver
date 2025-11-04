#!/bin/bash

# Quick Start Script for Topic Management System
set -e

echo "🚀 Starting Topic Management System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create it with:"
    echo ""
    echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/knowledge_platform"
    echo "OPENROUTER_API_KEY=your-key-here"
    echo "LLM_PROVIDER=openrouter"
    echo "LLM_MODEL=openai/gpt-4o-mini"
    echo "EMBEDDING_PROVIDER=openrouter"
    echo "EMBEDDING_MODEL=openai/text-embedding-3-small"
    echo ""
    exit 1
fi

# Start PostgreSQL with Docker
echo "📦 Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   Still waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Database is ready!"

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "apps/web/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd apps/web
    npm install
    cd ../..
    echo "✅ Frontend dependencies installed!"
fi

echo ""
echo "🎉 Setup complete! Now start the services:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd apps/api && uvicorn app:app --reload --port 8000"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd apps/web && npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""

