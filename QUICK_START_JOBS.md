# 快速开始 - 任务调度系统

这是一个简化的指南，帮你快速设置和使用基于数据库的任务调度系统。

## 🚀 5分钟快速设置

### 方式1: 使用 SQLite (本地开发)

```bash
# 1. 初始化数据库表
python scripts/init_job_tables.py

# 2. 创建第一个任务
python manage_jobs.py create "Daily Fetch" paper_fetch "0 9 * * *"

# 3. 启动调度器
python job_scheduler_main.py start

# 4. 查看任务
python manage_jobs.py list
```

### 方式2: 使用 Supabase (云端)

```bash
# 1. 设置环境变量
echo "SUPABASE_URL=https://your-project.supabase.co" >> .env
echo "SUPABASE_ANON_KEY=your_anon_key_here" >> .env

# 2. 在 Supabase SQL 编辑器中运行以下 SQL:
```

```sql
-- 复制这个 SQL 到 Supabase SQL 编辑器
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    schedule_expression TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused', 'deleted')),
    description TEXT DEFAULT '',
    timeout_seconds INTEGER DEFAULT 3600,
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_execution TIMESTAMP WITH TIME ZONE NULL,
    next_execution TIMESTAMP WITH TIME ZONE NULL
);

CREATE TABLE IF NOT EXISTS job_executions (
    execution_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled', 'timeout')),
    started_at TIMESTAMP WITH TIME ZONE NULL,
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds REAL NULL,
    result JSONB NULL DEFAULT '{}'::jsonb,
    error_message TEXT NULL,
    retry_attempt INTEGER DEFAULT 0,
    logs TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous access on jobs" ON jobs FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow anonymous access on job_executions" ON job_executions FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
```

```bash
# 3. 更新配置使用 Supabase
# 编辑 config.yaml，将 database.provider 改为 "supabase"

# 4. 测试连接
python scripts/test_supabase_jobs.py

# 5. 创建任务和启动
python manage_jobs.py create "Daily Fetch" paper_fetch "0 9 * * *"
python job_scheduler_main.py start
```

## 📋 基本命令

### 任务管理
```bash
# 列出所有任务
python manage_jobs.py list

# 查看任务详情
python manage_jobs.py show <job_id>

# 创建任务
python manage_jobs.py create <name> <type> <schedule>

# 立即执行任务
python manage_jobs.py trigger <job_id>

# 暂停/恢复任务
python manage_jobs.py pause <job_id>
python manage_jobs.py resume <job_id>

# 删除任务
python manage_jobs.py delete <job_id>
```

### 调度器控制
```bash
# 启动调度器 (守护进程)
python job_scheduler_main.py start --daemon

# 启动调度器 (交互模式)
python job_scheduler_main.py start

# 查看状态
python job_scheduler_main.py status

# 列出任务
python job_scheduler_main.py list
```

## ⏰ 常用调度表达式

```bash
"0 9 * * *"        # 每天上午9点
"0 */2 * * *"      # 每2小时
"*/30 * * * *"     # 每30分钟
"0 9 * * 1-5"      # 工作日上午9点
"0 2 * * 0"        # 每周日凌晨2点
"0 0 1 * *"        # 每月1号
```

## 🎯 任务类型

1. **paper_fetch**: 论文获取任务
   - 自动使用 `config.yaml` 中的搜索配置
   - 下载新论文并存储到数据库

2. **maintenance**: 维护任务
   - 清理旧的执行记录
   - 数据库优化

3. **custom**: 自定义任务
   - 可以注册自定义处理器

## 🔧 故障排除

### SQLite 问题
```bash
# 如果表不存在
python scripts/init_job_tables.py

# 如果数据库损坏，删除重建
rm papers.db
python scripts/init_job_tables.py
```

### Supabase 问题
```bash
# 测试连接
python scripts/test_supabase_jobs.py

# 检查环境变量
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
```

## 📊 监控

```bash
# 实时监控
python manage_jobs.py  # 进入交互模式

# 查看统计
> status

# 查看任务列表
> list

# 查看任务详情
> show <job_id>
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t arxiv-job-scheduler .

# 使用 SQLite
docker run --rm -v $(pwd)/config.yaml:/app/config.yaml arxiv-job-scheduler

# 使用 Supabase
docker run --rm \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  -v $(pwd)/config.yaml:/app/config.yaml \
  arxiv-job-scheduler
```

就这么简单！🎉

有问题可以查看详细文档：`JOB_SCHEDULING.md` 和 `SUPABASE_SETUP.md`