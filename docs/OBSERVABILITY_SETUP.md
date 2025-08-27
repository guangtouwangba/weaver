# RAG System Observability Setup

This guide explains how to set up and use the comprehensive observability stack for your RAG system, featuring modern log aggregation with Grafana Loki and AI-native monitoring with Pydantic Logfire.

## Architecture Overview

Our observability stack consists of:

### **Primary Log Aggregation Stack**
- **Grafana Loki**: Lightweight log aggregation (indexes metadata only, not full content)
- **Promtail**: Log collector that forwards logs from files and containers to Loki
- **Grafana**: Unified visualization for logs, metrics, and traces
- **Prometheus**: Metrics collection for system and application monitoring

### **AI-Native Observability** 
- **Pydantic Logfire**: Native FastAPI integration with LLM call tracing
- **Custom AI Metrics**: RAG operation monitoring, embedding performance, document processing

## Quick Start

### 1. Start the Observability Stack

```bash
# Start all middleware services including the observability stack
make start

# Check service status
make status

# View logs from all services
make logs
```

### 2. Access the Dashboards

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### 3. Configure Application Logging

```python
from logging_system import (
    LoggingConfig, 
    setup_logging, 
    get_logger,
    setup_logfire_integration
)

# Setup enhanced observability configuration
config = LoggingConfig.for_observability()
setup_logging(config)

# Initialize AI-native observability (requires LOGFIRE_TOKEN env var)
setup_logfire_integration(config)

# Get logger
logger = get_logger(__name__)
```

## Service Configuration

### Starting Services

The observability stack is integrated into your Docker middleware:

```yaml
# Services added to docker-compose.middleware.yaml:
- loki:3100         # Log aggregation
- promtail          # Log collection
- grafana:3000      # Visualization
- prometheus:9090   # Metrics collection
```

### Log Collection

Promtail automatically collects logs from:
- Application log files in `./logs/` directory
- Docker container logs
- FastAPI application structured logs
- Celery worker logs
- Error logs for priority monitoring

## AI-Native Observability Features

### LLM Call Monitoring

```python
from logging_system import log_llm_call, trace_span

# Automatic LLM call logging
with trace_span("openai_completion") as span:
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Log the call with metrics
    log_llm_call(
        model="gpt-4",
        prompt=prompt,
        response=response.choices[0].message.content,
        tokens_used=response.usage.total_tokens,
        duration_ms=span.duration if span else None
    )
```

### RAG Operation Monitoring

```python
from logging_system import log_rag_operation

# Monitor RAG operations
log_rag_operation(
    operation="semantic_search",
    query="What is the latest research on transformers?",
    num_results=5,
    duration_ms=234.5,
    vector_store="weaviate",
    collection="research_papers"
)
```

### Document Processing Monitoring

```python  
from logging_system import log_document_processing

# Track document processing pipeline
log_document_processing(
    file_name="research_paper.pdf",
    file_size=2048000,  # 2MB
    processing_stage="chunking",
    duration_ms=1500.2,
    chunks_created=45,
    strategy="semantic_chunking"
)
```

## Viewing Logs and Metrics

### Grafana Dashboard

1. **RAG System Overview**: Pre-built dashboard showing:
   - Log levels distribution
   - API request rates
   - Error logs in real-time
   - Celery task queue metrics
   - Response time percentiles

2. **AI Operations Dashboard**: Tracks:
   - LLM API calls and token usage
   - RAG operation performance  
   - Document processing metrics
   - Vector database operations

### Log Queries in Grafana

**Recent Errors Across All Services**:
```logql
{service=~"rag-api|rag-worker"} |= "ERROR"
```

**API Request Logs with Timing**:
```logql
{service="rag-api"} | json | duration_ms > 1000
```

**LLM Call Analysis**:
```logql
{service="rag-api"} | json | line =~ "LLM Call" 
```

**RAG Operation Performance**:
```logql
{service="rag-api"} | json | line =~ "RAG" | duration_ms > 500
```

### Prometheus Queries

**API Request Rate**:
```promql
rate(fastapi_requests_total{job="rag-api"}[5m])
```

**Response Time 95th Percentile**:
```promql
histogram_quantile(0.95, rate(fastapi_request_duration_seconds_bucket[5m]))
```

**Task Queue Length**:
```promql
celery_task_total{job="rag-workers"}
```

## Advanced Configuration

### Production Logging Configuration

```python
# For production with Loki integration
config = LoggingConfig.for_production()
setup_logging(config)
```

This includes:
- JSON structured logging
- Async file logging (50MB rotation)
- Loki integration for centralized logs
- Error-level console output only

### Custom Loki Labels

```python
from logging_system.config import LoggingConfig, HandlerConfig, LogOutput

config = LoggingConfig(
    handlers=[
        HandlerConfig(
            type=LogOutput.ASYNC_LOKI,
            loki_url="http://localhost:3100",
            loki_labels={
                "environment": "staging",
                "service": "rag-api",
                "team": "ai-research",
                "version": "v2.1.0"
            }
        )
    ]
)
```

### Environment Variables

Set these environment variables for enhanced observability:

```bash
# Required for Pydantic Logfire
LOGFIRE_TOKEN=your_logfire_token

# Optional: Custom Loki endpoint
LOKI_URL=http://localhost:3100

# Log level configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# AI observability features
LOG_INCLUDE_CONTEXT=true
LOG_INCLUDE_PERFORMANCE=true
```

## Alerting and Monitoring

### Built-in Alerts

The system includes pre-configured alerts for:
- High error rates (>5% of requests)
- Slow API responses (>2 seconds 95th percentile)
- Failed task processing
- High memory/CPU usage

### Custom Alert Rules

Add custom Prometheus alert rules in `config/prometheus/alert_rules.yml`:

```yaml
groups:
  - name: rag-system-alerts
    rules:
      - alert: HighLLMTokenUsage
        expr: rate(llm_tokens_total[5m]) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High LLM token usage detected
          
      - alert: RAGSearchLatency
        expr: histogram_quantile(0.95, rate(rag_search_duration_seconds_bucket[5m])) > 2
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: RAG search operations are too slow
```

## Troubleshooting

### Common Issues

**Loki Connection Failed**:
```bash
# Check Loki service status
docker logs rag-loki

# Verify Loki is accessible
curl http://localhost:3100/ready
```

**Missing AI Observability**:
- Ensure `logfire` is installed: `uv add logfire`
- Set `LOGFIRE_TOKEN` environment variable
- Check imports in your code

**High Log Volume**:
```python
# Reduce log level in production
config = LoggingConfig.for_production()  # Uses INFO level
config.level = LogLevel.WARNING  # Even more restrictive
```

### Log Retention

- **Loki**: 7 days (configurable in `config/loki/local-config.yaml`)
- **Local files**: 10 files × 50MB = 500MB total
- **Prometheus**: 30 days retention

This setup provides comprehensive observability for your RAG system with both traditional logging and AI-native monitoring capabilities.