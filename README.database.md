# 数据库管理指南

本项目使用 Alembic 管理 PostgreSQL 数据库的版本控制和迁移。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements-db.txt
```

### 2. 配置环境变量

确保 `.env.middleware` 文件包含正确的数据库连接信息：

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rag_db
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
```

### 3. 启动数据库服务

```bash
# 启动 PostgreSQL
./scripts/middleware-control.sh start-core
```

### 4. 初始化数据库

```bash
# 检查数据库连接
./scripts/db-migrate.sh check

# 初始化数据库（创建初始迁移并应用）
./scripts/db-migrate.sh init
```

## 📊 数据库结构

### 核心表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `documents` | 文档元数据 | id, title, content, file_path, status, metadata |
| `document_chunks` | 文档块 | id, document_id, content, chunk_index, embedding_vector |
| `query_history` | 查询历史 | id, query_text, query_type, strategy_used, response_time_ms |
| `user_sessions` | 用户会话 | id, user_id, session_data, expires_at |
| `vector_indexes` | 向量索引 | id, chunk_id, vector_type, vector_data |

### 数据库模型

```python
from infrastructure.database.models import Document, DocumentChunk, QueryHistory
from infrastructure.database.config import get_sync_session

# 使用同步会话
with get_sync_session() as session:
    doc = session.query(Document).first()
    print(doc.title)

# 使用异步会话
from infrastructure.database.config import get_async_session
async with get_async_session() as session:
    result = await session.execute(select(Document))
    docs = result.scalars().all()
```

## 🛠️ 迁移管理命令

### 基本操作

```bash
# 创建新迁移
./scripts/db-migrate.sh create "Add user preferences table"

# 应用迁移到最新版本
./scripts/db-migrate.sh upgrade

# 应用到特定版本
./scripts/db-migrate.sh upgrade abc123

# 回滚迁移
./scripts/db-migrate.sh downgrade

# 回滚到特定版本
./scripts/db-migrate.sh downgrade abc123

# 回滚到基础版本（清空数据库）
./scripts/db-migrate.sh downgrade base
```

### 查看状态

```bash
# 查看当前数据库版本
./scripts/db-migrate.sh current

# 查看迁移历史
./scripts/db-migrate.sh history

# 查看待应用的迁移
./scripts/db-migrate.sh pending

# 显示模型与数据库的差异
./scripts/db-migrate.sh diff
```

### 数据管理

```bash
# 备份数据库
./scripts/db-migrate.sh backup

# 从备份恢复
./scripts/db-migrate.sh restore backups/db/rag_db_backup_20231215_143022.sql

# 验证数据库结构
./scripts/db-migrate.sh validate

# 重置数据库（危险操作！）
./scripts/db-migrate.sh reset
```

## 🔧 开发工作流

### 1. 修改模型

编辑 `infrastructure/database/models/` 相关文件：

```python
class Document(Base):
    __tablename__ = 'documents'
    
    # 添加新字段
    author = Column(String(255))
    tags = Column(JSON, default=list)
```

### 2. 创建迁移

```bash
./scripts/db-migrate.sh create "Add author and tags to documents"
```

### 3. 检查生成的迁移文件

查看 `alembic/versions/` 目录下的新文件，确认迁移逻辑正确。

### 4. 应用迁移

```bash
./scripts/db-migrate.sh upgrade
```

### 5. 验证结果

```bash
./scripts/db-migrate.sh validate
```

## 📝 最佳实践

### 1. 迁移文件命名

使用描述性的迁移消息：

```bash
# 好的示例
./scripts/db-migrate.sh create "Add user authentication tables"
./scripts/db-migrate.sh create "Create index on documents.status"
./scripts/db-migrate.sh create "Modify user_sessions table structure"

# 避免
./scripts/db-migrate.sh create "update table"
./scripts/db-migrate.sh create "fix"
```

### 2. 安全的迁移

- 在生产环境应用迁移前，先在测试环境验证
- 重要的结构变更前，先备份数据库
- 避免直接删除列，使用分步骤迁移

### 3. 版本控制

- 迁移文件应该提交到版本控制系统
- 不要手动修改已经应用的迁移文件
- 团队开发时，及时同步迁移文件

## 🔍 故障排除

### 1. 连接问题

```bash
# 检查数据库连接
./scripts/db-migrate.sh check

# 检查 PostgreSQL 服务状态
./scripts/middleware-control.sh status
```

### 2. 迁移冲突

```bash
# 查看当前状态
./scripts/db-migrate.sh current

# 查看迁移历史
./scripts/db-migrate.sh history

# 如有冲突，可能需要手动解决
alembic merge -m "Merge conflicting migrations"
```

### 3. 回滚问题

```bash
# 如果回滚失败，检查迁移文件中的 downgrade 函数
# 确保所有 upgrade 操作都有对应的 downgrade 操作
```

### 4. 数据丢失恢复

```bash
# 从最近的备份恢复
./scripts/db-migrate.sh restore backups/db/latest_backup.sql

# 或者从中间件的自动备份恢复
./scripts/middleware-control.sh backup
```

## 🔒 生产环境注意事项

### 1. 备份策略

```bash
# 设置定期备份
# 在 cron 中添加：
# 0 2 * * * /path/to/project/scripts/db-migrate.sh backup
```

### 2. 迁移安全

- 在维护窗口执行大型迁移
- 准备回滚计划
- 监控迁移执行时间

### 3. 权限管理

- 使用专门的迁移用户
- 限制生产数据库访问权限
- 审计数据库变更

## 📊 监控和性能

### 1. 查询性能监控

```sql
-- 查看慢查询
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- 查看表大小
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 2. 索引优化

```bash
# 查看未使用的索引
psql -h localhost -U rag_user -d rag_db -c "
SELECT 
    schemaname, 
    tablename, 
    indexname, 
    idx_tup_read, 
    idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE idx_tup_read = 0 
ORDER BY schemaname, tablename;
"
```

## 🧪 测试

### 1. 单元测试

```python
import pytest
from infrastructure.database.config import sync_engine
from infrastructure.database.models import Base
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_session():
    # 创建测试数据库会话
    TestSessionLocal = sessionmaker(bind=sync_engine)
    session = TestSessionLocal()
    
    # 创建所有表
    Base.metadata.create_all(bind=sync_engine)
    
    yield session
    
    # 清理
    session.close()
    Base.metadata.drop_all(bind=sync_engine)
```

### 2. 迁移测试

```bash
# 测试迁移的完整周期
./scripts/db-migrate.sh backup
./scripts/db-migrate.sh upgrade
./scripts/db-migrate.sh downgrade
./scripts/db-migrate.sh upgrade
```