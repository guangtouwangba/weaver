# 快速修复迁移卡住问题

## 最简单的方法（推荐）

### 1. 打开 Supabase SQL Editor

1. 登录 [Supabase Dashboard](https://app.supabase.com)
2. 选择你的项目
3. 点击左侧菜单的 **SQL Editor**
4. 点击 **New Query**

### 2. 运行修复 SQL

复制以下 SQL 并执行：

```sql
-- 删除旧版本记录（如果有）
DELETE FROM alembic_version;

-- 插入最新版本
INSERT INTO alembic_version (version_num) 
VALUES ('20241202_000003_add_evaluation_log');

-- 验证结果
SELECT * FROM alembic_version;
```

### 3. 重新部署

在 Zeabur 触发重新部署，或者如果服务还在运行，等待自动超时恢复。

## 预期结果

执行 SQL 后应该看到：

```
version_num                      
---------------------------------
20241202_000003_add_evaluation_log

(1 row)
```

## 验证修复

重新部署后，日志应该显示：

```
Running database migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
✅ Migrations completed successfully
```

或者（如果已经是最新版本）：

```
⚠️  Migration timed out after 60 seconds
   Marking current state and continuing startup...
Starting Uvicorn server...
```

## 为什么需要这样做？

1. **表已存在**：数据库表已经创建（可能是之前手动创建或导入的）
2. **版本表为空**：`alembic_version` 表不存在或为空
3. **Alembic 卡住**：尝试运行初始迁移，但表已存在导致卡住

通过直接设置版本号，告诉 Alembic "数据库已经是最新版本了，不需要运行迁移"。

## 如果 SQL 执行失败

### 错误: `relation "alembic_version" does not exist`

表不存在，需要先创建：

```sql
-- 创建 alembic_version 表
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- 插入版本
INSERT INTO alembic_version (version_num) 
VALUES ('20241202_000003_add_evaluation_log');
```

### 错误: 权限不足

确保使用的是 **service_role** 密钥，而不是 **anon** 密钥。

## 其他方法

如果你有 `psql` 命令行工具：

```bash
# 设置 DATABASE_URL
export DATABASE_URL='your-database-url'

# 运行快速修复脚本
cd app/backend
./scripts/quick-fix-migration.sh
```

## 预防再次发生

1. ✅ 代码已添加 60 秒超时机制
2. ✅ 超时后自动尝试 `alembic stamp head`
3. ✅ 使用 Transaction Mode (6543) 避免连接问题

重新部署后不应该再出现这个问题。

