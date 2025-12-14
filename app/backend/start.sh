#!/bin/bash

# Load .env from multiple possible locations
# Only export lines that look like valid environment variables (KEY=value)
load_env() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        # Only export lines that match: VARIABLE_NAME=value (no spaces, no commands)
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            [[ "$line" =~ ^#.*$ ]] && continue
            [[ -z "$line" ]] && continue
            # Only export if it looks like a valid env var (starts with letter/underscore, has =)
            if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
                export "$line"
            fi
        done < "$env_file"
        echo "Loaded environment from $env_file"
        return 0
    fi
    return 1
}

# Try to load .env from current directory first, then project root
if ! load_env ".env"; then
    load_env "../../.env"
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
echo "Database: ${DATABASE_URL:0:50}..."

# Run database migrations automatically (for local development)
echo ""
echo "Running database migrations..."
if python -m alembic upgrade head 2>/dev/null; then
    echo "✅ Migrations completed successfully"
else
    echo "⚠️  Migration failed or not available"
    echo "   You may need to run 'make migrate' manually"
fi

echo ""
uvicorn research_agent.main:app --reload --host 0.0.0.0 --port 8000
