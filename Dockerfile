# ArXiv Paper Fetcher - Dockerfile
# Runs the paper fetching scheduler in a container

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

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-simple.txt

# Copy application code
COPY . .

# Remove any Python cache files
RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy and make entrypoint script executable
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/downloaded_papers /app/logs

# Create a non-root user for security
RUN groupadd -r paperuser && useradd -r -g paperuser paperuser

# Make sure the paperuser owns the app directory
RUN chown -R paperuser:paperuser /app

# Switch to non-root user
USER paperuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('papers.db'); print('OK')" || exit 1

# Expose ports (if needed for monitoring)
EXPOSE 8080

# Use entrypoint script
ENTRYPOINT ["/docker-entrypoint.sh"]

# Default command - run the scheduler
CMD ["scheduler"]