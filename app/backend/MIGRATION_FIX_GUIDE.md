# 迁移修复指南

## 问题

错误信息：
```
Can't locate revision identified by '20241202_000003_add'
```

## 原因

版本号不完整。正确的版本号是：`20241202_000003`（不是 `20241202_000003_add`）

## 快速修复（2 分钟）

### 1. 打开 Supabase SQL Editor

1. 访问 https://app.supabase.com
2. 选择你的项目
3. 左侧菜单：**SQL Editor**
4. 点击：**New Query**

### 2. 运行修复 SQL

复制粘贴并执行：

```sql
-- 删除旧版本
DELETE FROM alembic_version;

-- 插入正确的版本号（注意：是 20241202_000003 不是 20241202_000003_add）
INSERT INTO alembic_version (version_num) 
VALUES ('20241202_000003');

-- 验证
SELECT * FROM alembic_version;
```

### 3. 验证结果

应该看到：
```
version_num      
-----------------
20241202_000003

(1 row)
```

### 4. 重新部署

在 Zeabur 触发重新部署，或等待当前部署自动恢复（60秒超时）。

## 验证修复成功

部署日志应显示：

```
Running database migrations...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
✅ Migrations completed successfully
Starting Uvicorn server...
```

## 为什么会出现这个问题？

之前的修复建议使用了错误的版本号：
- ❌ 错误：`20241202_000003_add_evaluation_log`（文件名）
- ✅ 正确：`20241202_000003`（revision ID）

Alembic 使用的是 **revision ID**，而不是文件名。

## 如何找到正确的 revision ID？

### 方法 1: 查看迁移文件

打开任意迁移文件（如 `20241202_000003_add_evaluation_log.py`）：

```python
# revision identifiers, used by Alembic.
revision: str = '20241202_000003'  # ← 这个是正确的 ID
```

### 方法 2: 使用 alembic history

```bash
cd app/backend
alembic history

# 输出：
# 20241202_000003 -> head (head), Add evaluation log table
# 20241202_000002 -> 20241202_000003, Add tsvector for hybrid search
# ...
```

第一列就是正确的 revision ID。

## 当前所有迁移版本

按顺序：

1. `20241126_000001` - Initial schema
2. `20241127_000001` - Add file path to documents
3. `20241127_000002` - Add data column to canvases
4. `20241128_000001` - Add chat messages table
5. `20241128_000002` - Add task queue and graph tables
6. `20241128_000003` - Add graph status
7. `20241202_000001` - Add curriculum table
8. `20241202_000002` - Add tsvector for hybrid search
9. **`20241202_000003`** - Add evaluation log (最新) ✅

## 故障排查

### 如果 SQL 执行失败

**错误: `relation "alembic_version" does not exist`**

先创建表：

```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('20241202_000003');
```

**错误: 权限不足**

确保使用 **service_role** 密钥，而不是 anon 密钥。

### 如果仍然报错

1. 检查数据库表是否存在：
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```

2. 如果表不存在，需要运行完整迁移：
   ```bash
   alembic upgrade head
   ```

3. 如果表存在但结构不对，可能需要手动调整或重建数据库

## 预防措施

现在代码已更新：
- ✅ 自动超时恢复
- ✅ 正确的版本号检测
- ✅ 详细的错误日志

执行上面的 SQL 后，以后部署就会自动成功了！

