# Hybrid Job Scheduler - Dockerfile
# Runs the multi-threaded job scheduler in a container

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements-simple.txt .

# Install Python dependencies and additional scheduler dependencies
RUN pip install --no-cache-dir -r requirements-simple.txt && \
    pip install --no-cache-dir croniter pyyaml python-dotenv supabase

# Copy application code
COPY . .

# Remove any Python cache files
RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy and make entrypoint script executable
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/downloaded_papers /app/logs /app/data

# Create a non-root user for security
RUN groupadd -r scheduler && useradd -r -g scheduler scheduler

# Make sure the scheduler user owns the app directory
RUN chown -R scheduler:scheduler /app

# Switch to non-root user
USER scheduler

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check for hybrid scheduler
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python hybrid_job_scheduler.py --status > /dev/null || exit 1

# Expose ports (if needed for monitoring/API)
EXPOSE 8080

# Use entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command - run the hybrid scheduler
CMD ["hybrid-scheduler"]