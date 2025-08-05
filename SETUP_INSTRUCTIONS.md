# 🚀 云端Job系统 - 立即设置指南

## 当前状态
✅ 所有代码已修复Supabase兼容性问题  
⚠️ 需要在Supabase中创建数据库表

## 📋 立即执行步骤

### 1. 创建Supabase表 (5分钟)

**复制以下完整SQL并在Supabase SQL编辑器中运行：**

```sql
-- Create cloud_jobs table
CREATE TABLE IF NOT EXISTS cloud_jobs (
    job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'locked', 'success', 'failed', 'disabled')),
    description TEXT DEFAULT '',
    max_retries INTEGER DEFAULT 3,
    current_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_execution TIMESTAMP WITH TIME ZONE NULL,
    locked_at TIMESTAMP WITH TIME ZONE NULL,
    locked_by TEXT NULL,
    lock_expires_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create cloud_job_executions table
CREATE TABLE IF NOT EXISTS cloud_job_executions (
    execution_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds REAL NULL,
    result JSONB NULL DEFAULT '{}'::jsonb,
    error_message TEXT NULL,
    instance_id TEXT NULL,
    FOREIGN KEY (job_id) REFERENCES cloud_jobs (job_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_status ON cloud_jobs(status);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_status_retries ON cloud_jobs(status, current_retries, max_retries);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_lock_expires ON cloud_jobs(lock_expires_at);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_type ON cloud_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_cloud_jobs_created_at ON cloud_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_cloud_job_executions_job_id ON cloud_job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_cloud_job_executions_status ON cloud_job_executions(status);
CREATE INDEX IF NOT EXISTS idx_cloud_job_executions_started_at ON cloud_job_executions(started_at);

-- Enable Row Level Security
ALTER TABLE cloud_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cloud_job_executions ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
CREATE POLICY "Allow anonymous access on cloud_jobs" ON cloud_jobs FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow anonymous access on cloud_job_executions" ON cloud_job_executions FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- Create a function to get next available job atomically
CREATE OR REPLACE FUNCTION get_next_available_job(instance_id_param TEXT, lock_duration_minutes INTEGER DEFAULT 30)
RETURNS TABLE(
    job_id TEXT,
    name TEXT,
    job_type TEXT,
    config JSONB,
    description TEXT,
    current_retries INTEGER,
    max_retries INTEGER
) AS $$
BEGIN
    RETURN QUERY
    UPDATE cloud_jobs SET 
        status = 'locked',
        locked_at = NOW(),
        locked_by = instance_id_param,
        lock_expires_at = NOW() + INTERVAL '1 minute' * lock_duration_minutes
    WHERE cloud_jobs.job_id = (
        SELECT cloud_jobs.job_id FROM cloud_jobs
        WHERE (cloud_jobs.status = 'waiting' OR (cloud_jobs.status = 'failed' AND cloud_jobs.current_retries < cloud_jobs.max_retries))
          AND (cloud_jobs.lock_expires_at IS NULL OR cloud_jobs.lock_expires_at < NOW())
        ORDER BY 
            CASE 
                WHEN cloud_jobs.status = 'waiting' THEN 0 
                WHEN cloud_jobs.status = 'failed' THEN 1 
                ELSE 2 
            END,
            cloud_jobs.created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING 
        cloud_jobs.job_id, 
        cloud_jobs.name, 
        cloud_jobs.job_type, 
        cloud_jobs.config, 
        cloud_jobs.description,
        cloud_jobs.current_retries,
        cloud_jobs.max_retries;
END;
$$ LANGUAGE plpgsql;

-- Create a function to release expired locks
CREATE OR REPLACE FUNCTION release_expired_locks()
RETURNS INTEGER AS $$
DECLARE
    released_count INTEGER;
BEGIN
    UPDATE cloud_jobs 
    SET status = CASE 
        WHEN current_retries < max_retries THEN 'waiting'
        ELSE 'failed'
    END,
    locked_at = NULL,
    locked_by = NULL,
    lock_expires_at = NULL
    WHERE status = 'locked' 
      AND lock_expires_at < NOW();
    
    GET DIAGNOSTICS released_count = ROW_COUNT;
    RETURN released_count;
END;
$$ LANGUAGE plpgsql;

-- Create view for statistics
CREATE OR REPLACE VIEW job_statistics AS
SELECT 
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'waiting' THEN 1 ELSE 0 END) as waiting_jobs,
    SUM(CASE WHEN status = 'locked' THEN 1 ELSE 0 END) as locked_jobs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_jobs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
    SUM(CASE WHEN status = 'disabled' THEN 1 ELSE 0 END) as disabled_jobs,
    NOW() as calculated_at
FROM cloud_jobs;
```

### 2. 测试系统 (1分钟)

运行SQL后，立即测试：

```bash
python scripts/test_cloud_job_system.py
```

### 3. 创建第一个任务 (30秒)

```bash
# 创建论文获取任务
python cloud_job_manager.py create "First Test Job" paper_fetch

# 查看任务
python cloud_job_manager.py list
```

### 4. 执行任务 (10秒)

```bash
# 执行一次
python cloud_job_runner.py

# 查看结果  
python cloud_job_manager.py stats
```

## 🎯 预期结果

SQL运行成功后，你应该看到：
- ✅ 2个新表创建：`cloud_jobs`, `cloud_job_executions`
- ✅ 测试全部通过
- ✅ 任务创建和执行成功

## 🚨 如果遇到问题

### SQL错误
- 确保在Supabase SQL编辑器中运行
- 不要在psql或其他工具中运行

### 权限错误  
如果遇到RLS权限问题，运行：
```sql
DROP POLICY IF EXISTS "Allow anonymous access on cloud_jobs" ON cloud_jobs;
CREATE POLICY "Allow all access on cloud_jobs" ON cloud_jobs FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow anonymous access on cloud_job_executions" ON cloud_job_executions;  
CREATE POLICY "Allow all access on cloud_job_executions" ON cloud_job_executions FOR ALL USING (true) WITH CHECK (true);
```

## 🎉 成功后

你的云端任务系统就ready了！可以：
- 通过定时脚本调用：`*/5 * * * * python cloud_job_runner.py`
- 部署到AWS Lambda、Google Cloud Functions等
- 容器化部署：`docker run cloud-job-runner`

---

**现在请复制上面SQL到Supabase运行，然后告诉我结果！** 🚀