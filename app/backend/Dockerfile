# Research Agent RAG API - Production Dockerfile
# Build: docker build -t research-rag-api .
# Run: docker run -p 8000:8000 research-rag-api

FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend package files (pyproject.toml needs README.md)
COPY pyproject.toml README.md ./
COPY src src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# --- Production Stage ---
FROM python:3.13-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Create uploads directory (will be mounted as Zeabur Volume)
RUN mkdir -p /data/uploads && chmod 755 /data/uploads

# Set Python path
ENV PYTHONPATH=/app/src
ENV UPLOAD_DIR=/data/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start script: run migrations then start server
COPY scripts/start-prod.sh /app/start-prod.sh
RUN chmod +x /app/start-prod.sh

CMD ["/app/start-prod.sh"]

