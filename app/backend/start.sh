#!/bin/bash

# Load .env from multiple possible locations
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Loaded .env from current directory"
elif [ -f "../../.env" ]; then
    export $(grep -v '^#' ../../.env | xargs)
    echo "Loaded .env from project root"
fi

# Check if OPENROUTER_API_KEY is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "WARNING: OPENROUTER_API_KEY is not set!"
    echo "Please create a .env file with:"
    echo "  OPENROUTER_API_KEY=sk-or-v1-your-key-here"
    exit 1
fi

echo "Starting Research Agent RAG API..."
echo "API Key: ${OPENROUTER_API_KEY:0:20}..."

uvicorn research_agent.main:app --reload --port 8000

