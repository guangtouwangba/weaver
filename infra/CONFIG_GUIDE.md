# Environment Configuration Guide

This guide explains how to configure the Research Agent RAG system using a single `.env` file for all deployment scenarios.

## Single Environment File Approach

**One file to rule them all!** The system now uses a single comprehensive `.env` file that can handle:
- **Local development** (services running locally)
- **Docker development** (services in containers)  
- **Production deployment** (cloud services)
- **Hybrid setups** (mix of local and remote services)

## Quick Setup

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your configuration

3. **Choose your deployment mode** by setting the appropriate host values

## Database Configuration

### PostgreSQL Settings

```bash
# Connection settings
POSTGRES_HOST=localhost        # localhost for local, postgres for Docker
POSTGRES_PORT=5432            # Default PostgreSQL port
POSTGRES_DB=research_agent    # Database name
POSTGRES_USER=research_user   # Database user
POSTGRES_PASSWORD=your_password  # Strong password

# Connection pool settings
POSTGRES_MAX_CONNECTIONS=20   # Max concurrent connections
POSTGRES_CONNECTION_TIMEOUT=30 # Connection timeout in seconds
POSTGRES_SSL_MODE=disable     # SSL mode (disable/require/verify-full)
```

### Redis Settings

```bash
# Connection settings
REDIS_HOST=localhost          # localhost for local, redis for Docker
REDIS_PORT=6379              # Default Redis port
REDIS_PASSWORD=your_password  # Redis password (empty for no auth)
REDIS_DB=0                   # Redis database number

# Connection pool settings
REDIS_MAX_CONNECTIONS=20     # Max concurrent connections
REDIS_CONNECTION_TIMEOUT=5   # Connection timeout in seconds
REDIS_SOCKET_KEEPALIVE=true  # Keep connections alive
```

### Vector Database Settings

Choose your vector database provider:

```bash
VECTOR_DB_TYPE=chroma        # Options: chroma, weaviate, pinecone, qdrant
```

#### ChromaDB (Local Development)
```bash
CHROMA_HOST=                 # Empty for local, chroma for Docker
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=research-papers
```

#### Weaviate (Docker/Production)
```bash
WEAVIATE_HOST=weaviate       # Service name in Docker
WEAVIATE_PORT=8080
WEAVIATE_SCHEME=http
WEAVIATE_API_KEY=            # Optional API key
WEAVIATE_CLASS_NAME=ResearchPaper
```

#### Pinecone (Cloud)
```bash
PINECONE_API_KEY=your_api_key
PINECONE_ENVIRONMENT=us-west1-gcp-free
PINECONE_INDEX_NAME=research-papers
```

#### Qdrant (Self-hosted)
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=              # Optional API key
QDRANT_COLLECTION_NAME=research-papers
```

## Deployment Scenarios

### 1. Local Development (No Docker)

Edit your `.env` file:

```bash
# Use local services
POSTGRES_HOST=localhost
REDIS_HOST=localhost
VECTOR_DB_TYPE=chroma        # Local ChromaDB
CHROMA_HOST=                 # Empty for file-based storage

# Development settings
DEPLOYMENT_MODE=local
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

### 2. Docker Development

Edit your `.env` file:

```bash
# Use Docker service names
POSTGRES_HOST=postgres
REDIS_HOST=redis
WEAVIATE_HOST=weaviate

# Docker-optimized settings
DEPLOYMENT_MODE=docker
VECTOR_DB_TYPE=weaviate
LOG_LEVEL=INFO
NODE_ENV=production
API_BASE_URL=http://research-agent-backend:8000
```

**Commands:**
```bash
# Start middleware
make docker-run-middleware

# Start applications
make docker-run-apps

# Or start everything
make docker-run
```

### 3. Production Deployment

Edit your `.env` file:

```bash
# Production database settings
POSTGRES_HOST=your-db-host.com
POSTGRES_PASSWORD=secure_password
POSTGRES_SSL_MODE=require

# Secure Redis
REDIS_HOST=your-redis-host.com
REDIS_PASSWORD=secure_password

# Production vector DB
VECTOR_DB_TYPE=pinecone      # Or weaviate
PINECONE_API_KEY=your_key

# Security settings
DEPLOYMENT_MODE=production
ENABLE_API_KEY_AUTH=true
ENABLE_RATE_LIMITING=true
DEBUG_MODE=false
```

## Configuration Examples

### Quick Configuration Templates

The `.env` file includes quick setup examples at the bottom:

```bash
# FOR LOCAL DEVELOPMENT:
POSTGRES_HOST=localhost
REDIS_HOST=localhost  
VECTOR_DB_TYPE=chroma
CHROMA_HOST=

# FOR DOCKER SETUP:
POSTGRES_HOST=postgres
REDIS_HOST=redis
WEAVIATE_HOST=weaviate
VECTOR_DB_TYPE=weaviate
DEPLOYMENT_MODE=docker

# FOR PRODUCTION:
POSTGRES_HOST=your-db-host.com
POSTGRES_SSL_MODE=require
REDIS_HOST=your-redis-host.com
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your_key
ENABLE_API_KEY_AUTH=true
DEBUG_MODE=false
```

## Environment Variable Precedence

1. **Docker Compose variables** (highest priority)
2. **Environment file (.env)**
3. **System environment variables**
4. **Default values in config.py** (lowest priority)

## Common Configurations

### Development with External Services
```bash
# Use external PostgreSQL and Redis
POSTGRES_HOST=your-external-db.com
POSTGRES_SSL_MODE=require
REDIS_HOST=your-external-redis.com

# Use local ChromaDB
VECTOR_DB_TYPE=chroma
CHROMA_HOST=
```

### Hybrid Cloud Setup
```bash
# Local middleware
POSTGRES_HOST=localhost
REDIS_HOST=localhost

# Cloud vector DB
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your_key
```

### Full Cloud Deployment
```bash
# All external services
POSTGRES_HOST=your-db.amazonaws.com
POSTGRES_SSL_MODE=require
REDIS_HOST=your-cache.amazonaws.com
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=your_key
```

## Configuration Validation

The system validates configuration on startup:

```python
from config import Config

# Validate configuration
try:
    Config.validate()
    print("✅ Configuration is valid")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
```

## Helper Methods

```python
from config import Config

# Get database URLs
postgres_url = Config.get_postgres_url()
redis_url = Config.get_redis_url()

# Debug configuration
config_dict = Config.to_dict()
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use strong passwords** for databases
3. **Enable SSL** for production databases
4. **Rotate credentials** regularly
5. **Use secrets management** in production
6. **Limit connection pools** appropriately
7. **Enable authentication** for production APIs

## Troubleshooting

### Connection Issues
```bash
# Test database connections
make docker-health

# Check service logs
make docker-logs-db
make docker-logs-api
```

### Configuration Issues
```bash
# Validate configuration
cd backend && python -c "from config import Config; Config.validate()"

# Debug configuration
cd backend && python -c "from config import Config; import json; print(json.dumps(Config.to_dict(), indent=2))"
```

### Common Problems

1. **Wrong service names in Docker**: Use `postgres`, `redis`, `weaviate` not `localhost`
2. **Port conflicts**: Change ports if services are already running locally
3. **Missing API keys**: Ensure all required API keys are set
4. **SSL issues**: Set `POSTGRES_SSL_MODE=disable` for local development
5. **Vector DB not initialized**: Check vector database logs and configuration

## Advanced Configuration

### Custom Agent Configurations
```bash
# Individual agent settings
GOOGLE_ENGINEER_PROVIDER=openai
GOOGLE_ENGINEER_MODEL=gpt-4o-mini
MIT_RESEARCHER_PROVIDER=anthropic
MIT_RESEARCHER_MODEL=claude-3-5-sonnet-20241022

# Or use JSON format
AGENT_CONFIGS='{"google_engineer": {"provider": "openai", "model": "gpt-4o"}}'
```

### Performance Tuning
```bash
# Connection pools
POSTGRES_MAX_CONNECTIONS=50
REDIS_MAX_CONNECTIONS=50

# Vector database settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_PAPERS_PER_QUERY=100

# Caching
RESEARCH_TOPICS_CACHE_TTL=3600
```

### Monitoring and Logging
```bash
# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/app/logs/app.log

# Server settings
WORKERS=4                   # Number of worker processes
HOST=0.0.0.0               # Bind address
PORT=8000                  # Server port
```