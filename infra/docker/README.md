# Research Agent Docker Compose Setup

This directory contains the Docker Compose configuration for the Research Agent system with PostgreSQL, Weaviate, Redis middleware services, and separate frontend/backend containers.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    Weaviate     │    │     Redis       │
│   (Database)    │    │ (Vector Store)  │    │    (Cache)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Backend API   │
                    │   (FastAPI)     │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Frontend      │
                    │   (Next.js)     │
                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 5432, 6379, 8080, 8000, 3000 available

### 2. Environment Setup

```bash
# Copy the environment template
cp env.template .env

# Edit the .env file with your API keys
nano .env
```

### 3. Start Services

```bash
# Start all services (production)
docker-compose up -d

# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start with admin tools
docker-compose --profile admin up -d

# Start with monitoring
docker-compose --profile monitoring up -d
```

## 📋 Services Overview

### Core Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| `postgres` | 5432 | PostgreSQL database | `pg_isready` |
| `weaviate` | 8080 | Vector database | HTTP `/v1/.well-known/ready` |
| `redis` | 6379 | Cache and session store | Redis `PING` |
| `research-agent-backend` | 8000 | Backend API service | HTTP `/health` |
| `research-agent-frontend` | 3000 | Frontend application | HTTP `/api/health` |

### Optional Services

| Service | Port | Description | Profile |
|---------|------|-------------|---------|
| `pgadmin` | 5050 | PostgreSQL admin interface | `admin` |
| `redis-commander` | 8081 | Redis admin interface | `admin` |
| `prometheus` | 9090 | Monitoring metrics | `monitoring` |
| `nginx` | 80 | Load balancer | `loadbalancer` |

## 🔧 Configuration

### Database Configuration

```yaml
# PostgreSQL
POSTGRES_DB: research_agent
POSTGRES_USER: research_user
POSTGRES_PASSWORD: research_password
```

### Vector Database Configuration

```yaml
# Weaviate
WEAVIATE_HOST: weaviate
WEAVIATE_PORT: 8080
WEAVIATE_SCHEME: http
```

### Cache Configuration

```yaml
# Redis
REDIS_HOST: redis
REDIS_PORT: 6379
REDIS_PASSWORD: redis_password
REDIS_DB: 0
```

### Frontend Configuration

```yaml
# Next.js
NODE_ENV: production
NEXT_TELEMETRY_DISABLED: 1
API_BASE_URL: http://research-agent-backend:8000
```

## 🗄️ Database Schema

The PostgreSQL database includes the following tables:

- `cronjobs` - Scheduled research tasks
- `job_runs` - Execution history
- `papers` - Paper metadata
- `paper_embeddings` - Vector embeddings
- `chat_sessions` - Chat history

## 🔍 Monitoring & Health Checks

### Health Check Endpoints

```bash
# Backend API Health
curl http://localhost:8000/health

# Frontend Health
curl http://localhost:3000/api/health

# Weaviate Health
curl http://localhost:8080/v1/.well-known/ready

# PostgreSQL Health
docker exec research-agent-postgres pg_isready -U research_user

# Redis Health
docker exec research-agent-redis redis-cli ping
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f research-agent-backend
docker-compose logs -f research-agent-frontend
docker-compose logs -f postgres
docker-compose logs -f weaviate
docker-compose logs -f redis
```

## 🛠️ Development

### Development Mode

```bash
# Start development environment with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View development logs
docker-compose logs -f research-agent-backend-dev
docker-compose logs -f research-agent-frontend-dev
```

### Database Management

```bash
# Access PostgreSQL
docker exec -it research-agent-postgres psql -U research_user -d research_agent

# Access Redis CLI
docker exec -it research-agent-redis redis-cli -a redis_password

# Backup PostgreSQL
docker exec research-agent-postgres pg_dump -U research_user research_agent > backup.sql

# Restore PostgreSQL
docker exec -i research-agent-postgres psql -U research_user research_agent < backup.sql
```

### Admin Tools

```bash
# Start admin tools
docker-compose --profile admin up -d

# Access PgAdmin
# URL: http://localhost:5050
# Email: admin@research-agent.com
# Password: admin_password

# Access Redis Commander
# URL: http://localhost:8081
```

## 📊 Monitoring

### Prometheus Metrics

```bash
# Start monitoring
docker-compose --profile monitoring up -d

# Access Prometheus
# URL: http://localhost:9090
```

### Custom Metrics

The API exposes metrics at `/metrics` endpoint:

- `research_agent_requests_total`
- `research_agent_request_duration_seconds`
- `research_agent_papers_processed_total`
- `research_agent_cache_hits_total`

## 🔐 Security

### Default Credentials

| Service | Username | Password | Change Required |
|---------|----------|----------|-----------------|
| PostgreSQL | `research_user` | `research_password` | ✅ Yes |
| Redis | - | `redis_password` | ✅ Yes |
| PgAdmin | `admin@research-agent.com` | `admin_password` | ✅ Yes |

### Security Recommendations

1. **Change default passwords** in production
2. **Use environment variables** for sensitive data
3. **Enable SSL/TLS** for production deployments
4. **Restrict network access** to necessary ports only
5. **Regular security updates** for base images

## 🚀 Production Deployment

### Production Configuration

```bash
# Create production environment file
cp env.template .env.production

# Edit production settings
nano .env.production

# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Considerations

- Use external PostgreSQL/Redis for high availability
- Configure proper backup strategies
- Set up monitoring and alerting
- Use secrets management for sensitive data
- Configure SSL/TLS certificates
- Set up proper logging and log rotation

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Conflicts

```bash
# Check port usage
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
netstat -tulpn | grep :8080
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# Change ports in docker-compose.yml if needed
```

#### 2. Memory Issues

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

#### 3. Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test database connection
docker exec research-agent-postgres pg_isready -U research_user
```

#### 4. Vector Database Issues

```bash
# Check Weaviate logs
docker-compose logs weaviate

# Test Weaviate connection
curl http://localhost:8080/v1/.well-known/ready
```

#### 5. Frontend Issues

```bash
# Check frontend logs
docker-compose logs research-agent-frontend

# Test frontend connection
curl http://localhost:3000/api/health
```

### Debug Commands

```bash
# Enter container shell
docker exec -it research-agent-backend bash
docker exec -it research-agent-frontend sh
docker exec -it research-agent-postgres bash
docker exec -it research-agent-redis redis-cli

# View container processes
docker exec research-agent-backend ps aux

# Check network connectivity
docker exec research-agent-backend ping postgres
docker exec research-agent-backend ping weaviate
docker exec research-agent-backend ping redis
```

## 🧪 Testing

### Run Docker Tests

```bash
# Run comprehensive docker tests
python test-docker-setup.py

# Test specific components
make docker-health
```

## 📚 Additional Resources

### Documentation

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Redis Documentation](https://redis.io/documentation)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

### Useful Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild services
docker-compose build --no-cache

# Update images
docker-compose pull

# View service status
docker-compose ps

# Scale services
docker-compose up -d --scale research-agent-backend=3
```

## 🤝 Contributing

When adding new services or modifying configurations:

1. Update this README with new service information
2. Add appropriate health checks
3. Include environment variables in `env.template`
4. Test the configuration thoroughly
5. Update documentation for any breaking changes

## 📄 License

This configuration is part of the Research Agent project. See the main project LICENSE file for details. 