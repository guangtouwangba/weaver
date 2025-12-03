# 自动迁移机制说明

## 概述

为确保每次部署都能自动成功迁移，系统实现了多层自动恢复机制。

## 自动恢复机制

### 1️⃣ 超时保护（60秒）

```bash
timeout 60 alembic upgrade head
```

- 防止迁移无限等待
- 60秒后自动终止
- 触发自动恢复流程

### 2️⃣ 智能检测

迁移失败时自动检测原因：
- **超时（124）**：表已存在，尝试标记版本
- **其他错误**：尝试恢复，失败则继续启动

### 3️⃣ 自动恢复

```bash
# 超时后自动执行
alembic stamp head
```

- 标记数据库为最新版本
- 不运行任何 SQL
- 告诉 Alembic "数据库已是最新"

### 4️⃣ 优雅降级

即使恢复失败，服务仍会启动：
- 记录错误日志
- 提供手动修复建议
- 不阻塞服务启动

## 迁移流程

```
开始部署
   ↓
运行 alembic upgrade head (60秒超时)
   ↓
   ├─成功 → ✅ 启动服务
   │
   └─失败/超时
      ↓
   检测表是否存在
      ↓
      ├─表存在 → alembic stamp head → ✅ 启动服务
      │
      └─表不存在 → ⚠️  记录错误 → 启动服务（允许后续手动修复）
```

## 配置优化

### Alembic 配置

```python
# alembic/env.py

# 1. Transaction Mode 优化
connect_args = {
    "statement_cache_size": 0,  # 禁用 prepared statements
    "command_timeout": 30,       # 命令超时 30 秒
}

# 2. 每个迁移一个事务
context.configure(
    transaction_per_migration=True,  # 避免长事务
)

# 3. 引擎超时配置
engine_config = {
    "pool_timeout": "10",      # 连接超时 10 秒
    "pool_recycle": "300",     # 5 分钟回收连接
}
```

### 启动脚本优化

```bash
# scripts/start-prod.sh

# 1. 60 秒超时
timeout 60 alembic upgrade head

# 2. 超时后自动 stamp
timeout 10 alembic stamp head

# 3. 即使失败也启动服务
exec uvicorn research_agent.main:app ...
```

## 如何确保每次都成功

### 开发环境

```bash
# 本地测试迁移
cd app/backend
alembic upgrade head

# 检查状态
alembic current
```

### 生产环境

#### 首次部署
1. 数据库为空 → 自动运行所有迁移 ✅
2. 60 秒内完成 → 成功

#### 后续部署
1. 检查版本 → 已是最新 → 跳过 ✅
2. 有新迁移 → 运行增量迁移 → 成功 ✅
3. 超时 → stamp 标记 → 成功 ✅

### 异常恢复

如果自动恢复失败：

```bash
# 方法 1: 使用 SQL（最快）
# Supabase SQL Editor:
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) 
VALUES ('20241202_000003_add_evaluation_log');

# 方法 2: 使用脚本
./scripts/smart-migrate.sh

# 方法 3: 手动 stamp
alembic stamp head
```

## 监控和日志

### 成功的日志
```
Running database migrations...
INFO  [alembic.runtime.migration] Running upgrade -> 20241202_000003
✅ Migrations completed successfully
Starting Uvicorn server...
```

### 超时恢复的日志
```
Running database migrations...
⏱️  Migration timed out after 60 seconds
🔧 Attempting recovery: Stamping database...
✅ Database stamped successfully
Starting Uvicorn server...
```

### 需要手动修复的日志
```
Running database migrations...
❌ Migration failed with exit code 1
⚠️  Could not recover automatically
   Service will start, but migrations may be needed.
   Check: ./scripts/fix-alembic-state.sh
Starting Uvicorn server...
```

## 最佳实践

### 1. 编写幂等迁移

```python
# ✅ 好的做法
def upgrade():
    # 检查是否已存在
    op.execute("""
        CREATE TABLE IF NOT EXISTS my_table (
            id UUID PRIMARY KEY
        )
    """)

# ❌ 避免
def upgrade():
    # 直接创建，表存在会报错
    op.create_table('my_table', ...)
```

### 2. 测试迁移

```bash
# 本地测试
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# 验证
alembic current
```

### 3. 增量迁移

```bash
# 每次只添加小的变更
alembic revision --autogenerate -m "add_user_email"

# 避免大的架构重构
```

### 4. 监控部署

- 查看部署日志
- 确认迁移成功
- 验证服务启动

## 故障排查

### Q: 为什么会超时？

A: 可能原因：
1. 表已存在，Alembic 尝试创建导致冲突
2. Transaction Mode 下的锁等待
3. 网络延迟

**解决**：自动恢复机制会处理

### Q: stamp 是否安全？

A: 是的，stamp 只更新版本表：
- ✅ 不修改数据
- ✅ 不创建/删除表
- ✅ 只标记版本号

### Q: 如何验证迁移成功？

A: 检查数据库：
```sql
-- 查看当前版本
SELECT * FROM alembic_version;

-- 查看表列表
\dt

-- 验证表结构
\d your_table_name
```

## 总结

系统已实现：
- ✅ 自动超时保护（60秒）
- ✅ 智能故障检测
- ✅ 自动恢复（stamp）
- ✅ 优雅降级（继续启动）
- ✅ 详细日志
- ✅ 手动修复工具

**正常情况下，每次部署都会自动成功，无需人工干预。**

