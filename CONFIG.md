# 配置说明文档

## 概述

RAG 知识管理系统使用统一的配置管理，支持通过环境变量和 `.env` 文件进行配置。

## 快速开始

1. **复制配置模板**
   ```bash
   cp env.example .env
   ```

2. **编辑配置文件**
   ```bash
   nano .env
   ```

3. **根据环境修改配置值**

## 配置结构

### 应用基础配置
- `APP_NAME`: 应用名称
- `APP_VERSION`: 应用版本
- `DEBUG`: 调试模式 (true/false)
- `HOST`: 服务器主机地址
- `PORT`: 服务器端口
- `ENVIRONMENT`: 运行环境 (development/testing/staging/production)

### 数据库配置
支持两种配置方式：

**方式1：使用 DATABASE_URL**
```bash
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ragdb
```

**方式2：使用详细配置**
```bash
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=ragdb
DATABASE__USER=myuser
DATABASE__PASSWORD=mypassword
DATABASE__DRIVER=asyncpg
```

### Redis 配置
```bash
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__DB=0
REDIS__PASSWORD=your-redis-password
```

### Celery 配置
```bash
CELERY__BROKER_URL=redis://localhost:6379/0
CELERY__RESULT_BACKEND=redis://localhost:6379/1
CELERY__WORKER_CONCURRENCY=4
```

### 存储配置
支持多种存储后端：

**本地存储**
```bash
STORAGE__PROVIDER=local
STORAGE__LOCAL_PATH=./storage
```

**MinIO**
```bash
STORAGE__PROVIDER=minio
STORAGE__MINIO_ENDPOINT=localhost:9000
STORAGE__MINIO_ACCESS_KEY=minioadmin
STORAGE__MINIO_SECRET_KEY=minioadmin123
```

**AWS S3**
```bash
STORAGE__PROVIDER=s3
STORAGE__AWS_ACCESS_KEY_ID=your-access-key
STORAGE__AWS_SECRET_ACCESS_KEY=your-secret-key
STORAGE__AWS_REGION=us-east-1
```

## 环境变量命名规则

系统使用 `__` 双下划线来分隔嵌套配置：

- `DATABASE__HOST` → `config.database.host`
- `REDIS__PASSWORD` → `config.redis.password`
- `CELERY__BROKER_URL` → `config.celery.broker_url`

## 配置验证

启动应用时会自动验证配置：

```python
from config import get_config

config = get_config()
print(f"应用: {config.app_name}")
print(f"环境: {config.environment}")
print(f"数据库: {config.database.url}")
print(f"Redis: {config.redis.url}")
```

## 环境特定配置

### 开发环境
```bash
ENVIRONMENT=development
DEBUG=true
LOGGING__LEVEL=DEBUG
```

### 生产环境
```bash
ENVIRONMENT=production
DEBUG=false
LOGGING__LEVEL=INFO
DATABASE__POOL_SIZE=20
REDIS__MAX_CONNECTIONS=100
```

## 安全注意事项

1. **永远不要提交 `.env` 文件到版本控制**
2. **生产环境必须设置强密码**
3. **使用环境变量管理敏感信息**
4. **定期轮换密钥和令牌**

## 配置示例

### 完整的开发环境配置
```bash
# 应用配置
APP_NAME=RAG API
DEBUG=true
ENVIRONMENT=development
PORT=8000

# 数据库配置
DATABASE__HOST=localhost
DATABASE__NAME=ragdb_dev
DATABASE__USER=dev_user
DATABASE__PASSWORD=dev_password

# Redis配置
REDIS__HOST=localhost
REDIS__PASSWORD=dev_redis_pass

# Celery配置
CELERY__BROKER_URL=redis://localhost:6379/0
CELERY__RESULT_BACKEND=redis://localhost:6379/1

# 存储配置
STORAGE__PROVIDER=local
STORAGE__LOCAL_PATH=./dev_storage
```

### Docker Compose 配置
```bash
# 数据库配置
DATABASE__HOST=postgres
DATABASE__NAME=ragdb
DATABASE__USER=postgres
DATABASE__PASSWORD=postgres123

# Redis配置
REDIS__HOST=redis
REDIS__PASSWORD=redis123

# Celery配置
CELERY__BROKER_URL=redis://redis:6379/0
CELERY__RESULT_BACKEND=redis://redis:6379/1

# 存储配置
STORAGE__PROVIDER=minio
STORAGE__MINIO_ENDPOINT=minio:9000
STORAGE__MINIO_ACCESS_KEY=minioadmin
STORAGE__MINIO_SECRET_KEY=minioadmin123
```

## 故障排除

### 配置加载失败
```python
# 检查配置是否正确加载
from config import get_config
try:
    config = get_config()
    print("配置加载成功")
except Exception as e:
    print(f"配置加载失败: {e}")
```

### 数据库连接问题
```python
# 检查数据库配置
config = get_config()
print(f"数据库URL: {config.database.url}")
```

### Redis 连接问题
```python
# 检查Redis配置
config = get_config()
print(f"Redis URL: {config.redis.url}")
```

## 配置热重载

开发环境支持配置热重载：

```python
from config import reload_config

# 修改环境变量后重新加载
config = reload_config()
```

## 高级配置

### 自定义配置验证
系统会自动验证配置的合法性，如数据库驱动、存储提供商等。

### 配置继承
不同环境可以继承基础配置，只需要覆盖特定的值。

### 动态配置
某些配置支持运行时动态修改，如日志级别、任务并发数等。
