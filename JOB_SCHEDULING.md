# Database-Driven Job Scheduling System

本文档介绍基于数据库的持久化任务调度系统，该系统可以摆脱服务部署的生命周期限制。

## 🎯 核心特性

- **持久化调度**: 任务信息存储在数据库中，服务重启不丢失
- **多数据库支持**: 支持 SQLite（本地）和 Supabase（云端）
- **任务执行记录**: 详细的执行历史和状态跟踪
- **灵活调度**: 支持 Cron 表达式定义复杂调度规则
- **故障恢复**: 任务失败自动重试机制
- **实时监控**: 任务状态和执行统计

## 🏗️ 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Job Manager   │◄──►│   Job Scheduler  │◄──►│  Job Executor   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Database     │    │  Cron Scheduler  │    │   Job Handlers  │
│  (Jobs & Logs)  │    │   (Every 60s)    │    │ (Paper Fetch)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心组件

1. **Job Manager**: 任务的 CRUD 操作
2. **Job Scheduler**: 基于数据库的调度器
3. **Job Executor**: 任务执行器和处理器
4. **Database Adapter**: 统一的数据库接口

## 📊 数据库模型

### Jobs 表

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL,           -- paper_fetch, maintenance, custom
    schedule_expression TEXT NOT NULL, -- Cron 表达式
    config JSONB NOT NULL,            -- 任务配置
    status TEXT NOT NULL,             -- active, inactive, paused, deleted
    description TEXT,
    timeout_seconds INTEGER,
    retry_count INTEGER,
    retry_delay_seconds INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_execution TIMESTAMP,
    next_execution TIMESTAMP          -- 下次执行时间
);
```

### Job Executions 表

```sql
CREATE TABLE job_executions (
    execution_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL,             -- pending, running, success, failed, timeout
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds REAL,
    result JSONB,                     -- 执行结果
    error_message TEXT,
    retry_attempt INTEGER,
    logs TEXT,
    created_at TIMESTAMP
);
```

## 🚀 快速开始

### 1. 初始化数据库表

```bash
# 初始化任务表
python scripts/init_job_tables.py

# 对于 Supabase，需要在 SQL 编辑器中运行相应的 SQL
```

### 2. 启动调度器

```bash
# 启动守护进程模式
python job_scheduler_main.py start --daemon

# 交互模式
python job_scheduler_main.py start
```

### 3. 管理任务

```bash
# 任务管理工具
python manage_jobs.py

# 列出所有任务
python manage_jobs.py list

# 查看任务详情
python manage_jobs.py show <job_id>

# 创建新任务
python manage_jobs.py create "Daily Fetch" paper_fetch "0 9 * * *"
```

## 📋 任务管理

### 创建任务

```python
from jobs.job_scheduler import DatabaseJobScheduler
from database.database_adapter import create_database_manager

# 创建调度器
db_manager = create_database_manager(config)
scheduler = DatabaseJobScheduler(db_manager)

# 创建论文获取任务
job_id = scheduler.create_job(
    name="Daily Paper Fetch",
    job_type="paper_fetch",
    schedule_expression="0 9 * * *",  # 每天上午9点
    config={
        "config_path": "config.yaml",
        "max_papers": 100,
        "keywords": ["AI", "ML", "RAG"]
    },
    description="每日论文获取任务"
)
```

### 任务类型

1. **paper_fetch**: 论文获取任务
   - 执行 `simple_paper_fetcher.py`
   - 根据配置搜索和下载论文

2. **maintenance**: 维护任务
   - 清理旧的执行记录
   - 数据库优化

3. **custom**: 自定义任务
   - 可注册自定义处理器

### Cron 表达式示例

```bash
# 格式: 分钟 小时 日 月 星期
"0 */2 * * *"      # 每2小时执行一次
"0 9 * * *"        # 每天上午9点执行
"0 9 * * 1-5"      # 工作日上午9点执行
"*/15 * * * *"     # 每15分钟执行一次
"0 2 * * 0"        # 每周日凌晨2点执行
"0 0 1 * *"        # 每月1号执行
```

## 🔧 配置

### 调度器配置

```yaml
# config.yaml
scheduler:
  interval_hours: 2          # 默认间隔（小时）
  run_on_startup: false     # 启动时立即运行
  check_interval_seconds: 60 # 检查频率（秒）

# 任务配置
job_defaults:
  timeout_seconds: 3600      # 默认超时时间
  retry_count: 3            # 重试次数
  retry_delay_seconds: 300  # 重试延迟
```

### 环境变量

```bash
# .env 文件
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
OPENAI_API_KEY=your_openai_key_here
```

## 🐳 Docker 部署

### 启动调度器容器

```bash
# 使用新的任务调度器
docker run --rm \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  -v $(pwd)/config.yaml:/app/config.yaml \
  arxiv-paper-fetcher:latest scheduler
```

### Docker Compose

```yaml
version: '3.8'
services:
  scheduler:
    build: .
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./config.yaml:/app/config.yaml
    command: scheduler
    restart: unless-stopped
```

## 📊 监控和管理

### 查看调度器状态

```bash
python job_scheduler_main.py status
```

### 实时监控

```bash
# 交互式管理
python manage_jobs.py

# 命令示例:
> list      # 列出所有任务
> show <id> # 查看任务详情
> status    # 查看调度器状态
> trigger <id> # 立即触发任务
```

### 任务控制

```bash
# 暂停任务
python manage_jobs.py pause <job_id>

# 恢复任务
python manage_jobs.py resume <job_id>

# 立即执行
python manage_jobs.py trigger <job_id>

# 删除任务
python manage_jobs.py delete <job_id>
```

## 🔍 故障排除

### 常见问题

1. **任务表不存在**
   ```bash
   python scripts/init_job_tables.py
   ```

2. **任务不执行**
   - 检查任务状态: `python manage_jobs.py show <job_id>`
   - 检查 next_execution 时间
   - 检查调度器是否运行

3. **Supabase SQL 语法错误** (syntax error at or near "BEGIN")
   - 使用 `scripts/supabase_job_schema.sql` 中的简化 SQL
   - 避免使用 PostgreSQL 的 `DO` 块语法
   
4. **Supabase 权限错误**
   ```sql
   -- 在 Supabase SQL 编辑器中运行
   DROP POLICY IF EXISTS "Authenticated write access" ON jobs;
   CREATE POLICY "Allow anonymous write access" ON jobs
       FOR ALL TO anon, authenticated
       USING (true) WITH CHECK (true);
   ```

### 日志查看

```bash
# 调度器日志
tail -f job_scheduler.log

# 任务执行日志
python manage_jobs.py show <job_id>  # 查看执行历史
```

### 性能优化

1. **索引优化**: 数据库已创建必要索引
2. **清理旧记录**: 使用 maintenance 任务定期清理
3. **并发控制**: 默认限制并发执行的任务数量

## 🧪 测试

```bash
# 运行完整测试套件
python scripts/test_job_system.py

# 测试特定功能
python scripts/test_import.py      # 测试导入
python scripts/test_supabase.py    # 测试 Supabase 连接
```

## 📚 API 参考

### JobManager 类

```python
# 创建任务
job_manager.create_job(job)

# 获取任务
job = job_manager.get_job(job_id)

# 更新任务
job_manager.update_job(job)

# 删除任务
job_manager.delete_job(job_id)

# 列出任务
jobs = job_manager.list_jobs(status=JobStatus.ACTIVE)

# 获取到期任务
due_jobs = job_manager.get_due_jobs()
```

### DatabaseJobScheduler 类

```python
# 创建调度器
scheduler = DatabaseJobScheduler(db_manager)

# 启动/停止
scheduler.start()
scheduler.stop()

# 任务控制
scheduler.pause_job(job_id)
scheduler.resume_job(job_id)
scheduler.trigger_job(job_id)

# 获取状态
status = scheduler.get_status()
```

## 🔮 未来计划

- [ ] Web 管理界面
- [ ] 任务依赖关系
- [ ] 任务优先级
- [ ] 分布式调度
- [ ] 任务模板
- [ ] 高级监控和告警

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进任务调度系统！