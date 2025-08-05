# 混合Job调度器系统

**全新的多线程调度架构** - 既有持续运行能力，又具备数据库驱动的云端优势！

## 🎯 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Hybrid Job Scheduler                     │
├─────────────────────────────┬───────────────────────────────┤
│      Job Executor Thread   │      Job Creator Thread      │
│                             │                               │
│  ┌─────────────────────────┐│  ┌─────────────────────────┐  │
│  │ 1. 拉取待执行job         ││  │ 1. 检查cron表达式        │  │
│  │ 2. 原子性锁定           ││  │ 2. 创建定时job          │  │
│  │ 3. 执行job             ││  │ 3. 推送到数据库         │  │
│  │ 4. 更新结果             ││  │ 4. 更新创建时间         │  │
│  │ 5. 释放锁定             ││  │                         │  │
│  └─────────────────────────┘│  └─────────────────────────┘  │
│         ↓ 每30秒             │         ↓ 每60秒             │
└─────────────────────────────┴───────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │   Cloud Database    │
                    │   (Supabase/SQLite) │
                    └─────────────────────┘
```

## 🚀 核心特性

- **🔄 双线程架构**: 执行线程 + 创建线程并行工作
- **⏰ Cron调度**: 支持复杂的定时规则，如 `0 9 * * *` (每天9点)
- **🔒 原子性执行**: 多实例安全，避免重复执行
- **🗄️ 数据库持久化**: 任务和执行记录完整保存
- **📊 实时监控**: 详细统计和健康检查
- **🛡️ 优雅关闭**: 信号处理和线程安全停止

## 📋 快速开始

### 1. 安装依赖

```bash
pip install croniter pyyaml python-dotenv supabase
```

### 2. 配置Cron任务

编辑 `job_schedules.yaml`:

```yaml
job_schedules:
  - name: "Daily Paper Fetch"
    job_type: "paper_fetch"
    cron_expression: "0 9 * * *"  # 每天上午9点
    description: "每日论文获取"
    enabled: true
    config:
      config_path: "config.yaml"
      max_papers: 100
      keywords: ["AI", "machine learning"]
  
  - name: "Weekly Cleanup" 
    job_type: "maintenance"
    cron_expression: "0 2 * * 0"  # 每周日凌晨2点
    description: "周末数据清理"
    enabled: true
    config:
      cleanup_days: 30
```

### 3. 启动调度器

```bash
# 交互模式 (Ctrl+C停止)
python hybrid_job_scheduler.py

# 后台守护进程
python hybrid_job_scheduler.py --daemon

# 详细日志
python hybrid_job_scheduler.py --verbose

# 查看状态
python hybrid_job_scheduler.py --status
```

## ⚙️ 调度器配置

### scheduler_settings (job_schedules.yaml)

```yaml
scheduler_settings:
  # 检查新job创建的间隔 (秒)
  cron_check_interval: 60
  
  # 检查待执行job的间隔 (秒)  
  job_check_interval: 30
  
  # 最大并发执行job数量
  max_concurrent_jobs: 3
  
  # 默认设置
  default_max_retries: 3
  default_timeout_seconds: 3600
  
  # Job锁定时长 (分钟)
  job_lock_duration_minutes: 30
  
  # 实例名前缀
  instance_prefix: "hybrid-scheduler"
```

## 📅 Cron表达式参考

```bash
# 格式: 分钟 小时 日 月 星期
"0 9 * * *"        # 每天上午9点
"*/30 * * * *"     # 每30分钟
"0 */2 * * *"      # 每2小时
"0 9 * * 1-5"      # 工作日上午9点
"0 2 * * 0"        # 每周日凌晨2点
"0 0 1 * *"        # 每月1号
"0 9,21 * * *"     # 每天9点和21点
```

## 🎯 Job类型

### 1. paper_fetch (论文获取)
```yaml
- name: "Morning Papers"
  job_type: "paper_fetch"
  cron_expression: "0 9 * * *"
  config:
    config_path: "config.yaml"
    max_papers: 100
    keywords: ["AI", "ML", "deep learning"]
```

### 2. maintenance (系统维护)
```yaml
- name: "Weekly Cleanup"
  job_type: "maintenance"  
  cron_expression: "0 3 * * 0"
  config:
    cleanup_days: 30
    cleanup_executions: true
    optimize_database: true
```

### 3. custom (自定义任务)
```yaml
- name: "Data Backup"
  job_type: "custom"
  cron_expression: "0 1 * * *"
  config:
    backup_type: "incremental"
    target_dir: "/backup"
    compress: true
```

## 📊 监控和管理

### 查看实时状态

```bash
# 完整状态信息
python hybrid_job_scheduler.py --status

# 监控日志
tail -f hybrid_scheduler.log

# 数据库job统计
python cloud_job_manager.py stats
```

### 管理Cron规则

```python
# 运行时添加新的cron规则
from jobs.job_creator_thread import CronJobDefinition

new_cron = CronJobDefinition(
    name="Hourly Check",
    job_type="custom", 
    cron_expression="0 * * * *",
    config={"check_type": "health"}
)

# 添加到运行中的调度器
scheduler.creator_thread.add_cron_definition(new_cron)
```

### 数据库管理

```bash
# 查看所有job
python cloud_job_manager.py list

# 查看执行历史
python cloud_job_manager.py show <job_id>

# 手动创建job (会被执行线程拾取)
python cloud_job_manager.py create "Manual Job" custom
```

## 🔧 部署示例

### 1. Systemd 服务

创建 `/etc/systemd/system/hybrid-scheduler.service`:

```ini
[Unit]
Description=Hybrid Job Scheduler
After=network.target

[Service]
Type=simple
User=scheduler
WorkingDirectory=/opt/scheduler
Environment=SUPABASE_URL=https://your-project.supabase.co
Environment=SUPABASE_ANON_KEY=your_key_here
ExecStart=/usr/bin/python3 hybrid_job_scheduler.py --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable hybrid-scheduler
sudo systemctl start hybrid-scheduler
sudo systemctl status hybrid-scheduler
```

### 2. Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN pip install croniter

ENV PYTHONPATH=/app/backend
CMD ["python", "hybrid_job_scheduler.py", "--daemon"]
```

```bash
docker build -t hybrid-scheduler .
docker run -d --name scheduler \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/job_schedules.yaml:/app/job_schedules.yaml \
  hybrid-scheduler
```

### 3. Docker Compose

```yaml
version: '3.8'
services:
  hybrid-scheduler:
    build: .
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./job_schedules.yaml:/app/job_schedules.yaml
      - ./logs:/app/logs
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🚨 故障排除

### 常见问题

1. **croniter 库缺失**
   ```bash
   pip install croniter
   ```

2. **Cron表达式错误**
   ```bash
   # 验证表达式
   python -c "from croniter import croniter; print(croniter.is_valid('0 9 * * *'))"
   ```

3. **线程健康检查失败**
   ```bash
   # 查看详细日志
   python hybrid_job_scheduler.py --verbose
   ```

4. **数据库连接问题**
   ```bash
   # 测试数据库连接
   python scripts/test_cloud_job_system.py
   ```

### 日志分析

```bash
# 查看调度器日志
tail -f hybrid_scheduler.log

# 过滤特定类型日志
grep "ERROR" hybrid_scheduler.log
grep "Job completed" hybrid_scheduler.log
grep "Created scheduled job" hybrid_scheduler.log
```

### 性能调优

```yaml
# 高频任务场景
scheduler_settings:
  cron_check_interval: 30    # 更频繁检查
  job_check_interval: 15     # 更快执行
  max_concurrent_jobs: 5     # 更多并发

# 低频任务场景  
scheduler_settings:
  cron_check_interval: 300   # 5分钟检查一次
  job_check_interval: 60     # 1分钟检查执行
  max_concurrent_jobs: 2     # 保守并发
```

## 🔍 架构优势

### vs 传统调度器
- ✅ **数据库持久化**: 任务定义和历史完整保存
- ✅ **多实例安全**: 原子性锁定避免重复执行
- ✅ **动态配置**: 运行时修改cron规则
- ✅ **详细监控**: 完整的执行统计和日志

### vs 云端单次脚本  
- ✅ **持续运行**: 无需外部触发器
- ✅ **实时响应**: 立即执行新创建的job
- ✅ **复杂调度**: 支持复杂的cron表达式
- ✅ **状态管理**: 线程健康监控

## 🎉 使用场景

### 科研论文系统
```yaml
# 多时段论文获取
- name: "Morning Papers"
  cron_expression: "0 9 * * *"
  job_type: "paper_fetch"
  
- name: "Evening Papers"  
  cron_expression: "0 21 * * *"
  job_type: "paper_fetch"

# 周末数据处理
- name: "Weekend Analysis"
  cron_expression: "0 10 * * 6,0"
  job_type: "custom"
```

### 数据处理管道
```yaml
# 每小时数据同步
- name: "Hourly Sync"
  cron_expression: "0 * * * *"
  job_type: "custom"
  
# 每日汇总报告
- name: "Daily Report"
  cron_expression: "0 6 * * *" 
  job_type: "custom"
```

### 系统维护
```yaml
# 日常清理
- name: "Daily Cleanup"
  cron_expression: "0 2 * * *"
  job_type: "maintenance"

# 周末备份
- name: "Weekend Backup"
  cron_expression: "0 3 * * 0"
  job_type: "custom"
```

---

## 🤝 开发贡献

欢迎提交Issue和Pull Request！

### 扩展新Job类型

1. 在 `SimpleJobExecutor` 中添加处理器
2. 在 `job_schedules.yaml` 中定义规则
3. 测试和文档更新

### 添加新功能

- Job优先级支持
- 分布式锁机制  
- Web管理界面
- 告警通知系统

---

**混合Job调度器** - 兼具传统调度器的强大和云端架构的灵活！🚀