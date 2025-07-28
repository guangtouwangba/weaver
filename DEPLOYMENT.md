# Deployment Guide - Research Agent RAG System

## Overview

This guide covers various deployment options for the Research Agent RAG System, optimized for Docker serverless platforms and production environments.

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone and setup
git clone <repository>
cd research-agent-rag

# 2. Copy and configure environment
cp deployment/.env.development .env
# Edit .env with your API keys

# 3. Run with docker-compose
docker-compose up research-agent-api
```

Access the API at: http://localhost:8000/docs

## 📦 Docker Deployment Options

### Option 1: Docker Compose (Recommended for Development)

```bash
# Production mode
docker-compose up -d research-agent-api

# Development mode with hot reload
docker-compose --profile dev up -d research-agent-dev

# With load balancer and monitoring
docker-compose --profile loadbalancer --profile monitoring up -d
```

### Option 2: Standalone Docker

```bash
# Build optimized image
docker build -f Dockerfile.serverless -t research-agent-rag:latest .

# Run container
docker run -d \
  --name research-agent-api \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  research-agent-rag:latest
```

## ☁️ Cloud Platform Deployments

### AWS ECS/Fargate

```bash
# 1. Push image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag research-agent-rag:latest <account>.dkr.ecr.us-east-1.amazonaws.com/research-agent-rag:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/research-agent-rag:latest

# 2. Create ECS task definition (see deployment/aws/task-definition.json)
# 3. Deploy to ECS service
```

### Google Cloud Run

```bash
# 1. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/research-agent-rag

# 2. Deploy to Cloud Run
gcloud run deploy research-agent-api \
  --image gcr.io/PROJECT_ID/research-agent-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --set-env-vars DEFAULT_PROVIDER=deepseek
```

### Azure Container Instances

```bash
# 1. Push to Azure Container Registry
az acr build --registry myregistry --image research-agent-rag .

# 2. Deploy to ACI
az container create \
  --resource-group myResourceGroup \
  --name research-agent-api \
  --image myregistry.azurecr.io/research-agent-rag:latest \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --environment-variables DEFAULT_PROVIDER=deepseek \
  --secure-environment-variables DEEPSEEK_API_KEY=your-key-here
```

### Digital Ocean App Platform

```yaml
# app.yaml
name: research-agent-rag
services:
- name: api
  source_dir: /
  dockerfile_path: Dockerfile.serverless
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8000
  health_check:
    http_path: /health
  envs:
  - key: DEFAULT_PROVIDER
    value: deepseek
  - key: DEEPSEEK_API_KEY
    value: your-key-here
    type: SECRET
```

## 🎯 Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl and ensure cluster access
kubectl cluster-info

# Create namespace (optional)
kubectl create namespace research-agent
```

### Deploy to Kubernetes

```bash
# 1. Create secrets (replace with your actual API keys)
kubectl create secret generic research-agent-secrets \
  --from-literal=openai-api-key="your-openai-key" \
  --from-literal=deepseek-api-key="your-deepseek-key" \
  --from-literal=anthropic-api-key="your-anthropic-key"

# 2. Apply Kubernetes manifests
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/ingress.yaml

# 3. Check deployment status
kubectl get pods -l app=research-agent-api
kubectl get services
kubectl get ingress
```

### Scaling

```bash
# Horizontal scaling
kubectl scale deployment research-agent-api --replicas=5

# Auto-scaling (HPA)
kubectl autoscale deployment research-agent-api --cpu-percent=70 --min=2 --max=10
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEFAULT_PROVIDER` | AI Provider (openai/deepseek/anthropic) | deepseek | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - | Yes |
| `OPENAI_API_KEY` | OpenAI API Key | - | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API Key | - | Optional |
| `HOST` | Server host | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |
| `WORKERS` | Uvicorn workers | 1 | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `MAX_PAPERS_PER_QUERY` | Max papers per request | 30 | No |
| `ENABLE_AGENT_DISCUSSIONS` | Enable multi-agent discussions | true | No |

### Performance Tuning

#### For Production Workloads

```env
# Optimize for production
WORKERS=1
MAX_REQUESTS_PER_MINUTE=60
DEFAULT_MAX_PAPERS=15
ARXIV_FALLBACK_MAX_PAPERS=5
MAX_QUERY_EXPANSIONS=2
```

#### For High-Traffic Scenarios

```env
# Scale horizontally instead of adding workers
WORKERS=1
# Use load balancer with multiple container instances
# Enable caching and rate limiting at the ingress level
```

## 📊 Monitoring

### Health Checks

- **Health endpoint**: `GET /health`
- **Readiness**: Database connectivity check
- **Liveness**: Application responsiveness

### Metrics Collection

```bash
# Prometheus metrics (if monitoring profile enabled)
curl http://localhost:9090/metrics

# Application metrics
curl http://localhost:8000/stats
```

### Logging

```bash
# View logs
docker logs research-agent-api

# In Kubernetes
kubectl logs -f deployment/research-agent-api
```

## 🔒 Security

### Production Security Checklist

- [ ] API keys stored in secure secret management
- [ ] Rate limiting enabled at ingress/load balancer
- [ ] TLS/SSL certificates configured
- [ ] Non-root user in container
- [ ] Resource limits configured
- [ ] Security headers enabled
- [ ] CORS origins restricted
- [ ] Network policies (Kubernetes)

### API Security

```bash
# Enable API key authentication (optional)
ENABLE_API_KEY_AUTH=true
API_KEY=your-secure-api-key

# Enable rate limiting
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
```

## 🚨 Troubleshooting

### Common Issues

1. **Container fails to start**
   ```bash
   # Check logs
   docker logs research-agent-api
   
   # Common fixes:
   # - Verify API keys are set
   # - Check disk space for vector DB
   # - Validate .env file format
   ```

2. **High memory usage**
   ```bash
   # Monitor memory
   docker stats research-agent-api
   
   # Reduce paper limits
   DEFAULT_MAX_PAPERS=10
   MAX_PAPERS_PER_QUERY=20
   ```

3. **Slow response times**
   ```bash
   # Check agent configuration
   curl http://localhost:8000/config
   
   # Use faster models
   DEEPSEEK_MODEL=deepseek-chat  # instead of gpt-4
   ```

4. **Database issues**
   ```bash
   # Reset vector database
   rm -rf data/vector_db/*
   # Restart container
   ```

### Performance Optimization

1. **Image Size Optimization**
   - Use `Dockerfile.serverless` (optimized)
   - Multi-stage build reduces size by ~60%
   - Minimal dependencies in `requirements.serverless.txt`

2. **Cold Start Optimization**
   - Pre-initialize orchestrator on startup
   - Keep containers warm with health checks
   - Use connection pooling

3. **Resource Allocation**
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "2Gi"
       cpu: "1000m"
   ```

## 📈 Scaling Strategies

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up --scale research-agent-api=3

# Kubernetes
kubectl scale deployment research-agent-api --replicas=5
```

### Load Balancing

- Use NGINX or cloud load balancers
- Configure session affinity if needed
- Enable health checks for automatic failover

### Database Scaling

- Use persistent volumes for vector database
- Consider distributed vector databases for high scale
- Implement database sharding if needed

---

## 🎯 Serverless Platform Specific Guides

### Railway

```bash
# Deploy to Railway
railway login
railway new
railway add
railway deploy
```

### Render

```yaml
# render.yaml
services:
  - type: web
    name: research-agent-api
    env: docker
    dockerfilePath: ./Dockerfile.serverless
    plan: starter
    healthCheckPath: /health
    envVars:
      - key: DEFAULT_PROVIDER
        value: deepseek
      - key: DEEPSEEK_API_KEY
        sync: false
```

### Fly.io

```toml
# fly.toml
app = "research-agent-rag"
primary_region = "dfw"

[build]
  dockerfile = "Dockerfile.serverless"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024
```

Deploy with: `fly deploy`

---

This deployment guide provides comprehensive coverage for various platforms and scenarios. Choose the deployment method that best fits your infrastructure and scaling requirements.