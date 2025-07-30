# ===============================
# Zeabur Backend Dockerfile
# Research Agent RAG System - Backend API
# ===============================

# ===============================
# Stage 1: Dependencies Builder
# ===============================
FROM python:3.11-slim AS deps-builder

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=3

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt ./

# Configure pip to use mirrors and install dependencies
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ===============================
# Stage 2: Production Image
# ===============================
FROM python:3.11-slim AS production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    # FastAPI/Uvicorn settings
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1 \
    # Performance tuning
    MALLOC_TRIM_THRESHOLD_=100000 \
    MALLOC_MMAP_THRESHOLD_=100000

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=deps-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps-builder /usr/local/bin /usr/local/bin

# Copy backend application code
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data/vector_db /app/logs /tmp/cache && \
    chown -R appuser:appuser /app /tmp/cache

# Switch to non-root user
USER appuser

# Expose port (Zeabur will automatically set PORT environment variable)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for API server
CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# ===============================
# Labels for metadata
# ===============================
LABEL maintainer="Research Agent RAG Team" \
      version="1.0.0" \
      description="Multi-agent research paper analysis system - Backend API for Zeabur" \
      org.opencontainers.image.source="https://github.com/your-org/research-agent-rag" \
      org.opencontainers.image.title="Research Agent RAG Backend" \
      org.opencontainers.image.description="FastAPI server for multi-agent research analysis" 