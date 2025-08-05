# Cloud Job Runner System

简化的云原生任务执行系统，专为无状态、serverless 环境设计。

## 🎯 设计理念

**传统调度器的问题：**
- 需要长期运行的进程
- 复杂的线程管理
- 不适合云函数和容器化部署

**云端Job Runner的优势：**
- **无状态**: 每次运行独立，执行完即退出
- **轻量级**: 只专注执行job，不包含调度逻辑  
- **云原生**: 适合AWS Lambda、Kubernetes CronJob等
- **水平扩展**: 多实例并行运行，原子性防冲突

## 🏗️ 系统架构

```
云端触发器 → Cloud Job Runner → 数据库查询 → 原子锁定Job → 执行Job → 更新结果 → 退出
```

### 核心组件

1. **CloudJob 数据模型**: 简化的job定义，支持锁定机制
2. **CloudJobPicker**: 原子性job选择和锁定，避免并发冲突
3. **SimpleJobExecutor**: 轻量化job执行器，无线程管理
4. **cloud_job_runner.py**: 主执行脚本，单次运行逻辑

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements-simple.txt

# 设置环境变量 (.env 文件)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

### 2. 初始化数据库

```bash
# 创建cloud job表
python scripts/init_cloud_job_tables.py

# 测试系统
python scripts/test_cloud_job_system.py
```

### 3. 创建和执行Job

```bash
# 创建论文获取任务
python cloud_job_manager.py create "Daily Papers" paper_fetch --job-config max_papers=50

# 运行job执行器
python cloud_job_runner.py

# 查看统计
python cloud_job_manager.py stats
```

## 📋 Job 管理

### 创建Job

```bash
# 论文获取job
python cloud_job_manager.py create "Daily Fetch" paper_fetch \\
  --description "每日论文获取" \\
  --job-config config_path=config.yaml max_papers=100

# 维护job  
python cloud_job_manager.py create "Weekly Cleanup" maintenance \\
  --job-config cleanup_days=30 cleanup_executions=true

# 自定义job
python cloud_job_manager.py create "Custom Task" custom \\
  --job-config task_type=data_processing input_file=data.json
```

### 监控Job

```bash
# 列出所有job
python cloud_job_manager.py list

# 查看特定job详情
python cloud_job_manager.py show <job_id>

# 实时统计
python cloud_job_manager.py stats

# 查看等待执行的job
python cloud_job_manager.py list --status waiting
```

## 🔧 部署方式

### 1. AWS Lambda

```yaml
# serverless.yml
service: arxiv-job-runner

provider:
  name: aws
  runtime: python3.9
  environment:
    SUPABASE_URL: ${env:SUPABASE_URL}
    SUPABASE_ANON_KEY: ${env:SUPABASE_ANON_KEY}

functions:
  jobRunner:
    handler: lambda_handler.main
    timeout: 900  # 15分钟
    events:
      - schedule: rate(5 minutes)  # 每5分钟触发
```

```python
# lambda_handler.py
import subprocess
import sys

def main(event, context):
    result = subprocess.run([
        sys.executable, 'cloud_job_runner.py'
    ], capture_output=True, text=True)
    
    return {
        'statusCode': 200 if result.returncode == 0 else 500,
        'body': result.stdout
    }
```

### 2. Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: arxiv-job-runner
spec:
  schedule: "*/5 * * * *"  # 每5分钟
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: job-runner
            image: arxiv-job-runner:latest
            env:
            - name: SUPABASE_URL
              valueFrom:
                secretKeyRef:
                  name: supabase-credentials
                  key: url
            - name: SUPABASE_ANON_KEY
              valueFrom:
                secretKeyRef:
                  name: supabase-credentials
                  key: anon_key
            command: ["python", "cloud_job_runner.py"]
          restartPolicy: OnFailure
```

### 3. Google Cloud Functions

```python
# main.py
from cloud_job_runner import main as runner_main
import sys
from io import StringIO

def cloud_job_runner(request):
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        runner_main()
        output = captured_output.getvalue()
        return {'status': 'success', 'output': output}
    except SystemExit as e:
        output = captured_output.getvalue()
        return {'status': 'error' if e.code != 0 else 'success', 'output': output}
    finally:
        sys.stdout = old_stdout
```

### 4. Docker 容器

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements-simple.txt

ENV PYTHONPATH=/app/backend
CMD ["python", "cloud_job_runner.py"]
```

```bash
# 构建和运行
docker build -t arxiv-job-runner .
docker run --env-file .env arxiv-job-runner
```

## 🔒 并发安全

### 原子性Job锁定

系统使用数据库级别的原子操作确保多实例并发安全：

**Supabase (PostgreSQL):**
```sql
-- 原子性获取下一个job
UPDATE cloud_jobs SET 
    status = 'locked',
    locked_at = NOW(),
    locked_by = 'instance-id',
    lock_expires_at = NOW() + INTERVAL '30 minutes'
WHERE job_id = (
    SELECT job_id FROM cloud_jobs
    WHERE status = 'waiting'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
```

**SQLite:**
```sql
-- 事务中的原子性操作
BEGIN IMMEDIATE;
UPDATE cloud_jobs SET status = 'locked' WHERE job_id = ?;
COMMIT;
```

### 锁定超时处理

- 默认锁定30分钟
- 自动释放过期锁定
- 支持失败重试机制

## 📊 Job 类型

### 1. paper_fetch
自动获取ArXiv论文

```json
{
  "config_path": "config.yaml",
  "max_papers": 100,
  "keywords": ["AI", "ML", "RAG"]
}
```

### 2. maintenance  
系统维护任务

```json
{
  "cleanup_days": 30,
  "cleanup_executions": true
}
```

### 3. custom
自定义任务

```python
# 注册自定义处理器
def my_custom_handler(job):
    # 自定义业务逻辑
    return {"success": True, "processed": 100}

executor.register_handler('my_task', my_custom_handler)
```

## 🔍 监控和调试

### 日志分析

```bash
# 详细日志
python cloud_job_runner.py --verbose

# 查看可用job（不执行）
python cloud_job_runner.py --dry-run
```

### 执行统计

每个job执行都会记录：
- 开始/结束时间
- 执行时长
- 结果数据
- 错误信息
- 执行实例ID

### 故障排除

```bash
# 检查系统状态
python scripts/test_cloud_job_system.py

# 查看失败的job
python cloud_job_manager.py list --status failed

# 查看job执行历史
python cloud_job_manager.py show <job_id>

# 释放死锁
python -c "
from jobs.job_picker import CloudJobPicker
from database.database_adapter import create_database_manager
picker = CloudJobPicker(create_database_manager({}))
picker._release_expired_locks()
"
```

## 🔧 配置选项

### 环境变量

```bash
# 数据库配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# 可选配置
JOB_LOCK_DURATION=30  # 锁定时长（分钟）
JOB_INSTANCE_ID=custom-id  # 实例ID
```

### 运行参数

```bash
python cloud_job_runner.py \\
  --config custom_config.yaml \\
  --instance-id worker-01 \\
  --lock-duration 60 \\
  --verbose
```

## 🚀 最佳实践

### 1. 合理设置触发频率
- 开发环境: 5-10分钟
- 生产环境: 根据job数量和执行时间调整
- 避免频繁触发导致资源浪费

### 2. 监控job执行
- 设置告警：连续失败超过阈值
- 监控执行时长：发现性能问题
- 跟踪锁定超时：避免死锁

### 3. 合理配置重试
- 网络相关任务：增加重试次数
- 资源密集型任务：减少重试，快速失败
- 设置合理的重试间隔

### 4. 数据库优化
- 定期清理执行记录
- 监控数据库连接数
- 使用连接池（生产环境）

## 📈 扩展功能

### Job优先级
通过修改job选择查询添加优先级：

```sql
ORDER BY 
    priority DESC,  -- 高优先级优先
    CASE WHEN status = 'waiting' THEN 0 ELSE 1 END,
    created_at ASC
```

### Job依赖
实现job间依赖关系：

```python
class CloudJob:
    def __init__(self, ..., depends_on: List[str] = None):
        self.depends_on = depends_on or []
```

### 分布式锁
使用Redis实现更高性能的分布式锁：

```python
import redis
r = redis.Redis()

def acquire_job_lock(job_id, instance_id, ttl=1800):
    return r.set(f"job_lock:{job_id}", instance_id, nx=True, ex=ttl)
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 克隆项目
git clone <repository>
cd research-agent-rag

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python scripts/test_cloud_job_system.py

# 运行linter
make lint
```

### 提交规范

- feat: 新功能
- fix: 修复
- docs: 文档更新
- test: 测试相关
- refactor: 重构

---

## 📄 许可证

[MIT License](LICENSE)

## 🔗 相关文档

- [ArXiv API 文档](https://arxiv.org/help/api)
- [Supabase 文档](https://supabase.com/docs)
- [Docker 部署指南](./DOCKER_DEPLOYMENT.md)
- [AWS Lambda 部署指南](./AWS_LAMBDA_DEPLOYMENT.md)

---

**Cloud Job Runner** - 让您的任务执行更简单、更可靠！ 🚀