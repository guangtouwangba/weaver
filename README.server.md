# RAG API Server Guide

This guide explains how to start and manage the RAG API server.

## Quick Start

### 1. Complete Setup (First Time)

For development:
```bash
make setup-dev
```

For production-like environment:
```bash
make setup-server
```

### 2. Start the Server

**Development server with hot reload:**
```bash
make server
# or
make server-dev
```

**Production server:**
```bash
make server-prod
```

**Quick start (if middleware is already running):**
```bash
make server-quick
```

**Full stack startup:**
```bash
make server-full
```

## Server Commands

### Basic Server Operations

| Command | Description |
|---------|-------------|
| `make server` | Start development server (default) |
| `make server-dev` | Start development server with hot reload |
| `make server-prod` | Start production server with multiple workers |
| `make server-test` | Start server for testing (port 8001) |
| `make server-debug` | Start server with debug logging |
| `make server-gunicorn` | Start server with Gunicorn |

### Server Management

| Command | Description |
|---------|-------------|
| `make server-status` | Check server status and show endpoints |
| `make server-stop` | Stop running server |
| `make server-restart` | Restart development server |
| `make server-background` | Start server in background |
| `make server-logs` | Show server logs (background mode) |

### Full Stack Operations

| Command | Description |
|---------|-------------|
| `make server-full` | Start middleware + database + server |
| `make server-quick` | Quick start (middleware assumed running) |

## API Endpoints

Once the server is running, you can access:

- **Health Check**: http://localhost:8000/health
- **Server Info**: http://localhost:8000/info
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Topics API**: http://localhost:8000/api/v1/topics
- **Metrics**: http://localhost:8000/metrics

## Testing the API

### Automated Testing

```bash
# Run comprehensive API tests
make api-test

# Quick health check
make api-test-quick

# Test specific endpoints
make api-test-health
make api-test-topics
```

### Manual Testing

```bash
# Check health
curl http://localhost:8000/health

# Get server info
curl http://localhost:8000/info

# List topics
curl http://localhost:8000/api/v1/topics

# Create a topic
curl -X POST http://localhost:8000/api/v1/topics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Test Topic",
    "description": "A test topic",
    "category": "test",
    "tags": ["test", "example"]
  }'
```

## Load Testing

```bash
# Run load test
make load-test
```

## Configuration

The server reads configuration from:

1. Environment variables
2. `.env` file
3. `.env.middleware` file

Key environment variables:

- `ENVIRONMENT`: development/production/test
- `DEBUG`: true/false
- `POSTGRES_HOST`: Database host
- `REDIS_HOST`: Redis host
- `MINIO_ENDPOINT`: MinIO endpoint

## Troubleshooting

### Server Won't Start

1. **Check dependencies:**
   ```bash
   make install-server
   ```

2. **Check middleware services:**
   ```bash
   make status
   ```

3. **Check database:**
   ```bash
   make db-status
   ```

### Import Errors

If you see "ModuleNotFoundError", install dependencies:

```bash
# Install server dependencies
make install-server

# Or install all dependencies
make install-all
```

### Database Issues

```bash
# Initialize database
make db-init

# Check migration status
make db-status

# Reset database (WARNING: deletes all data)
make db-reset
```

### Port Already in Use

If port 8000 is in use:

```bash
# Stop any running servers
make server-stop

# Or find and kill the process
lsof -ti:8000 | xargs kill -9
```

## Development Workflow

1. **Initial setup:**
   ```bash
   make setup-dev
   ```

2. **Start development:**
   ```bash
   make server-dev
   ```

3. **Run tests:**
   ```bash
   make api-test
   ```

4. **Check code quality:**
   ```bash
   make check
   ```

5. **Stop everything:**
   ```bash
   make server-stop
   make stop
   ```

## Production Deployment

1. **Setup production environment:**
   ```bash
   make setup-server
   ```

2. **Start production server:**
   ```bash
   make server-prod
   ```

3. **Monitor status:**
   ```bash
   make server-status
   ```

4. **Check logs:**
   ```bash
   make server-logs
   ```

## Advanced Usage

### Custom Server Configuration

You can start the server with custom parameters:

```bash
# Custom port
$(UV) run uvicorn main:app --host 0.0.0.0 --port 8080

# Custom workers
$(UV) run gunicorn main:app -w 8 -k uvicorn.workers.UvicornWorker

# With SSL
$(UV) run uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Environment-Specific Startup

```bash
# Development
ENVIRONMENT=development make server-dev

# Production
ENVIRONMENT=production make server-prod

# Testing
ENVIRONMENT=test make server-test
```

## Support

For issues or questions:

1. Check the logs: `make server-logs`
2. Check service status: `make status`
3. Run health checks: `make api-test-health`
4. Review the main README.md for general project information