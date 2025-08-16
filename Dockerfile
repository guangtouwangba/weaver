# RAG Knowledge Management System - Production Dockerfile
# Multi-stage build for optimized production container

# ============================================================================
# Stage 1: Build dependencies
# ============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production
ARG PYTHON_VERSION=3.11

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Create application directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip install --system --no-cache-dir -e .

# ============================================================================
# Stage 2: Production runtime
# ============================================================================
FROM python:3.11-slim as production

# Set runtime arguments
ARG APP_VERSION=0.1.0
ARG BUILD_DATE
ARG VCS_REF

# Set labels for container metadata
LABEL maintainer="Research Agent Team <team@research-agent.com>" \
      version="${APP_VERSION}" \
      description="RAG Knowledge Management API - Production Container" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/scripts:$PATH" \
    # Application settings
    ENVIRONMENT=production \
    DEBUG=false \
    LOG_LEVEL=INFO \
    # Server settings
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=4 \
    WORKER_CLASS=uvicorn.workers.UvicornWorker \
    WORKER_TIMEOUT=120 \
    KEEPALIVE=5 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100 \
    # Health check settings
    HEALTH_CHECK_INTERVAL=30 \
    HEALTH_CHECK_TIMEOUT=10 \
    HEALTH_CHECK_RETRIES=3

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Runtime libraries
    libpq5 \
    libffi8 \
    libssl3 \
    # Utilities for health checks and debugging
    curl \
    netcat-openbsd \
    procps \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r ragapi && useradd -r -g ragapi -d /app -s /bin/bash ragapi

# Create application directory structure
WORKDIR /app
RUN mkdir -p /app/logs /app/data /app/temp \
    && chown -R ragapi:ragapi /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=ragapi:ragapi . .

# Remove development and test files
RUN rm -rf tests/ docs/ *.md roadmap.md \
    && rm -rf .git/ .github/ .vscode/ __pycache__/ \
    && find . -name "*.pyc" -delete \
    && find . -name "__pycache__" -type d -exec rm -rf {} + \
    && find . -name ".pytest_cache" -type d -exec rm -rf {} +

# Create startup script
RUN cat > /app/docker-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Function to wait for services
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    log "Waiting for $service_name at $host:$port..."
    
    while ! nc -z "$host" "$port" > /dev/null 2>&1; do
        if [ $attempt -eq $max_attempts ]; then
            log "ERROR: $service_name at $host:$port is not available after $max_attempts attempts"
            return 1
        fi
        log "Attempt $attempt/$max_attempts: $service_name not ready, waiting..."
        sleep 2
        ((attempt++))
    done
    
    log "✅ $service_name at $host:$port is ready"
    return 0
}

# Function to run database migrations
run_migrations() {
    if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
        log "Running database migrations..."
        if alembic upgrade head; then
            log "✅ Database migrations completed successfully"
        else
            log "❌ Database migrations failed"
            return 1
        fi
    else
        log "Skipping database migrations (RUN_MIGRATIONS=false)"
    fi
}

# Function to validate configuration
validate_config() {
    log "Validating configuration..."
    if python scripts/check_dependencies.py; then
        log "✅ Configuration validation passed"
    else
        log "❌ Configuration validation failed"
        return 1
    fi
}

# Function to start the application
start_application() {
    log "Starting RAG API application..."
    log "Environment: ${ENVIRONMENT:-production}"
    log "Debug mode: ${DEBUG:-false}"
    log "Host: ${HOST:-0.0.0.0}"
    log "Port: ${PORT:-8000}"
    log "Workers: ${WORKERS:-4}"

    # Determine startup command based on environment
    if [ "${ENVIRONMENT:-production}" = "development" ]; then
        log "Starting in development mode with auto-reload"
        exec uvicorn main:app \
            --host "${HOST:-0.0.0.0}" \
            --port "${PORT:-8000}" \
            --reload \
            --log-level "${LOG_LEVEL:-info}"
    else
        log "Starting in production mode with Gunicorn"
        exec gunicorn main:app \
            --bind "${HOST:-0.0.0.0}:${PORT:-8000}" \
            --workers "${WORKERS:-4}" \
            --worker-class "${WORKER_CLASS:-uvicorn.workers.UvicornWorker}" \
            --worker-timeout "${WORKER_TIMEOUT:-120}" \
            --keepalive "${KEEPALIVE:-5}" \
            --max-requests "${MAX_REQUESTS:-1000}" \
            --max-requests-jitter "${MAX_REQUESTS_JITTER:-100}" \
            --preload \
            --log-level "${LOG_LEVEL:-info}" \
            --access-logfile - \
            --error-logfile -
    fi
}

# Main execution flow
main() {
    log "🚀 Starting RAG API container..."
    log "Build info: version=${APP_VERSION:-unknown}, date=${BUILD_DATE:-unknown}"
    
    # Wait for required services
    if [ -n "${POSTGRES_HOST}" ]; then
        wait_for_service "${POSTGRES_HOST}" "${POSTGRES_PORT:-5432}" "PostgreSQL"
    fi
    
    if [ -n "${REDIS_HOST}" ]; then
        wait_for_service "${REDIS_HOST}" "${REDIS_PORT:-6379}" "Redis"
    fi
    
    if [ -n "${MINIO_ENDPOINT}" ]; then
        # Extract host and port from MinIO endpoint
        MINIO_HOST=$(echo "${MINIO_ENDPOINT}" | cut -d':' -f1)
        MINIO_PORT=$(echo "${MINIO_ENDPOINT}" | cut -d':' -f2)
        wait_for_service "${MINIO_HOST}" "${MINIO_PORT:-9000}" "MinIO"
    fi
    
    # Validate configuration
    validate_config || exit 1
    
    # Run database migrations
    run_migrations || exit 1
    
    # Start the application
    start_application
}

# Handle signals gracefully
trap 'log "Received SIGTERM, shutting down gracefully..."; exit 0' SIGTERM
trap 'log "Received SIGINT, shutting down gracefully..."; exit 0' SIGINT

# Execute main function if script is run directly
if [ "${1}" = "start" ] || [ $# -eq 0 ]; then
    main
else
    # Allow running other commands
    exec "$@"
fi
EOF

# Make scripts executable
RUN chmod +x /app/docker-entrypoint.sh /app/scripts/*.py \
    && chown ragapi:ragapi /app/docker-entrypoint.sh

# Create health check script
RUN cat > /app/healthcheck.sh << 'EOF'
#!/bin/bash
set -e

# Health check configuration
HEALTH_URL="http://localhost:${PORT:-8000}/health"
TIMEOUT="${HEALTH_CHECK_TIMEOUT:-10}"

# Perform health check
if curl -f -s --max-time "$TIMEOUT" "$HEALTH_URL" > /dev/null 2>&1; then
    exit 0
else
    echo "Health check failed for $HEALTH_URL"
    exit 1
fi
EOF

RUN chmod +x /app/healthcheck.sh && chown ragapi:ragapi /app/healthcheck.sh

# Switch to non-root user
USER ragapi

# Expose port
EXPOSE 8000

# Configure health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh

# Set entrypoint and default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["start"]

# Build-time smoke test
RUN python -c "import main; print('✅ Application imports successfully')"