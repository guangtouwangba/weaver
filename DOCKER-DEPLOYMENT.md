# Docker 部署指南

## 快速开始

### 1. 准备配置文件

确保有 `config.yaml` 文件：

```yaml
database:
  provider: "supabase"  # 或 "sqlite"
  supabase:
    url: "${SUPABASE_URL}"
    anon_key: "${SUPABASE_ANON_KEY}"

llm_providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-3.5-turbo"
```

### 2. 设置环境变量

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your_anon_key"
export OPENAI_API_KEY="your_openai_key"
```

### 3. 运行调度器

```bash
# 构建并运行
./docker-run.sh rebuild

# 或者分步执行
./docker-run.sh build   # 构建镜像
./docker-run.sh run     # 运行容器
```

## 管理命令

```bash
# 查看状态
./docker-run.sh status

# 查看日志
./docker-run.sh logs

# 停止容器
./docker-run.sh stop
```

## 手动 Docker 命令

```bash
# 构建镜像
docker build -t hybrid-job-scheduler .

# 运行容器
docker run -d \
  --name hybrid-scheduler \
  --restart unless-stopped \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  hybrid-job-scheduler

# 查看日志
docker logs -f hybrid-scheduler

# 检查状态
docker exec hybrid-scheduler python hybrid_job_scheduler.py --status
```

## 文件结构

```
.
├── config.yaml              # 主配置文件 (必需)
├── job_schedules.yaml        # 任务调度配置 (可选)
├── docker-run.sh            # 运行脚本
├── Dockerfile               # Docker 镜像配置
├── data/                    # 数据目录
├── logs/                    # 日志目录
└── downloaded_papers/       # 下载的论文
```

## 云端部署

上传到云服务器后运行：

```bash
# 上传文件
scp -r . user@server:/opt/scheduler/

# 在服务器上运行
cd /opt/scheduler
./docker-run.sh rebuild
```

完成！调度器会在后台持续运行，根据 cron 表达式创建和执行任务。