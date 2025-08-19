# File 模型与 FileStatus 枚举集成指南

## 概述

本文档说明了如何将 `File` 数据库模型与 `FileStatus` 枚举正确集成，实现类型安全和业务逻辑的一致性。

## 主要更改

### 1. 统一 FileStatus 枚举

**之前的问题：**
- `domain/file.py` 中定义的是字符串枚举
- `infrastructure/database/models/file.py` 中定义的是整数枚举
- 两者不一致，导致类型混乱

**现在的解决方案：**
- 统一使用字符串枚举：`FileStatus(str, Enum)`
- 在数据库模型中使用 `SQLAlchemyEnum(FileStatus)` 类型
- 确保 domain 层和 infrastructure 层的一致性

### 2. 数据库字段类型更新

```python
# 之前
status = Column(Integer, nullable=False, default=0)

# 现在
status = Column(SQLAlchemyEnum(FileStatus), nullable=False, default=FileStatus.UPLOADING)
```

### 3. 添加业务方法

在 `File` 模型中添加了便捷的状态管理方法：

```python
def mark_as_available(self) -> None:
    """标记文件为可用状态"""
    if self.status == FileStatus.UPLOADING:
        self.status = FileStatus.AVAILABLE

def mark_as_processing(self) -> None:
    """标记文件为处理中状态"""
    self.status = FileStatus.PROCESSING

def mark_as_failed(self) -> None:
    """标记文件为失败状态"""
    self.status = FileStatus.FAILED

def mark_as_deleted(self) -> None:
    """标记文件为删除状态"""
    self.status = FileStatus.DELETED
    self.is_deleted = True
```

### 4. 添加属性方法

```python
@property
def is_available(self) -> bool:
    """检查文件是否可用"""
    return self.status == FileStatus.AVAILABLE and not self.is_deleted

@property
def is_processing(self) -> bool:
    """检查文件是否正在处理"""
    return self.status == FileStatus.PROCESSING

@property
def is_failed(self) -> bool:
    """检查文件是否处理失败"""
    return self.status == FileStatus.FAILED
```

## 使用方法

### 1. 创建文件实例

```python
from infrastructure.database.models.file import File, FileStatus

file = File(
    original_name="document.pdf",
    file_size=1024 * 1024,
    content_type="application/pdf",
    storage_bucket="my-bucket",
    storage_key="uploads/document.pdf",
    topic_id=1
    # status 会自动设置为 FileStatus.UPLOADING
)
```

### 2. 状态转换

```python
# 标记为处理中
file.mark_as_processing()

# 标记为可用
file.mark_as_available()

# 标记为失败
file.mark_as_failed()

# 标记为删除
file.mark_as_deleted()
```

### 3. 状态检查

```python
if file.is_available:
    print("文件可以下载")

if file.is_processing:
    print("文件正在处理中")

if file.is_failed:
    print("文件处理失败")
```

### 4. 使用 Repository

```python
from infrastructure.database.repositories.file import FileRepository

# 获取所有可用的文件
available_files = await repo.get_available_files()

# 获取所有处理中的文件
processing_files = await repo.get_processing_files()

# 更新文件状态
await repo.mark_as_available(file_id)

# 按状态统计文件数量
summary = await repo.get_status_summary()
```

## 数据库迁移

### 1. 运行迁移

```bash
# 应用迁移
alembic upgrade head

# 如果需要回滚
alembic downgrade -1
```

### 2. 迁移内容

- 创建 `file_status_enum` 类型
- 将现有的整数状态值转换为字符串
- 更新 `status` 字段类型为枚举
- 设置默认值为 `'uploading'`

### 3. 状态值映射

| 旧值 | 新值 | 说明 |
|------|------|------|
| 0 | 'uploading' | 上传中 |
| 1 | 'available' | 可用 |
| 2 | 'processing' | 处理中 |
| 3 | 'available' | 已处理（映射为可用） |
| 4 | 'failed' | 失败 |
| 5 | 'deleted' | 已删除 |

## 类型安全

### 1. 枚举值验证

```python
# 正确的用法
file.status = FileStatus.AVAILABLE

# 错误的用法（会报错）
file.status = "invalid_status"  # 类型错误
```

### 2. 数据库约束

- 数据库层面确保只有有效的枚举值被存储
- 防止无效状态值的插入

## 最佳实践

### 1. 状态转换

- 使用预定义的方法进行状态转换
- 避免直接赋值，确保业务逻辑的一致性
- 在状态转换时记录时间戳

### 2. 状态查询

- 使用 Repository 的专用方法进行状态查询
- 利用索引优化状态相关的查询性能
- 避免在应用层进行复杂的状态过滤

### 3. 错误处理

- 在状态转换失败时提供有意义的错误信息
- 记录状态变更的审计日志
- 实现状态回滚机制

## 测试

运行示例代码来验证集成：

```bash
python examples/file_status_usage.py
```

这将演示：
- 枚举的基本特性
- 文件状态的使用方法
- Repository 方法的使用
- 状态统计和过滤

## 注意事项

1. **向后兼容性**：迁移脚本会保留现有数据
2. **性能影响**：枚举类型比整数类型稍慢，但提供了类型安全
3. **存储空间**：字符串枚举占用更多存储空间
4. **索引优化**：确保在 `status` 字段上创建适当的索引

## 总结

通过这次集成，我们实现了：

- ✅ 类型安全的文件状态管理
- ✅ 统一的枚举定义
- ✅ 便捷的业务方法
- ✅ 完整的 Repository 支持
- ✅ 数据库层面的约束验证
- ✅ 向后兼容的数据迁移

这样的设计使得文件状态管理更加可靠、易用和可维护。
