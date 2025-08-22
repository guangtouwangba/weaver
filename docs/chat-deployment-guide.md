# Chat系统部署运维指南

## 📋 概述

本文档详细说明Chat系统的部署配置、运维监控和故障处理方案，支持本地开发、测试环境和生产环境的部署。

## 🏗️ 系统架构

### 部署架构图

```mermaid
graph TB
    subgraph "负载均衡层"
        LB[Nginx Load Balancer]
    end
    
    subgraph "应用层"
        API1[Chat API Server 1]
        API2[Chat API Server 2]
        API3[Chat API Server 3]
    end
    
    subgraph "异步任务层"
        Worker1[Celery Worker 1]
        Worker2[Celery Worker 2]
        Worker3[Celery Worker 3]
    end
    
    subgraph "缓存层"
        Redis[(Redis Cluster)]
    end
    
    subgraph "数据层"
        PG[(PostgreSQL)]
        Vector[(Weaviate)]
        Storage[(MinIO)]
    end
    
    subgraph "监控层"
        Prometheus[Prometheus]
        Grafana[Grafana]
        AlertManager[Alert Manager]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    
    API1 --> PG
    API2 --> PG
    API3 --> PG
    
    API1 --> Vector
    API2 --> Vector
    API3 --> Vector
    
    API1 --> Storage
    API2 --> Storage
    API3 --> Storage
    
    Worker1 --> Redis
    Worker2 --> Redis
    Worker3 --> Redis
    
    Worker1 --> PG
    Worker2 --> PG
    Worker3 --> PG
    
    Prometheus --> API1
    Prometheus --> API2
    Prometheus --> API3
    Prometheus --> Redis
    Prometheus --> PG
    
    Grafana --> Prometheus
    AlertManager --> Prometheus
```

## 🐳 Docker部署

### 1. Docker Compose配置

```yaml
# docker-compose.chat.yml
version: '3.8'

services:
  # Chat API服务
  chat-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/rag_db
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - postgres
      - redis
      - weaviate
      - minio
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  chat-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A worker worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/rag_db
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin123
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - postgres
      - redis
      - weaviate
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
    deploy:
      replicas: 2

  # PostgreSQL数据库
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=rag_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db:/docker-entrypoint-initdb.d
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Weaviate向量数据库
  weaviate:
    image: semitechnologies/weaviate:1.21.1
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: 'text2vec-openai,generative-openai'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/v1/.well-known/ready"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MinIO对象存储
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx负载均衡
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./config/nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - chat-api
    restart: unless-stopped

  # Prometheus监控
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  # Grafana可视化
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
  minio_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

### 2. 应用Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-db.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-db.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Nginx配置

```nginx
# config/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream chat_api {
        server chat-api:8000;
        # 添加更多实例进行负载均衡
        # server chat-api-2:8000;
        # server chat-api-3:8000;
    }

    # WebSocket升级配置
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    server {
        listen 80;
        server_name localhost;

        # 客户端最大请求体大小
        client_max_body_size 100M;

        # 日志配置
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        # API请求
        location /api/ {
            proxy_pass http://chat_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 静态文件
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # 文件下载
        location /downloads/ {
            alias /app/uploads/;
            expires 1h;
        }

        # 健康检查
        location /health {
            proxy_pass http://chat_api/health;
        }

        # 前端应用 (如果部署前端)
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }
    }

    # HTTPS配置 (生产环境)
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

        # 同上面的location配置
        location /api/ {
            proxy_pass http://chat_api;
            # ... 其他配置
        }
    }
}
```

## 🔧 环境配置

### 1. 环境变量配置

```bash
# .env.production
# 基础配置
APP_ENV=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://user:password@postgres:5432/rag_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis配置
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50

# 存储配置
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
BUCKET_NAME=rag-chat-uploads

# LLM配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.7

# 向量数据库配置
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=

# 监控配置
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8001
SENTRY_DSN=your-sentry-dsn

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log

# 安全配置
CORS_ORIGINS=["http://localhost:3000", "https://your-domain.com"]
ALLOWED_HOSTS=["localhost", "your-domain.com"]
MAX_UPLOAD_SIZE=100MB

# 性能配置
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
WORKER_TIMEOUT=30
```

### 2. 数据库迁移脚本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 开始部署Chat系统..."

# 1. 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 2. 构建Docker镜像
echo "🏗️ 构建Docker镜像..."
docker-compose -f docker-compose.chat.yml build

# 3. 启动依赖服务
echo "🔧 启动依赖服务..."
docker-compose -f docker-compose.chat.yml up -d postgres redis weaviate minio

# 等待数据库启动
echo "⏳ 等待数据库启动..."
sleep 30

# 4. 运行数据库迁移
echo "📊 运行数据库迁移..."
docker-compose -f docker-compose.chat.yml run --rm chat-api alembic upgrade head

# 5. 初始化向量数据库
echo "🔍 初始化向量数据库..."
docker-compose -f docker-compose.chat.yml run --rm chat-api python scripts/init_weaviate.py

# 6. 启动应用服务
echo "🚀 启动应用服务..."
docker-compose -f docker-compose.chat.yml up -d

# 7. 健康检查
echo "🏥 健康检查..."
sleep 10
if curl -f http://localhost:8000/health; then
    echo "✅ 部署成功！"
else
    echo "❌ 部署失败！"
    exit 1
fi

echo "🎉 Chat系统部署完成！"
```

## 📊 监控配置

### 1. Prometheus配置

```yaml
# config/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  # Chat API监控
  - job_name: 'chat-api'
    static_configs:
      - targets: ['chat-api:8001']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # PostgreSQL监控
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres:5432']

  # Redis监控
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  # Nginx监控
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

  # 系统监控
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. 告警规则

```yaml
# config/prometheus/rules/chat_alerts.yml
groups:
  - name: chat_system_alerts
    rules:
      # API响应时间告警
      - alert: HighAPIResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过高"
          description: "95%的API请求响应时间超过2秒"

      # 错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API错误率过高"
          description: "API错误率超过5%"

      # WebSocket连接数告警
      - alert: HighWebSocketConnections
        expr: websocket_active_connections > 800
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "WebSocket连接数过高"
          description: "活跃WebSocket连接数超过800"

      # 数据库连接告警
      - alert: DatabaseConnectionIssue
        expr: up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
          description: "PostgreSQL数据库无法连接"

      # Redis连接告警
      - alert: RedisConnectionIssue
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis连接失败"
          description: "Redis缓存服务无法连接"

      # 内存使用告警
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "系统内存使用率超过80%"

      # CPU使用告警
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "系统CPU使用率超过80%"
```

### 3. Grafana仪表板

```json
{
  "dashboard": {
    "title": "Chat系统监控面板",
    "panels": [
      {
        "title": "API请求量",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "API响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "WebSocket连接数",
        "type": "singlestat",
        "targets": [
          {
            "expr": "websocket_active_connections",
            "legendFormat": "活跃连接"
          }
        ]
      },
      {
        "title": "消息处理量",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(chat_messages_processed_total[1m])",
            "legendFormat": "消息/秒"
          }
        ]
      },
      {
        "title": "数据库连接池",
        "type": "graph",
        "targets": [
          {
            "expr": "db_pool_size",
            "legendFormat": "连接池大小"
          },
          {
            "expr": "db_pool_checked_out",
            "legendFormat": "已使用连接"
          }
        ]
      },
      {
        "title": "Redis内存使用",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "内存使用"
          }
        ]
      }
    ]
  }
}
```

## 🔍 日志管理

### 1. 日志配置

```python
# config/logging.py
import logging
import sys
from pathlib import Path

def setup_logging(app_env: str = "development"):
    """设置日志配置"""
    
    # 日志格式
    if app_env == "production":
        # 生产环境使用JSON格式
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(name)s", "message": "%(message)s", '
            '"filename": "%(filename)s", "line": %(lineno)d}'
        )
    else:
        # 开发环境使用可读格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 文件处理器
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setFormatter(formatter)
    
    # 错误日志处理器
    error_handler = logging.FileHandler(log_dir / "error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if app_env == "production" else logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # 第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    
    return root_logger
```

### 2. 日志轮转配置

```bash
# /etc/logrotate.d/chat-system
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        docker-compose -f /path/to/docker-compose.chat.yml restart chat-api
    endscript
}
```

## 🚨 故障处理

### 1. 常见问题排查

#### WebSocket连接失败
```bash
# 检查服务状态
docker-compose -f docker-compose.chat.yml ps

# 检查网络连接
docker-compose -f docker-compose.chat.yml exec chat-api netstat -tlnp

# 检查日志
docker-compose -f docker-compose.chat.yml logs chat-api
```

#### 数据库连接问题
```bash
# 检查数据库状态
docker-compose -f docker-compose.chat.yml exec postgres pg_isready

# 查看连接数
docker-compose -f docker-compose.chat.yml exec postgres \
  psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 检查锁定
docker-compose -f docker-compose.chat.yml exec postgres \
  psql -U postgres -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

#### Redis缓存问题
```bash
# 检查Redis状态
docker-compose -f docker-compose.chat.yml exec redis redis-cli ping

# 查看内存使用
docker-compose -f docker-compose.chat.yml exec redis redis-cli info memory

# 检查连接数
docker-compose -f docker-compose.chat.yml exec redis redis-cli info clients
```

### 2. 应急处理脚本

```bash
#!/bin/bash
# scripts/emergency_restart.sh

echo "🚨 执行应急重启..."

# 1. 保存当前状态
echo "📊 保存当前状态..."
docker-compose -f docker-compose.chat.yml ps > /tmp/services_status.txt
docker-compose -f docker-compose.chat.yml logs --tail=100 > /tmp/recent_logs.txt

# 2. 检查关键服务
echo "🔍 检查关键服务..."
if ! curl -f http://localhost:8000/health; then
    echo "❌ API服务异常，执行重启..."
    docker-compose -f docker-compose.chat.yml restart chat-api
fi

if ! docker-compose -f docker-compose.chat.yml exec redis redis-cli ping; then
    echo "❌ Redis服务异常，执行重启..."
    docker-compose -f docker-compose.chat.yml restart redis
fi

if ! docker-compose -f docker-compose.chat.yml exec postgres pg_isready; then
    echo "❌ 数据库服务异常，执行重启..."
    docker-compose -f docker-compose.chat.yml restart postgres
fi

# 3. 等待服务恢复
echo "⏳ 等待服务恢复..."
sleep 30

# 4. 验证服务状态
echo "✅ 验证服务状态..."
if curl -f http://localhost:8000/health; then
    echo "🎉 服务恢复正常！"
else
    echo "❌ 服务仍然异常，请人工介入！"
    exit 1
fi
```

## 📈 性能优化

### 1. 数据库优化

```sql
-- 定期维护脚本
-- scripts/db_maintenance.sql

-- 1. 更新表统计信息
ANALYZE chat_sessions;
ANALYZE chat_messages;
ANALYZE chat_contexts;
ANALYZE chat_references;

-- 2. 重建索引
REINDEX INDEX CONCURRENTLY idx_chat_messages_session_created;
REINDEX INDEX CONCURRENTLY idx_chat_contexts_relevance;

-- 3. 清理过期数据
DELETE FROM chat_streams WHERE created_at < NOW() - INTERVAL '7 days';
DELETE FROM chat_contexts WHERE expires_at < NOW();

-- 4. 优化表
VACUUM ANALYZE chat_messages;
VACUUM ANALYZE chat_sessions;
```

### 2. 缓存策略

```python
# 缓存优化配置
CACHE_STRATEGIES = {
    "session_data": {
        "ttl": 3600,  # 1小时
        "key_pattern": "session:{session_id}"
    },
    "user_sessions": {
        "ttl": 1800,  # 30分钟
        "key_pattern": "user_sessions:{user_id}"
    },
    "document_chunks": {
        "ttl": 7200,  # 2小时
        "key_pattern": "chunks:{document_id}"
    },
    "search_results": {
        "ttl": 900,   # 15分钟
        "key_pattern": "search:{query_hash}"
    }
}
```

### 3. 自动扩缩容

```yaml
# kubernetes/chat-deployment.yml (K8s环境)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-api
  template:
    metadata:
      labels:
        app: chat-api
    spec:
      containers:
      - name: chat-api
        image: chat-api:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chat-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chat-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

这个部署运维指南提供了完整的Chat系统部署方案，包括Docker配置、监控告警、日志管理和故障处理，确保系统的高可用性和稳定运行。


