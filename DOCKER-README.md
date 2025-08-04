# Docker 部署指南

## 🚀 快速开始

### 1. 使用 Docker Compose（推荐）

```bash
# 启动服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 使用 Docker 命令

```bash
# 构建镜像
docker build -t arxiv-paper-fetcher .

# 运行容器
docker run -d \
  --name arxiv-fetcher \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/papers.db:/app/papers.db \
  -v $(pwd)/downloaded_papers:/app/downloaded_papers \
  -v $(pwd)/logs:/app/logs \
  arxiv-paper-fetcher
```

## 📁 卷挂载说明

### 必需的挂载：
- `config.yaml` - 配置文件（只读）
- `papers.db` - 数据库文件（读写）
- `downloaded_papers/` - PDF存储目录
- `logs/` - 日志目录

### 示例目录结构：
```
your-host-directory/
├── config.yaml              # 配置文件
├── papers.db                 # 数据库（自动创建）
├── downloaded_papers/        # PDF文件
│   └── 2025-08-04/
└── logs/                     # 日志文件
    └── paper_fetcher.log
```

## 🎛️ 运行模式

### 默认模式：调度器
```bash
docker run arxiv-paper-fetcher
# 或明确指定
docker run arxiv-paper-fetcher scheduler
```

### 单次运行模式
```bash
docker run arxiv-paper-fetcher once
```

### 测试模式
```bash
docker run arxiv-paper-fetcher test
```

### 交互模式
```bash
docker run -it arxiv-paper-fetcher bash
```

## ⚙️ 环境变量

```yaml
environment:
  - PYTHONPATH=/app
  - PYTHONUNBUFFERED=1
  - TZ=Asia/Shanghai        # 设置时区
```

## 📊 监控和健康检查

### 查看容器状态
```bash
docker ps
docker inspect arxiv-fetcher
```

### 查看健康检查
```bash
docker exec arxiv-fetcher python -c "import sqlite3; conn = sqlite3.connect('papers.db'); print('DB OK')"
```

### 查看日志
```bash
# Docker logs
docker logs -f arxiv-fetcher

# 应用日志
docker exec arxiv-fetcher tail -f logs/paper_fetcher.log
```

## 🔄 更新和维护

### 更新容器
```bash
# 停止旧容器
docker-compose down

# 重新构建
docker-compose build

# 启动新容器
docker-compose up -d
```

### 数据备份
```bash
# 备份数据库
docker exec arxiv-fetcher sqlite3 papers.db ".backup /app/papers_backup.db"
docker cp arxiv-fetcher:/app/papers_backup.db ./papers_backup.db

# 备份配置
cp config.yaml config_backup.yaml
```

## 🐛 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker logs arxiv-fetcher
   
   # 检查配置文件
   docker run --rm -v $(pwd)/config.yaml:/app/config.yaml arxiv-paper-fetcher test
   ```

2. **权限问题**
   ```bash
   # 修复文件权限
   sudo chown -R $USER:$USER downloaded_papers papers.db logs
   ```

3. **网络问题**
   ```bash
   # 测试网络连接
   docker exec arxiv-fetcher curl -I https://arxiv.org
   ```

4. **磁盘空间不足**
   ```bash
   # 检查磁盘使用
   df -h
   
   # 清理Docker
   docker system prune -a
   ```

### 调试命令

```bash
# 进入容器调试
docker exec -it arxiv-fetcher bash

# 查看进程
docker exec arxiv-fetcher ps aux

# 查看Python环境
docker exec arxiv-fetcher python --version
docker exec arxiv-fetcher pip list
```

## 📈 性能优化

### 资源限制
```yaml
services:
  paper-fetcher:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### 日志轮转
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔐 安全建议

1. **使用非root用户**（已配置）
2. **只读挂载配置文件**
3. **限制容器权限**
4. **定期更新基础镜像**

```bash
# 定期重构建镜像
docker build --no-cache -t arxiv-paper-fetcher .
```

## 📝 配置示例

### 最小配置 `config.yaml`
```yaml
database:
  url: "sqlite:///papers.db"

search:
  keywords:
    - "machine learning"
    - "artificial intelligence"
  max_papers_per_run: 50
  days_back: 7

scheduler:
  interval_hours: 24
  run_on_startup: true

logging:
  level: "INFO"
  file: "logs/paper_fetcher.log"

pdf_storage:
  base_directory: "./downloaded_papers"
  create_subdirectories: true

advanced:
  request_delay: 1.0
  download_timeout: 300
```

## 🚀 生产部署

### 使用 Docker Swarm
```bash
docker swarm init
docker stack deploy -c docker-compose.yml arxiv-stack
```

### 使用 Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxiv-paper-fetcher
spec:
  replicas: 1
  selector:
    matchLabels:
      app: arxiv-paper-fetcher
  template:
    metadata:
      labels:
        app: arxiv-paper-fetcher
    spec:
      containers:
      - name: arxiv-fetcher
        image: arxiv-paper-fetcher:latest
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: data
          mountPath: /app/papers.db
          subPath: papers.db
        - name: downloads
          mountPath: /app/downloaded_papers
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: arxiv-config
      - name: data
        persistentVolumeClaim:
          claimName: arxiv-data
      - name: downloads
        persistentVolumeClaim:
          claimName: arxiv-downloads
      - name: logs
        persistentVolumeClaim:
          claimName: arxiv-logs
```