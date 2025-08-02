# Celery异步任务系统配置指南

本文档说明如何配置和运行Research Agent RAG系统的Celery异步任务系统。

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │  Celery Worker  │
│   (React)       │────│   (FastAPI)     │────│   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Redis Broker  │
                    │  (Message Queue)│
                    └─────────────────┘
```

## 📋 前置要求

1. **Docker & Docker Compose** (推荐)
2. **Redis** (消息代理)
3. **PostgreSQL** (数据库)
4. **Python 3.9+** (本地开发)

## 🚀 快速启动

### 方法1: 使用Docker (推荐)

```bash
# 1. 启动完整的Celery环境
./start-celery.sh

# 2. 或者只启动开发环境
./start-dev-celery.sh
```

### 方法2: 本地开发

```bash
# 1. 启动基础服务
docker-compose -f infra/docker/docker-compose.middleware.yml up -d postgres redis

# 2. 设置环境变量
export POSTGRES_URL='postgresql://research_user:research_password@localhost:5433/research_agent'
export REDIS_URL='redis://:redis_password@localhost:6379/0'
export CELERY_BROKER_URL='redis://:redis_password@localhost:6379/0'
export CELERY_RESULT_BACKEND='redis://:redis_password@localhost:6379/0'

# 3. 启动后端API
cd backend
python -m uvicorn api.simple_server:app --reload --host 0.0.0.0 --port 8000

# 4. 启动Celery Worker
cd backend
celery -A celery_app worker --loglevel=info --concurrency=2 -Q research,processing

# 5. 启动前端 (新终端)
cd frontend
npm run dev
```

## 🔧 环境配置

### 环境变量配置

复制并编辑环境配置文件：

```bash
cp infra/docker/env.template .env
```

关键的Celery配置项：

```bash
# Celery配置
CELERY_BROKER_URL=redis://:redis_password@redis:6379/0
CELERY_RESULT_BACKEND=redis://:redis_password@redis:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_RESULT_SERIALIZER=json

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password
REDIS_DB=0
```

## 📊 监控和管理

### 1. Celery Flower (推荐)

Flower是Celery的Web管理界面：

```bash
# 启动Flower
docker-compose -f infra/docker/docker-compose.yml --profile monitoring up -d

# 访问: http://localhost:5555
# 用户名: admin
# 密码: flower_password
```

### 2. Redis监控

```bash
# 启动Redis Commander
docker-compose -f infra/docker/docker-compose.middleware.yml --profile admin up -d

# 访问: http://localhost:8081
```

### 3. 命令行监控

```bash
# 查看Celery Worker状态
celery -A celery_app inspect active

# 查看注册的任务
celery -A celery_app inspect registered

# 查看Worker统计信息
celery -A celery_app inspect stats
```

## 🎯 任务队列配置

系统使用以下队列：

- **`research`**: 研究任务 (论文搜索、分析)
- **`processing`**: 处理任务 (嵌入、向量化)
- **`default`**: 默认任务队列

### 启动特定队列的Worker

```bash
# 只处理research队列
celery -A celery_app worker -Q research --loglevel=info

# 处理多个队列
celery -A celery_app worker -Q research,processing --loglevel=info

# 启动多个Worker实例
celery -A celery_app worker --concurrency=4 --loglevel=info
```

## 🐛 故障排除

### 常见问题

#### 1. "Celery app not available - tasks will not be registered"

**原因**: Redis连接失败或Celery配置错误

**解决方案**:
```bash
# 检查Redis是否运行
docker-compose -f infra/docker/docker-compose.middleware.yml ps redis

# 检查Redis连接
docker-compose -f infra/docker/docker-compose.middleware.yml exec redis redis-cli ping

# 重启Redis
docker-compose -f infra/docker/docker-compose.middleware.yml restart redis
```

#### 2. "Connection refused" 错误

**原因**: Redis服务未启动或端口配置错误

**解决方案**:
```bash
# 确保Redis服务运行
docker-compose -f infra/docker/docker-compose.middleware.yml up -d redis

# 检查端口映射
docker port research-agent-redis
```

#### 3. Worker无法启动

**原因**: 导入错误或依赖缺失

**解决方案**:
```bash
# 检查Python路径
cd backend && python -c "import celery_app; print('Import OK')"

# 检查任务导入
cd backend && python -c "from tasks.research_tasks import execute_research_job; print('Tasks OK')"

# 重建Docker镜像
docker-compose -f infra/docker/docker-compose.yml build celery-worker
```

#### 4. 任务执行失败

查看详细日志：
```bash
# Worker日志
docker logs research-agent-celery-worker -f

# 应用日志
docker logs research-agent-backend -f

# Redis日志
docker logs research-agent-redis -f
```

## 📈 性能优化

### Worker配置优化

```bash
# 调整并发数 (CPU密集型任务)
celery -A celery_app worker --concurrency=2

# 调整预取数量
celery -A celery_app worker --prefetch-multiplier=1

# 内存限制
celery -A celery_app worker --max-memory-per-child=200000
```

### Redis配置优化

在`.env`文件中：
```bash
# Redis内存优化
REDIS_MAXMEMORY=256mb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# 连接池优化
REDIS_POOL_SIZE=10
REDIS_POOL_TIMEOUT=30
```

## 🔄 任务重试机制

系统配置了自动重试机制：

- **默认重试延迟**: 60秒
- **最大重试次数**: 3次
- **指数退避**: 支持

在任务中自定义重试：
```python
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def my_task(self):
    # 任务逻辑
    pass
```

## 📝 日志配置

Celery任务日志会自动记录到：
- **Elasticsearch**: 结构化日志搜索
- **文件系统**: `logs/`目录
- **Docker日志**: `docker logs`命令

查看实时日志：
```bash
# Celery Worker日志
docker logs research-agent-celery-worker -f

# 查看特定任务日志
# 在Kibana中搜索: http://localhost:5601
```

## 🔒 安全考虑

1. **Redis密码保护**: 默认已配置密码
2. **网络隔离**: 使用Docker网络
3. **任务参数验证**: 任务执行前验证输入
4. **结果过期**: 任务结果自动过期清理

## 📚 扩展阅读

- [Celery官方文档](https://docs.celeryproject.org/)
- [Redis官方文档](https://redis.io/documentation)
- [Flower监控文档](https://flower.readthedocs.io/)
- [Docker Compose参考](https://docs.docker.com/compose/)

## 🆘 获取帮助

如果遇到问题：

1. 检查服务状态: `docker-compose ps`
2. 查看日志: `docker logs <container_name> -f`
3. 检查网络连接: `docker network ls`
4. 重启服务: `docker-compose restart <service_name>`

---

**注意**: 首次启动时请确保在`.env`文件中配置正确的API密钥 (OpenAI, DeepSeek, Anthropic)。