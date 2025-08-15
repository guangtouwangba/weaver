# RAG 中间件管理指南

本项目使用 Docker Compose 管理所需的中间件服务，包括 PostgreSQL、Weaviate、Redis 等。

## 🚀 快速开始

### 1. 启动核心服务

```bash
# 启动核心服务 (PostgreSQL, Weaviate, Redis)
./scripts/middleware-control.sh start-core

# 或启动所有服务（包括可选服务）
./scripts/middleware-control.sh start-all
```

### 2. 检查服务状态

```bash
# 查看所有服务状态
./scripts/middleware-control.sh status

# 健康检查
./scripts/middleware-control.sh health
```

### 3. 查看连接信息

```bash
./scripts/middleware-control.sh connections
```

## 📦 服务说明

### 核心服务

| 服务 | 端口 | 用途 | 连接信息 |
|------|------|------|----------|
| **PostgreSQL** | 5432 | 主数据库 | `postgresql://rag_user:rag_password@localhost:5432/rag_db` |
| **Weaviate** | 8080 | 向量数据库 | `http://localhost:8080` |
| **Redis** | 6379 | 缓存和会话 | `redis://:redis_password@localhost:6379/0` |

### 可选服务

| 服务 | 端口 | 用途 | 连接信息 |
|------|------|------|----------|
| **Elasticsearch** | 9200 | 全文搜索 | `http://localhost:9200` |
| **MinIO** | 9000/9001 | 对象存储 | `http://localhost:9000` (Console: 9001) |
| **Grafana** | 3000 | 监控面板 | `http://localhost:3000` (admin/admin123) |
| **Prometheus** | 9090 | 指标收集 | `http://localhost:9090` |

## 🛠️ 管理命令

### 基本操作

```bash
# 启动核心服务
./scripts/middleware-control.sh start-core

# 启动所有服务
./scripts/middleware-control.sh start-all

# 停止所有服务
./scripts/middleware-control.sh stop

# 重启服务
./scripts/middleware-control.sh restart

# 查看状态
./scripts/middleware-control.sh status
```

### 日志管理

```bash
# 查看所有服务日志
./scripts/middleware-control.sh logs

# 查看特定服务日志
./scripts/middleware-control.sh logs postgres
./scripts/middleware-control.sh logs weaviate
./scripts/middleware-control.sh logs redis
```

### 数据管理

```bash
# 备份数据
./scripts/middleware-control.sh backup

# 清理所有数据（谨慎使用！）
./scripts/middleware-control.sh clean
```

## 🔧 配置文件

### 环境变量
- `.env.middleware` - 中间件连接配置

### 配置文件
- `config/redis.conf` - Redis 配置
- `config/prometheus/prometheus.yml` - Prometheus 配置
- `scripts/init-db/001_init_tables.sql` - PostgreSQL 初始化脚本

## 📊 数据库结构

PostgreSQL 数据库包含以下表：

- `documents` - 文档元数据
- `document_chunks` - 文档块
- `query_history` - 查询历史
- `user_sessions` - 用户会话

## 🔍 监控和调试

### 1. 健康检查
```bash
./scripts/middleware-control.sh health
```

### 2. 查看服务日志
```bash
# 实时查看 PostgreSQL 日志
./scripts/middleware-control.sh logs postgres

# 实时查看 Weaviate 日志
./scripts/middleware-control.sh logs weaviate
```

### 3. 直接连接服务

#### PostgreSQL
```bash
# 使用 psql 连接
docker exec -it rag-postgres psql -U rag_user -d rag_db

# 或使用图形工具连接
# Host: localhost, Port: 5432, DB: rag_db, User: rag_user, Password: rag_password
```

#### Redis
```bash
# 使用 redis-cli 连接
docker exec -it rag-redis redis-cli -a redis_password
```

#### Weaviate
```bash
# 检查 Weaviate 状态
curl http://localhost:8080/v1/.well-known/ready

# 查看 schema
curl http://localhost:8080/v1/schema
```

## 🚨 故障排除

### 1. 端口冲突
如果遇到端口冲突，修改 `docker-compose.middleware.yaml` 中的端口映射：

```yaml
ports:
  - "15432:5432"  # 将 PostgreSQL 端口改为 15432
```

### 2. 内存不足
对于 Elasticsearch，确保 Docker 有足够内存（至少 4GB）：

```bash
# 检查 Docker 内存限制
docker system info | grep Memory
```

### 3. 数据持久化问题
数据存储在 Docker volumes 中，检查卷状态：

```bash
# 查看所有卷
docker volume ls

# 查看特定卷详情
docker volume inspect rag_postgres_data
```

## 🔒 安全注意事项

1. **生产环境部署**：
   - 修改所有默认密码
   - 启用 SSL/TLS
   - 配置防火墙规则

2. **密码管理**：
   - 使用环境变量管理敏感信息
   - 不要在代码中硬编码密码

3. **网络安全**：
   - 限制服务绑定的网络接口
   - 使用 Docker 网络隔离

## 📝 开发建议

1. **本地开发**：
   - 只启动核心服务以节省资源
   - 使用 `start-core` 命令

2. **测试环境**：
   - 启动所有服务进行完整测试
   - 定期备份测试数据

3. **生产环境**：
   - 使用专用的生产配置
   - 配置监控和告警
   - 定期备份数据