# RAG API Production Deployment Guide

This guide provides comprehensive instructions for deploying the RAG API system in production using Docker containers.

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- 4GB+ RAM
- 20GB+ storage space
- SSL certificates (for HTTPS)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd research-agent-rag

# Copy and configure environment
cp .env.production.example .env.production
# Edit .env.production with your settings
```

### 2. Deploy with One Command

```bash
# Full deployment with all services
./scripts/deploy.sh deploy

# Or deploy specific services
./scripts/deploy.sh deploy -s rag-api
```

### 3. Access Your Services

- **API**: https://your-domain.com/api/v1/
- **Health Check**: https://your-domain.com/health
- **Monitoring**: http://your-domain.com:8081/grafana/
- **Object Storage**: http://your-domain.com:8081/minio/

## 📋 Deployment Options

### Option 1: Full Stack Deployment

Deploy all services including monitoring, storage, and API:

```bash
./scripts/deploy.sh deploy
```

### Option 2: API Only Deployment

Deploy just the API service (requires external dependencies):

```bash
./scripts/deploy.sh deploy -s rag-api
```

### Option 3: Without Reverse Proxy

Deploy without nginx (direct access to API):

```bash
docker compose -f docker-compose.production.yaml up -d --profile core
```

## 🔧 Configuration

### Environment Variables

Edit `.env.production` with your specific settings:

```bash
# Application
APP_VERSION=0.1.0
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-256-bit-secret-key
POSTGRES_PASSWORD=secure_password_here
REDIS_PASSWORD=secure_redis_password
MINIO_ROOT_PASSWORD=secure_minio_password

# External APIs
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Domain and SSL
DOMAIN_NAME=api.your-domain.com
SSL_EMAIL=admin@your-domain.com
```

### SSL Certificates

Place your SSL certificates in `config/nginx/ssl/`:

```bash
# Self-signed certificates (development only)
mkdir -p config/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout config/nginx/ssl/key.pem \
  -out config/nginx/ssl/cert.pem

# Production certificates (Let's Encrypt recommended)
# Use certbot or your certificate provider
```

### Database Configuration

The deployment includes optimized PostgreSQL settings for production:

- Connection pooling: 200 connections
- Shared buffers: 256MB
- Effective cache size: 1GB
- WAL configuration for performance

### Redis Configuration

Redis is configured with:

- Password authentication
- Persistence enabled
- Memory optimization
- Connection limits

## 🔍 Monitoring and Health Checks

### Built-in Health Checks

All services include health checks:

```bash
# Check overall system health
curl https://your-domain.com/health

# Check specific service health
./scripts/deploy.sh health
```

### Monitoring Stack

Access monitoring dashboards:

- **Grafana**: http://your-domain:8081/grafana/
  - Username: admin
  - Password: (set in .env.production)

- **Prometheus**: http://your-domain:8081/prometheus/
  - Metrics collection and alerting

### Logs

View service logs:

```bash
# All services
./scripts/deploy.sh logs

# Specific service
./scripts/deploy.sh logs -s rag-api

# Follow logs in real-time
docker compose -f docker-compose.production.yaml logs -f rag-api
```

## 🔄 Operations

### Deployment Management

```bash
# Deploy/update services
./scripts/deploy.sh deploy

# Restart services
./scripts/deploy.sh restart

# Stop services
./scripts/deploy.sh stop

# Update services (with backup)
./scripts/deploy.sh update

# Force recreate containers
./scripts/deploy.sh restart --force-recreate
```

### Backup and Restore

```bash
# Create backup
./scripts/deploy.sh backup

# Restore from backup (interactive)
./scripts/deploy.sh restore

# Deploy with backup skip
./scripts/deploy.sh deploy --skip-backup
```

### Scaling

Scale specific services:

```bash
# Scale API service to 3 replicas
docker compose -f docker-compose.production.yaml up -d --scale rag-api=3

# Update load balancer configuration in nginx.conf
```

## 🚦 Status and Troubleshooting

### Check System Status

```bash
# Overall status
./scripts/deploy.sh status

# Service-specific status
docker compose -f docker-compose.production.yaml ps

# Resource usage
docker stats
```

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
./scripts/deploy.sh logs -s <service-name>

# Check configuration
./scripts/deploy.sh health

# Restart with force recreate
./scripts/deploy.sh restart --force-recreate
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
docker compose -f docker-compose.production.yaml exec postgres pg_isready

# Check credentials in .env.production
# Verify network connectivity
```

#### 3. API Returns 502/503 Errors

```bash
# Check API container health
docker compose -f docker-compose.production.yaml ps rag-api

# Check nginx configuration
docker compose -f docker-compose.production.yaml exec nginx nginx -t

# Review API logs
./scripts/deploy.sh logs -s rag-api
```

#### 4. High Memory Usage

```bash
# Check resource usage
docker stats

# Scale down if needed
docker compose -f docker-compose.production.yaml stop <service>

# Review resource limits in docker-compose.production.yaml
```

### Performance Optimization

#### Database Optimization

```bash
# Monitor database performance
docker compose -f docker-compose.production.yaml exec postgres \
  psql -U rag_user -d rag_db -c "SELECT * FROM pg_stat_activity;"

# Analyze query performance
docker compose -f docker-compose.production.yaml exec postgres \
  psql -U rag_user -d rag_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### API Performance

```bash
# Monitor API metrics
curl https://your-domain.com/metrics

# Check response times in nginx logs
docker compose -f docker-compose.production.yaml logs nginx | grep "rt="
```

## 🛡️ Security

### Security Best Practices

1. **Environment Variables**: Store sensitive data in `.env.production`
2. **SSL/TLS**: Use valid certificates for production
3. **Firewall**: Restrict access to necessary ports only
4. **Updates**: Regularly update base images
5. **Monitoring**: Enable alerting for security events

### Network Security

- Services communicate via internal Docker network
- External access only through nginx reverse proxy
- Rate limiting configured for API endpoints
- Security headers implemented

### Data Protection

- Database credentials encrypted
- API keys stored as environment variables
- Regular automated backups
- Volume encryption recommended for production

## 📊 Monitoring and Alerting

### Metrics Collection

The deployment includes:

- **Application metrics**: Custom RAG API metrics
- **Infrastructure metrics**: Docker, nginx, database
- **Business metrics**: API usage, performance

### Alert Configuration

Configure alerts in Prometheus:

```yaml
# Example alert rules
groups:
  - name: rag-api
    rules:
      - alert: APIHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseConnections
        expr: pg_stat_database_numbackends > 150
        for: 2m
        annotations:
          summary: "High database connections"
```

## 🔄 Updates and Maintenance

### Regular Maintenance

```bash
# Weekly maintenance routine
./scripts/deploy.sh backup
./scripts/deploy.sh update
./scripts/deploy.sh cleanup

# Monthly full backup
./scripts/deploy.sh backup
# Store backup externally
```

### Version Updates

```bash
# Update to new version
export APP_VERSION=0.2.0
./scripts/deploy.sh update

# Rollback if needed
docker compose -f docker-compose.production.yaml down
# Restore from backup
./scripts/deploy.sh restore
```

## 📞 Support

### Getting Help

1. Check logs: `./scripts/deploy.sh logs`
2. Verify configuration: `./scripts/deploy.sh health`
3. Review this documentation
4. Check project issues on GitHub

### Emergency Procedures

```bash
# Emergency stop
./scripts/deploy.sh stop

# Emergency rollback
docker compose -f docker-compose.production.yaml down
./scripts/deploy.sh restore

# Emergency contact
# Document your emergency contact procedures here
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [Prometheus Monitoring](https://prometheus.io/docs/)

---

For development deployment, see [README.server.md](README.server.md).
For general project information, see [README.md](README.md).