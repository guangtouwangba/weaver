# Cloud Job Runner - 5分钟快速开始

最简单的云端任务执行系统上手指南。

## 🚀 一键部署

```bash
# 克隆项目
git clone <your-repo>
cd research-agent-rag

# 自动部署
python scripts/deploy_cloud_jobs.py
```

## ⚡ 手动快速设置

### 1. 安装依赖 (30秒)

```bash
pip install python-dotenv pyyaml supabase
```

### 2. 配置数据库 (2分钟)

**选项A: 使用 Supabase (推荐云端)**

```bash
# 创建 .env 文件
echo "SUPABASE_URL=https://your-project.supabase.co" >> .env
echo "SUPABASE_ANON_KEY=your_anon_key_here" >> .env

# 在 Supabase SQL 编辑器中运行:
# CREATE TABLE cloud_jobs (...) -- 见下方SQL
```

**选项B: 使用 SQLite (本地测试)**

```bash
# 自动创建表
python scripts/init_cloud_job_tables.py
```

### 3. 创建任务 (30秒)

```bash
# 创建论文获取任务
python cloud_job_manager.py create "Daily Papers" paper_fetch

# 查看任务
python cloud_job_manager.py list
```

### 4. 执行任务 (10秒)

```bash
# 运行一次
python cloud_job_runner.py

# 查看结果
python cloud_job_manager.py stats
```

## 🗄️ 必需的SQL (Supabase)

在 Supabase SQL 编辑器中运行：

```sql
CREATE TABLE cloud_jobs (
    job_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL CHECK (job_type IN ('paper_fetch', 'maintenance', 'custom')),
    config JSONB DEFAULT '{}'::jsonb,
    status TEXT DEFAULT 'waiting' CHECK (status IN ('waiting', 'locked', 'success', 'failed', 'disabled')),
    description TEXT DEFAULT '',
    max_retries INTEGER DEFAULT 3,
    current_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_execution TIMESTAMP WITH TIME ZONE NULL,
    locked_at TIMESTAMP WITH TIME ZONE NULL,
    locked_by TEXT NULL,
    lock_expires_at TIMESTAMP WITH TIME ZONE NULL
);

CREATE TABLE cloud_job_executions (
    execution_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    job_id TEXT NOT NULL REFERENCES cloud_jobs(job_id),
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    finished_at TIMESTAMP WITH TIME ZONE NULL,
    duration_seconds REAL NULL,
    result JSONB DEFAULT '{}'::jsonb,
    error_message TEXT NULL,
    instance_id TEXT NULL
);

ALTER TABLE cloud_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cloud_job_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all" ON cloud_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON cloud_job_executions FOR ALL USING (true) WITH CHECK (true);
```

## 📱 常用命令

```bash
# 🔍 查看状态
python cloud_job_manager.py stats

# 📋 列出任务
python cloud_job_manager.py list

# ➕ 创建任务
python cloud_job_manager.py create "My Task" paper_fetch

# 🏃 执行任务  
python cloud_job_runner.py

# 🔍 查看任务详情
python cloud_job_manager.py show <job_id>

# 🧪 测试系统
python scripts/test_cloud_job_system.py
```

## 🐳 Docker 一键运行

```bash
# 构建镜像
docker build -t cloud-job-runner .

# 使用 Supabase
docker run --env-file .env cloud-job-runner

# 使用环境变量
docker run -e SUPABASE_URL=... -e SUPABASE_ANON_KEY=... cloud-job-runner
```

## ⚙️ 任务类型

### 📄 论文获取 (paper_fetch)
```bash
python cloud_job_manager.py create "Daily Fetch" paper_fetch \\
  --job-config max_papers=50 keywords="['AI','ML']"
```

### 🧹 系统维护 (maintenance)  
```bash
python cloud_job_manager.py create "Cleanup" maintenance \\
  --job-config cleanup_days=30
```

### 🔧 自定义任务 (custom)
```bash
python cloud_job_manager.py create "My Task" custom \\
  --job-config task_type=backup target_dir=/data
```

## ☁️ 云端部署

### AWS Lambda
```python
# lambda_handler.py
import subprocess
def lambda_handler(event, context):
    result = subprocess.run(['python', 'cloud_job_runner.py'])
    return {'statusCode': 200 if result.returncode == 0 else 500}
```

### Kubernetes CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: job-runner
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: runner
            image: cloud-job-runner:latest
            command: ["python", "cloud_job_runner.py"]
          restartPolicy: OnFailure
```

## 🚨 故障排除

### 没有任务可执行
```bash
# 检查任务状态
python cloud_job_manager.py list

# 创建测试任务
python cloud_job_manager.py create "Test" custom
```

### 数据库连接失败
```bash
# 测试连接
python scripts/test_cloud_job_system.py

# 检查环境变量
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
```

### 任务执行失败
```bash
# 查看详细错误  
python cloud_job_manager.py show <job_id>

# 详细日志
python cloud_job_runner.py --verbose
```

## 📈 生产使用

### 1. 设置定时执行
```bash
# Linux Cron (每5分钟)
*/5 * * * * cd /path/to/project && python cloud_job_runner.py

# 系统服务 (systemd timer)
# 见 CLOUD_JOB_RUNNER.md 详细配置
```

### 2. 监控和告警
```bash
# 健康检查脚本
if python cloud_job_runner.py --dry-run; then
    echo "System healthy"
else
    echo "System error" | mail admin@company.com
fi
```

### 3. 扩展实例
```bash
# 启动多个实例并行执行
python cloud_job_runner.py --instance-id worker-1 &
python cloud_job_runner.py --instance-id worker-2 &
python cloud_job_runner.py --instance-id worker-3 &
```

## 🔗 更多资源

- 📚 **完整文档**: [CLOUD_JOB_RUNNER.md](CLOUD_JOB_RUNNER.md)
- 🐳 **Docker指南**: 见文档部署部分
- ☁️ **云平台部署**: 见各云服务商配置
- 🆘 **技术支持**: 提交 Issue

---

**🎉 恭喜！您的云端任务系统已经ready！**

开始创建您的第一个定时任务吧：
```bash
python cloud_job_manager.py create "我的第一个任务" paper_fetch
python cloud_job_runner.py
```