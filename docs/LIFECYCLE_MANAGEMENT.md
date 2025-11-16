# RAG 系统生命周期管理文档

## 概述

本文档介绍 RAG 系统的生命周期管理实现，包括模块启动、关闭、健康检查和依赖注入。

## 🏗️ 架构设计

### 核心组件

1. **ApplicationState** (`app/lifecycle.py`)
   - 集中管理所有系统组件
   - 处理初始化和清理逻辑
   - 提供组件状态查询

2. **Lifespan Context Manager**
   - FastAPI 生命周期事件管理
   - 确保资源正确初始化和清理
   - 异常处理和日志记录

3. **Health Check Endpoints** (`app/routers/health.py`)
   - `/health` - 详细健康检查
   - `/ready` - Kubernetes readiness probe
   - `/live` - Kubernetes liveness probe
   - `/startup` - Kubernetes startup probe
   - `/status` - 系统状态详情

4. **Dependency Injection** (`app/dependencies.py`)
   - 组件依赖注入
   - 统一错误处理
   - 向后兼容支持

## 📋 配置管理

### 模块开关

所有模块都可以通过环境变量配置启用/禁用：

```bash
# Cache (Redis)
CACHE_ENABLED=false
REDIS_URL=redis://localhost:6379

# Reranker
RERANKER_ENABLED=false
RERANKER_TYPE=cross_encoder

# LangSmith Tracing
LANGSMITH_ENABLED=false
LANGCHAIN_API_KEY=lsv2_xxx
LANGCHAIN_PROJECT=rag-production

# Prometheus Metrics
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=9090
```

详细配置请参考 `env.example` 文件。

## 🚀 启动流程

### 初始化顺序

系统按以下顺序初始化组件：

```
1. 📋 加载配置 (AppSettings)
2. 🤖 初始化 LLM 和 Embeddings
3. 🗄️  初始化向量存储 (Vector Store)
4. 🔴 初始化 Redis (如果启用)
5. 🎯 初始化重排序器 (如果启用)
6. 🔍 初始化 LangSmith (如果启用)
7. 📊 初始化 Prometheus (如果启用)
```

### 启动日志示例

```
================================================================================
🚀 开始初始化 RAG 系统模块...
================================================================================
📋 加载配置...
   ├─ 环境: development
   ├─ LLM Provider: openrouter
   └─ Embedding Provider: openrouter
🤖 初始化 LLM 和 Embeddings...
   ├─ LLM: openai/gpt-3.5-turbo
   └─ Embeddings: openai/text-embedding-3-small
🗄️  初始化向量存储...
   ✅ 向量存储加载成功 (路径: ./data/vector_store)
🔴 初始化 Redis 缓存...
   ✅ Redis 连接成功 (redis://localhost:6379)
🔍 初始化 LangSmith 追踪...
   ✅ LangSmith 已启用 (项目: rag-production)
================================================================================
✅ RAG 系统所有模块初始化完成！
================================================================================

📊 系统组件状态:
   ├─ LLM: ✅ 已加载
   ├─ Embeddings: ✅ 已加载
   ├─ 向量存储: ✅ 已加载
   ├─ Redis 缓存: ✅ 已连接
   ├─ 重排序器: ❌ 未启用
   ├─ LangSmith: ✅ 已启用
   └─ Prometheus: ❌ 未启用
```

## 🧹 关闭流程

### 清理顺序

系统按**相反顺序**清理组件，确保依赖关系正确：

```
1. 📊 清理 Prometheus
2. 🔍 清理 LangSmith
3. 🎯 清理重排序器
4. 🔴 关闭 Redis 连接
5. 🗄️  清理向量存储
6. 🤖 清理 LLM 和 Embeddings
```

### 优雅关闭

系统支持优雅关闭（Graceful Shutdown）：

- 接收 SIGTERM/SIGINT 信号
- 完成当前正在处理的请求
- 清理所有资源
- 记录清理日志

## 🏥 健康检查

### 端点说明

#### 1. `/health` - 详细健康检查

返回所有组件的详细状态：

```bash
curl http://localhost:8000/health
```

响应示例：

```json
{
  "status": "healthy",
  "version": "0.3.0",
  "environment": "development",
  "components": {
    "llm": {
      "status": "up",
      "provider": "openrouter",
      "model": "openai/gpt-3.5-turbo"
    },
    "embeddings": {
      "status": "up",
      "provider": "openrouter",
      "model": "openai/text-embedding-3-small"
    },
    "vector_store": {
      "status": "up",
      "path": "./data/vector_store"
    },
    "redis": {
      "status": "up",
      "url": "redis://localhost:6379"
    },
    "database": {
      "status": "up",
      "type": "PostgreSQL"
    },
    "reranker": {
      "status": "disabled"
    },
    "langsmith": {
      "status": "enabled",
      "project": "rag-production"
    },
    "prometheus": {
      "status": "disabled"
    }
  }
}
```

#### 2. `/ready` - Kubernetes Readiness Probe

检查关键组件是否就绪：

```bash
curl http://localhost:8000/ready
```

返回 200 表示就绪，503 表示未就绪。

#### 3. `/live` - Kubernetes Liveness Probe

简单的存活检查：

```bash
curl http://localhost:8000/live
```

始终返回 200（除非进程崩溃）。

#### 4. `/startup` - Kubernetes Startup Probe

检查初始化是否完成：

```bash
curl http://localhost:8000/startup
```

#### 5. `/status` - 系统状态详情

获取技术详情和配置信息：

```bash
curl http://localhost:8000/status
```

### Kubernetes 配置示例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: rag-api:latest
        ports:
        - containerPort: 8000
        
        # 启动探针 - 给予足够时间初始化
        startupProbe:
          httpGet:
            path: /startup
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 30  # 最多等待 150 秒
        
        # 就绪探针 - 确定服务可以接收流量
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          failureThreshold: 3
        
        # 存活探针 - 检测服务是否还活着
        livenessProbe:
          httpGet:
            path: /live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          failureThreshold: 3
        
        # 优雅关闭
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
```

## 💉 依赖注入使用

### 在路由中使用

#### 方法 1: 使用新的依赖注入（推荐）

```python
from fastapi import APIRouter, Depends
from typing import Annotated

from app.dependencies import (
    get_app_state,
    get_settings_from_state,
    get_vector_store_from_state,
    get_llm_from_state,
    get_redis_client,
)

router = APIRouter()

@router.post("/query")
async def query(
    request: QueryRequest,
    # 注入各个组件
    settings: Annotated[AppSettings, Depends(get_settings_from_state)],
    vector_store = Depends(get_vector_store_from_state),
    llm = Depends(get_llm_from_state),
):
    # 使用注入的组件
    docs = vector_store.similarity_search(request.query, k=settings.retriever.top_k)
    answer = llm(format_prompt(request.query, docs))
    return {"answer": answer}
```

#### 方法 2: 直接使用 ApplicationState

```python
from app.lifecycle import ApplicationState

@router.post("/query")
async def query(
    request: QueryRequest,
    state: Annotated[ApplicationState, Depends(get_app_state)],
):
    # 直接访问所有组件
    if not state.vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    
    # 使用组件
    docs = state.vector_store.similarity_search(request.query)
    answer = state.llm(format_prompt(request.query, docs))
    
    # 如果 Redis 可用，尝试缓存
    if state.redis_client:
        await state.redis_client.set(cache_key, answer, ex=3600)
    
    return {"answer": answer}
```

#### 方法 3: 可选依赖（Redis, Reranker）

```python
from typing import Annotated, Optional
from app.dependencies import get_redis_client, get_reranker

@router.post("/query")
async def query(
    request: QueryRequest,
    state: Annotated[ApplicationState, Depends(get_app_state)],
):
    # Redis 可选，不可用时不会报错
    cache_key = f"query:{hash(request.query)}"
    
    # 尝试从缓存获取
    if state.redis_client:
        try:
            cached = await state.redis_client.get(cache_key)
            if cached:
                return {"answer": cached, "from_cache": True}
        except Exception as e:
            logger.warning(f"Redis error: {e}")
    
    # 正常处理...
    docs = state.vector_store.similarity_search(request.query)
    
    # 如果重排序器可用，使用它
    if state.reranker:
        docs = await state.reranker.rerank(request.query, docs)
    
    answer = state.llm(format_prompt(request.query, docs))
    
    # 缓存结果
    if state.redis_client:
        try:
            await state.redis_client.set(cache_key, answer, ex=3600)
        except Exception as e:
            logger.warning(f"Failed to cache: {e}")
    
    return {"answer": answer, "from_cache": False}
```

## 🔧 开发模式 vs 生产模式

### 开发模式配置

```bash
# .env.development
APP_ENV=development
LLM_PROVIDER=fake
EMBEDDING_PROVIDER=fake
CACHE_ENABLED=false
LANGSMITH_ENABLED=false
PROMETHEUS_ENABLED=false
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### 生产模式配置

```bash
# .env.production
APP_ENV=production
LLM_PROVIDER=openrouter
EMBEDDING_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxx

# 启用所有功能
CACHE_ENABLED=true
REDIS_URL=redis://redis-cluster:6379

RERANKER_ENABLED=true
RERANKER_TYPE=cross_encoder

LANGSMITH_ENABLED=true
LANGCHAIN_API_KEY=lsv2_xxx

PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🐛 故障排查

### 常见问题

#### 1. 系统初始化失败

**症状**: `/ready` 返回 503，`/health` 显示 "not_initialized"

**排查步骤**:
1. 检查日志中的初始化错误
2. 确认所有必需的环境变量已设置
3. 验证外部服务（数据库、Redis）是否可达
4. 检查 API keys 是否有效

#### 2. Redis 连接失败

**症状**: `redis: {"status": "down"}`

**解决方案**:
```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 测试连接
redis-cli -h localhost -p 6379 ping

# 如果不需要 Redis，禁用它
CACHE_ENABLED=false
```

#### 3. 向量存储为空

**症状**: `vector_store: {"status": "empty"}`

**这是正常的**，表示还没有导入文档：

```bash
# 导入文档
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@document.pdf"
```

#### 4. LLM 初始化失败

**症状**: `llm: {"status": "down"}`

**排查步骤**:
1. 检查 `LLM_PROVIDER` 配置
2. 验证 API key 是否设置
3. 测试 API 连通性

```python
# 测试 LLM 连接
from rag_core.chains.llm import build_llm
from shared_config.settings import AppSettings

settings = AppSettings()
llm = build_llm(settings)
response = llm("Hello")
print(response)
```

## 📈 监控建议

### 关键指标

1. **初始化时间**: 从启动到 `/ready` 返回 200 的时间
2. **组件可用性**: 各组件的 up/down 状态
3. **Redis 连接池**: 活跃连接数
4. **内存使用**: ApplicationState 占用的内存

### Prometheus 指标（待实现）

```python
# 示例指标
rag_component_status{component="llm"} 1  # 1=up, 0=down
rag_component_status{component="redis"} 1
rag_initialization_duration_seconds 2.34
rag_requests_total{endpoint="/query"} 1234
```

## 🚢 部署检查清单

部署前确认：

- [ ] 所有必需的环境变量已配置
- [ ] 外部服务（PostgreSQL, Redis）可达
- [ ] API keys 有效且有足够配额
- [ ] 健康检查端点正常工作
- [ ] 日志级别设置正确（生产用 INFO）
- [ ] 资源限制配置合理（内存、CPU）
- [ ] 优雅关闭时间足够（建议 30-60 秒）

## 📚 相关文档

- [ROADMAP.md](./architecture/ROADMAP.md) - 系统实施路线图
- [env.example](../env.example) - 配置示例
- [docker-compose.yml](../docker-compose.yml) - Docker 部署配置

## 🎯 下一步

现在系统已经有完善的生命周期管理，建议：

1. 实施 Redis 缓存功能
2. 实施 Prometheus 指标收集
3. 实施 LangSmith 追踪
4. 完善重排序器实现

每个功能都可以通过配置独立启用，不影响其他功能！

