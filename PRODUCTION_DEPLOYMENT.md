# Production Deployment Guide

## 🚀 Overview

This guide explains how to deploy the Research Agent RAG System in production environments without relying on `.env` files.

## 🔧 Environment Variables

### Required Environment Variables

Set these environment variables in your production environment:

```bash
# API Keys (at least one required)
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
ANTHROPIC_API_KEY=sk-your-anthropic-key

# Default Provider
DEFAULT_PROVIDER=openai

# Model Configuration
OPENAI_MODEL=gpt-4o-mini
DEEPSEEK_MODEL=deepseek-chat
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Vector Database
VECTOR_DB_PATH=/app/data/vector_db

# Search Configuration
MIN_SIMILARITY_THRESHOLD=0.5
ENABLE_ARXIV_FALLBACK=true
ARXIV_FALLBACK_MAX_PAPERS=10

# Query Expansion
ENABLE_QUERY_EXPANSION=true
MAX_QUERY_EXPANSIONS=3

# Agent Discussions
ENABLE_AGENT_DISCUSSIONS=true
DEFAULT_SELECTED_AGENTS=Google Engineer,MIT Researcher,Industry Expert,Paper Analyst

# Research Parameters
DEFAULT_MAX_PAPERS=20
DEFAULT_INCLUDE_RECENT=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/research_agent.log

# Server Configuration
STREAMLIT_PORT=8501
STREAMLIT_HOST=0.0.0.0
```

### Optional Agent-Specific Configuration

For fine-grained control over individual agents:

```bash
# Google Engineer Agent
GOOGLE_ENGINEER_PROVIDER=deepseek
GOOGLE_ENGINEER_MODEL=deepseek-reasoner

# MIT Researcher Agent
MIT_RESEARCHER_PROVIDER=openai
MIT_RESEARCHER_MODEL=gpt-4o

# Industry Expert Agent
INDUSTRY_EXPERT_PROVIDER=anthropic
INDUSTRY_EXPERT_MODEL=claude-3-5-sonnet-20241022

# Paper Analyst Agent
PAPER_ANALYST_PROVIDER=deepseek
PAPER_ANALYST_MODEL=deepseek-chat
```

### Advanced JSON Configuration

For complex agent configurations, use JSON format:

```bash
AGENT_CONFIGS='{"google_engineer": {"provider": "deepseek", "model": "deepseek-reasoner"}, "mit_researcher": {"provider": "openai", "model": "gpt-4o"}}'
```

## 🐳 Docker Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  research-agent:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DEFAULT_PROVIDER=${DEFAULT_PROVIDER:-openai}
      - VECTOR_DB_PATH=/app/data/vector_db
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

### Docker Run

```bash
docker run -d \
  --name research-agent-rag \
  -p 8501:8501 \
  -e OPENAI_API_KEY=sk-your-key \
  -e DEEPSEEK_API_KEY=sk-your-key \
  -e DEFAULT_PROVIDER=openai \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  research-agent-rag:latest
```

## ☁️ Cloud Platform Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-agent-rag
spec:
  replicas: 1
  selector:
    matchLabels:
      app: research-agent-rag
  template:
    metadata:
      labels:
        app: research-agent-rag
    spec:
      containers:
      - name: research-agent
        image: research-agent-rag:latest
        ports:
        - containerPort: 8501
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-api-key
        - name: DEEPSEEK_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: deepseek-api-key
        - name: DEFAULT_PROVIDER
          value: "openai"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: research-agent-data
      - name: logs-volume
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: research-agent-service
spec:
  selector:
    app: research-agent-rag
  ports:
  - port: 80
    targetPort: 8501
  type: LoadBalancer
```

### AWS ECS

```json
{
  "family": "research-agent-rag",
  "containerDefinitions": [
    {
      "name": "research-agent",
      "image": "research-agent-rag:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "sk-your-key"
        },
        {
          "name": "DEFAULT_PROVIDER",
          "value": "openai"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/research-agent-rag",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "1024",
  "memory": "2048"
}
```

### Google Cloud Run

```bash
gcloud run deploy research-agent-rag \
  --image gcr.io/your-project/research-agent-rag \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="OPENAI_API_KEY=sk-your-key,DEFAULT_PROVIDER=openai"
```

## 🔐 Security Best Practices

### Secret Management

1. **Never commit API keys to version control**
2. **Use environment variables or secret management systems**
3. **Rotate API keys regularly**

### AWS Secrets Manager

```bash
# Store secrets
aws secretsmanager create-secret \
  --name research-agent/api-keys \
  --secret-string '{"openai":"sk-your-key","deepseek":"sk-your-key"}'

# Retrieve in application
aws secretsmanager get-secret-value --secret-id research-agent/api-keys
```

### Azure Key Vault

```bash
# Store secrets
az keyvault secret set --vault-name your-vault --name OpenAIApiKey --value sk-your-key

# Retrieve in application
az keyvault secret show --vault-name your-vault --name OpenAIApiKey
```

### Google Secret Manager

```bash
# Store secrets
echo -n "sk-your-key" | gcloud secrets create openai-api-key --data-file=-

# Retrieve in application
gcloud secrets versions access latest --secret openai-api-key
```

## 📊 Monitoring and Logging

### Health Check

```bash
# Check if the application is running
curl http://localhost:8501/_stcore/health

# Check logs
docker logs research-agent-rag
```

### Log Configuration

```bash
# Set log level
export LOG_LEVEL=INFO

# Set log file
export LOG_FILE=/app/logs/research_agent.log

# Enable debug mode
export LOG_LEVEL=DEBUG
```

### Metrics

The application logs the following metrics:
- API calls per provider
- Search results count
- Agent analysis time
- Error rates

## 🔧 Troubleshooting

### Common Issues

1. **No API Keys Provided**
   ```
   Solution: Set at least one API key environment variable
   ```

2. **Model Not Available**
   ```
   Solution: Check provider documentation for available models
   ```

3. **Vector Database Issues**
   ```
   Solution: Ensure VECTOR_DB_PATH is writable
   ```

4. **Memory Issues**
   ```
   Solution: Increase container memory limits
   ```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export STREAMLIT_LOGGER_LEVEL=debug
```

### Validation

Run configuration validation:

```bash
python validate_config.py
```

## 🚀 Quick Start

1. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY=sk-your-key
   export DEFAULT_PROVIDER=openai
   ```

2. **Run the application:**
   ```bash
   streamlit run chat/chat_interface.py --server.port 8501 --server.address 0.0.0.0
   ```

3. **Access the web interface:**
   ```
   http://localhost:8501
   ```

## 📝 Configuration Examples

### Minimal Configuration
```bash
export OPENAI_API_KEY=sk-your-key
export DEFAULT_PROVIDER=openai
```

### Multi-Provider Configuration
```bash
export OPENAI_API_KEY=sk-your-key
export DEEPSEEK_API_KEY=sk-your-key
export ANTHROPIC_API_KEY=sk-your-key
export DEFAULT_PROVIDER=openai
```

### Advanced Configuration
```bash
export OPENAI_API_KEY=sk-your-key
export DEEPSEEK_API_KEY=sk-your-key
export DEFAULT_PROVIDER=openai
export GOOGLE_ENGINEER_PROVIDER=deepseek
export GOOGLE_ENGINEER_MODEL=deepseek-reasoner
export MIT_RESEARCHER_PROVIDER=openai
export MIT_RESEARCHER_MODEL=gpt-4o
export VECTOR_DB_PATH=/app/data/vector_db
export LOG_LEVEL=INFO
```

## 🔄 Migration from .env Files

If you're migrating from `.env` files:

1. **Extract variables from .env:**
   ```bash
   cat .env | grep -v '^#' | grep -v '^$' > env_vars.txt
   ```

2. **Set environment variables:**
   ```bash
   export $(cat env_vars.txt | xargs)
   ```

3. **Remove .env dependency:**
   ```bash
   rm .env
   ```

4. **Verify configuration:**
   ```bash
   python validate_config.py
   ``` 