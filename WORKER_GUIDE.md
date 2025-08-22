# Worker 使用指南 - 架构优化版

## 📋 概述

本指南介绍了架构优化后的 Celery Worker 系统，支持任务分离和专用 Worker 配置。

## 🏗️ 架构概览

### 队列设计

| 队列名称 | 用途 | 任务类型 | 推荐并发数 |
|---------|------|----------|------------|
| `document_queue` | 文档创建和管理 | `document.create`, `document.update_metadata` | 4 |
| `rag_queue` | RAG处理 | `rag.process_document_async`, `rag.*` | 2 |
| `file_queue` | 文件处理 | `file.*`, 上传完成处理 | 3 |
| `workflow_queue` | 工作流协调 | 工作流管理任务 | 2 |
| `default` | 通用任务 | 其他任务 | 2 |
| `notification_queue` | 通知任务 | 通知相关 | 1 |

### 任务分离

```
文件上传 → 文件处理 → 文档创建 → RAG处理 → 状态更新
    ↓           ↓          ↓          ↓          ↓
file_queue  file_queue  document_queue  rag_queue  document_queue
```

## 🚀 快速开始

### 1. 基本启动

```bash
# 启动通用 Worker（监听所有队列）
python worker.py

# 使用启动脚本
./start_workers.sh --all
```

### 2. 专用 Worker

```bash
# 启动专用文档处理 Worker
python worker.py --specialized=document

# 启动专用 RAG 处理 Worker  
python worker.py --specialized=rag

# 启动专用文件处理 Worker
python worker.py --specialized=file

# 启动专用工作流协调 Worker
python worker.py --specialized=workflow
```

### 3. 多 Worker 部署（推荐生产环境）

```bash
# 一键启动所有专用 Workers
./start_workers.sh --multi

# 或手动启动
python worker.py --specialized=document --concurrency=4 &
python worker.py --specialized=rag --concurrency=2 &
python worker.py --specialized=file --concurrency=3 &
python worker.py --specialized=workflow --concurrency=2 &
```

## 📝 命令行选项

### worker.py 选项

```bash
python worker.py [选项]

选项:
  --loglevel LEVEL        日志级别 (debug/info/warning/error)
  --concurrency N         并发数
  --queues QUEUES         自定义队列，逗号分隔
  --specialized TYPE      专用Worker类型 (document/rag/file/workflow)
  --max-tasks-per-child N 每个进程最大任务数
  --pool TYPE             Worker池类型 (prefork/eventlet/gevent/solo)
```

### 启动脚本选项

```bash
./start_workers.sh [选项]

选项:
  -h, --help              显示帮助信息
  -c, --check             检查环境配置
  -a, --all              启动通用Worker
  -d, --document         启动专用文档处理Worker
  -r, --rag              启动专用RAG处理Worker
  -f, --file             启动专用文件处理Worker
  -w, --workflow         启动专用工作流协调Worker
  -m, --multi            启动多个专用Worker
  -s, --status           显示Worker状态
  -k, --kill             停止所有Worker

高级选项:
  --concurrency N        设置并发数
  --loglevel LEVEL       设置日志级别
  --queues QUEUES        自定义队列
```

## 📊 监控

### 实时监控

```bash
# 启动实时监控面板
python monitor_workers.py

# 自定义监控间隔
python monitor_workers.py --interval=10

# 单次状态检查
python monitor_workers.py --once

# JSON格式输出
python monitor_workers.py --once --json
```

### 使用启动脚本监控

```bash
# 查看Worker状态
./start_workers.sh --status

# 停止所有Worker
./start_workers.sh --kill
```

## 🔧 配置优化

### 生产环境推荐配置

#### 高吞吐量场景

```bash
# 文档处理Worker（高并发）
python worker.py --specialized=document --concurrency=8 --pool=prefork

# RAG处理Worker（低并发，高资源）
python worker.py --specialized=rag --concurrency=2 --pool=prefork

# 文件处理Worker（中等并发）
python worker.py --specialized=file --concurrency=4 --pool=prefork
```

#### 低资源环境

```bash
# 通用Worker（低并发）
python worker.py --concurrency=2 --pool=prefork
```

#### 高并发I/O场景

```bash
# 使用事件驱动池
python worker.py --pool=eventlet --concurrency=100
```

### 配置文件调优

在 `config/settings.py` 中调整 Celery 配置：

```python
# Celery 配置
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
```

## 📈 性能监控

### 关键指标

1. **队列长度** - 监控待处理任务数量
2. **Worker负载** - CPU和内存使用率
3. **任务执行时间** - 平均处理时间
4. **错误率** - 任务失败比例

### 监控命令

```bash
# 查看队列状态
python -c "
from celery import Celery
from config import get_config
config = get_config()
app = Celery(config.celery.app_name, broker=config.celery.broker_url)
inspect = app.control.inspect()
print('队列状态:', inspect.active())
"

# 查看Worker统计
python monitor_workers.py --once --json | jq '.worker_stats'
```

## 🚨 故障排除

### 常见问题

#### 1. Worker 启动失败

```bash
# 检查环境
./start_workers.sh --check

# 检查日志
tail -f logs/worker_*.log
```

#### 2. 任务堆积

```bash
# 检查队列状态
python monitor_workers.py --once

# 增加Worker数量
python worker.py --specialized=rag --concurrency=4
```

#### 3. 内存泄漏

```bash
# 设置最大任务数
python worker.py --max-tasks-per-child=500
```

#### 4. 连接问题

```bash
# 检查Redis连接
python -c "
import redis
from config import get_config
config = get_config()
r = redis.from_url(config.celery.broker_url)
print(r.ping())
"
```

### 日志分析

```bash
# 查看错误日志
grep -i error logs/worker_*.log

# 监控任务执行时间
grep "execution time" logs/worker_*.log

# 查看任务路由
grep "routing" logs/worker_*.log
```

## 🔄 部署策略

### 单机部署

```bash
# 启动多个专用Worker
./start_workers.sh --multi
```

### 多机部署

```bash
# 机器1：文档和文件处理
python worker.py --specialized=document --concurrency=4
python worker.py --specialized=file --concurrency=3

# 机器2：RAG处理（GPU机器）
python worker.py --specialized=rag --concurrency=2

# 机器3：工作流协调
python worker.py --specialized=workflow --concurrency=2
```

### 容器化部署

```dockerfile
# Dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "worker.py", "--specialized=document"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  worker-document:
    build: .
    command: python worker.py --specialized=document --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    
  worker-rag:
    build: .
    command: python worker.py --specialized=rag --concurrency=2
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
```

## 📚 最佳实践

### 1. 资源分配

- **文档处理**: CPU密集，高并发
- **RAG处理**: 内存/GPU密集，低并发
- **文件处理**: I/O密集，中等并发

### 2. 错误处理

- 设置合适的重试次数
- 使用死信队列处理失败任务
- 监控错误率和类型

### 3. 扩展策略

- 根据队列长度自动扩展Worker
- 使用负载均衡分发任务
- 实现优雅的Worker关闭

### 4. 安全考虑

- 限制任务执行时间
- 验证任务参数
- 隔离不同类型的Worker

## 🆕 新功能

### 工作流支持

```python
# 启动文档处理工作流
curl -X POST http://localhost:8000/workflow/document-processing \
  -H 'Content-Type: application/json' \
  -d '{
    "file_id": "file123",
    "document_data": {...},
    "enable_rag": true
  }'
```

### 任务协调

- 自动任务依赖管理
- 并行任务执行
- 失败恢复机制

### 监控集成

- 实时状态监控
- 性能指标收集
- 告警机制

## 📞 支持

如有问题，请查看：

1. 日志文件：`logs/worker_*.log`
2. 监控面板：`python monitor_workers.py`
3. 环境检查：`./start_workers.sh --check`

---

🎉 **架构优化完成！享受更高效的任务处理体验！**
