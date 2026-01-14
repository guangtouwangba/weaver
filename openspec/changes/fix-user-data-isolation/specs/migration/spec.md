# Spec: Database Migration for User Isolation

## 目标

创建 Alembic migration 文件，为所有核心资源表添加 `user_id` 列。

## 文件路径

`app/backend/alembic/versions/20260114_XXXXXX_add_user_id_to_all_tables.py`

（XXXXXX 将由 alembic revision 命令自动生成）

---

## 创建步骤

### Step 1: 生成 Migration 框架

```bash
cd app/backend
alembic revision -m "add_user_id_to_all_tables"
```

这会在 `alembic/versions/` 目录生成一个新文件。

### Step 2: 编辑 Migration 内容

**打开生成的文件**，替换为以下完整内容：

```python
"""Add user_id to all resource tables for multi-tenant isolation.

This migration adds a user_id column to all core resource tables to enable
database-level user isolation. The user_id is backfilled from the associated
project's user_id.

Tables modified:
- documents
- resource_chunks
- canvases
- chat_messages
- chat_memories
- chat_summaries
- outputs
- highlights
- comments
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
# 注意：这里的值由 alembic revision 命令自动生成，不要修改
revision = 'XXXXXX'  # 保持生成的值
down_revision = 'XXXXXX'  # 保持生成的值
branch_labels = None
depends_on = None


# 需要添加 user_id 的表列表
TABLES_WITH_PROJECT_ID = [
    'documents',
    'resource_chunks',
    'canvases',
    'chat_messages',
    'chat_memories',
    'chat_summaries',
    'outputs',
]

TABLES_WITH_DOCUMENT_ID = [
    'highlights',
    'comments',
]

ALL_TABLES = TABLES_WITH_PROJECT_ID + TABLES_WITH_DOCUMENT_ID


def upgrade() -> None:
    """Add user_id column to all resource tables and backfill from project."""
    
    # Step 1: 为每个表添加 user_id 列和索引
    for table_name in ALL_TABLES:
        # 添加列
        op.add_column(
            table_name,
            sa.Column('user_id', sa.String(255), nullable=True)
        )
        # 创建索引
        op.create_index(
            f'idx_{table_name}_user_id',
            table_name,
            ['user_id']
        )
    
    # Step 2: 为有 project_id 的表回填 user_id (直接从 project 获取)
    for table_name in TABLES_WITH_PROJECT_ID:
        op.execute(f"""
            UPDATE {table_name}
            SET user_id = (
                SELECT user_id
                FROM projects
                WHERE projects.id = {table_name}.project_id
            )
            WHERE user_id IS NULL
        """)
    
    # Step 3: 为通过 document_id 关联的表回填 user_id
    # highlights: document_id -> documents.project_id -> projects.user_id
    op.execute("""
        UPDATE highlights
        SET user_id = (
            SELECT p.user_id
            FROM documents d
            JOIN projects p ON d.project_id = p.id
            WHERE d.id = highlights.document_id
        )
        WHERE user_id IS NULL
    """)
    
    # comments: document_id -> documents.project_id -> projects.user_id
    op.execute("""
        UPDATE comments
        SET user_id = (
            SELECT p.user_id
            FROM documents d
            JOIN projects p ON d.project_id = p.id
            WHERE d.id = comments.document_id
        )
        WHERE user_id IS NULL
    """)


def downgrade() -> None:
    """Remove user_id column from all resource tables."""
    for table_name in ALL_TABLES:
        # 删除索引
        op.drop_index(f'idx_{table_name}_user_id', table_name=table_name)
        # 删除列
        op.drop_column(table_name, 'user_id')
```

---

## 执行 Migration

### 本地环境

```bash
cd app/backend
alembic upgrade head
```

### 生产环境

```bash
# 1. 先备份数据库
pg_dump $DATABASE_URL > backup_before_user_isolation.sql

# 2. 执行 migration
cd app/backend
DATABASE_URL=<production_url> alembic upgrade head
```

---

## 验证 Migration

### 验证列已添加

```bash
psql $DATABASE_URL -c "
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE column_name = 'user_id' 
  AND table_schema = 'public'
  AND table_name IN (
    'documents', 'resource_chunks', 'canvases', 
    'chat_messages', 'chat_memories', 'chat_summaries',
    'outputs', 'highlights', 'comments'
  )
ORDER BY table_name;
"
```

**预期输出**: 9 行，每个表一行

### 验证索引已创建

```bash
psql $DATABASE_URL -c "
SELECT indexname 
FROM pg_indexes 
WHERE indexname LIKE 'idx_%_user_id'
ORDER BY indexname;
"
```

**预期输出**: 9 行，每个索引一行

### 验证数据已回填

```bash
psql $DATABASE_URL -c "
SELECT 
    'documents' as table_name, 
    COUNT(*) as total,
    COUNT(user_id) as with_user_id,
    COUNT(*) - COUNT(user_id) as without_user_id
FROM documents
UNION ALL
SELECT 'resource_chunks', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM resource_chunks
UNION ALL
SELECT 'canvases', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM canvases
UNION ALL
SELECT 'chat_messages', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM chat_messages
UNION ALL
SELECT 'outputs', COUNT(*), COUNT(user_id), COUNT(*) - COUNT(user_id) FROM outputs;
"
```

**预期输出**: `without_user_id` 列应该全部为 0（除非 project.user_id 本身为 NULL）

---

## 回滚步骤

如果需要回滚：

```bash
cd app/backend
alembic downgrade -1
```

这会删除所有添加的 `user_id` 列和索引。
