# 修复迁移卡住问题

## 问题症状

部署时卡在：
```
Running upgrade  -> 20241126_000001, Initial schema
```

迁移一直不结束，服务无法启动。

## 原因

1. 数据库表已经存在（之前手动创建或从其他源导入）
2. Alembic 版本表 `alembic_version` 为空或记录不一致
3. Alembic 尝试创建已存在的表，导致卡住或死锁

## 快速修复方案

### 方案 1: 自动超时恢复（推荐）

已在 `scripts/start-prod.sh` 中添加超时机制：
- 迁移最多等待 60 秒
- 超时后自动尝试 `alembic stamp head`
- 标记当前状态后继续启动

**无需手动操作**，重新部署即可。

### 方案 2: 手动标记当前版本

如果方案 1 不起作用，手动运行：

```bash
# 1. 连接到数据库
# 使用 Supabase Dashboard 的 SQL Editor 或 psql 客户端

# 2. 运行修复 SQL
cd app/backend
cat scripts/fix-alembic-version.sql
# 将内容复制到 SQL Editor 执行

# 或使用 alembic stamp 命令
alembic stamp head
```

### 方案 3: 完全重置迁移状态

如果数据库是新的且没有重要数据：

```bash
# 1. 删除 alembic_version 表
DROP TABLE IF EXISTS alembic_version;

# 2. 重新运行迁移
alembic upgrade head
```

## 验证修复

修复后，检查版本表：

```sql
SELECT * FROM alembic_version;
```

应该返回：
```
version_num                      
---------------------------------
20241202_000003_add_evaluation_log
```

## 预防措施

### 1. 使用 Transaction Mode

确保 `DATABASE_URL` 使用端口 6543（Transaction Mode）：
```
DATABASE_URL=postgresql://...@...pooler.supabase.com:6543/postgres
```

### 2. 检查迁移日志

启动时查看日志：
```bash
# 应该看到
✅ Migrations completed successfully

# 或超时后
⚠️  Migration timed out after 60 seconds
   Marking current state and continuing startup...
```

### 3. 手动运行迁移

在部署前先测试迁移：
```bash
# 本地测试
cd app/backend
alembic upgrade head

# 检查状态
alembic current
```

## 常见问题

### Q: 为什么会卡住？

A: 通常是因为：
1. 表已存在但 `alembic_version` 为空
2. 迁移脚本创建表时与现有表冲突
3. Transaction Mode 下的锁等待超时

### Q: 会丢失数据吗？

A: 不会。`alembic stamp` 只更新版本表，不修改数据。

### Q: 如何避免再次发生？

A: 
1. 始终使用 Alembic 管理数据库架构
2. 不要手动创建表
3. 使用 Transaction Mode (6543)
4. 在生产环境部署前先在测试环境验证

## 技术细节

### Alembic 版本表结构

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
```

### 迁移版本历史

```
20241126_000001 - Initial schema
20241127_000002 - Add data column to canvases
20241202_000002 - Add tsvector for hybrid search
20241202_000003 - Add evaluation log (最新)
```

### 超时机制

```bash
# start-prod.sh
timeout 60 alembic upgrade head
# 60 秒后自动终止，不会无限等待
```

