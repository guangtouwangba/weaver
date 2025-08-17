# 嵌入处理系统设计文档

## 概述

基于UI设计中文件上传后的后台任务处理需求，我设计并实现了一个完整的异步任务处理系统，用于文件的嵌入处理和状态跟踪。

## 系统架构

### 核心组件

1. **TaskService** - 主服务类，统一管理所有任务操作
2. **TaskQueue** - 优先级队列，管理任务调度和worker协调
3. **TaskStatusManager** - 实时状态跟踪和通知管理
4. **TaskProcessors** - 具体的任务处理器（嵌入、解析、分析等）
5. **TaskErrorHandler** - 错误处理和重试机制
6. **API Routes** - REST API和WebSocket/SSE实时更新接口

### 数据模型

```python
class ProcessingTask:
    """文件处理任务定义"""
    task_id: str                    # 任务ID
    task_type: TaskType            # 任务类型（嵌入/解析/分析）
    status: TaskStatus             # 任务状态
    priority: TaskPriority         # 优先级
    file_id: str                   # 文件ID
    file_path: str                 # 文件路径
    progress: TaskProgress         # 进度信息
    config: Dict[str, Any]         # 处理配置
    # ... 更多字段
```

## 功能特性

### ✅ 已实现功能

1. **任务队列管理**
   - 基于优先级的任务调度
   - 异步worker池管理
   - 任务超时控制
   - 队列状态监控

2. **实时状态跟踪**
   - WebSocket实时通知
   - Server-Sent Events支持
   - 客户端订阅管理
   - 状态变更历史

3. **文件处理流水线**
   - 文件嵌入（向量化）
   - 文档解析（内容提取）
   - 内容分析（关键词、情感）
   - 缩略图生成
   - OCR识别

4. **错误处理机制**
   - 模式匹配的错误分类
   - 智能重试策略
   - 错误恢复机制
   - 监控和告警

5. **API接口**
   - REST API完整接口
   - WebSocket实时更新
   - SSE事件流
   - 队列管理接口

## 使用示例

### 1. 提交文件进行嵌入处理

```python
from infrastructure.tasks import process_file_embedding

# 提交文件进行嵌入处理
task_id = await process_file_embedding(
    file_id="file_123",
    file_path="/uploads/document.pdf",
    file_name="重要文档.pdf",
    file_size=2048000,
    mime_type="application/pdf",
    topic_id=42,
    user_id="user_456"
)
```

### 2. 检查任务状态

```python
from infrastructure.tasks import get_task_service

service = await get_task_service()
status = await service.get_task_status(task_id)

print(f"状态: {status['status']}")
print(f"进度: {status['progress']['percentage']}%")
print(f"当前操作: {status['progress']['current_operation']}")
```

### 3. 实时状态监听（前端JavaScript）

```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8000/api/v1/tasks/ws/42/client_123');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'task_status_update') {
        updateTaskUI(data.task_id, data.status, data.progress);
    }
};

function updateTaskUI(taskId, status, progress) {
    const element = document.getElementById(`task-${taskId}`);
    element.querySelector('.status').textContent = status;
    element.querySelector('.progress-bar').style.width = `${progress.percentage}%`;
    element.querySelector('.operation').textContent = progress.current_operation;
}
```

### 4. HTTP API调用

```bash
# 提交任务
curl -X POST "http://localhost:8000/api/v1/tasks/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "file_123",
    "file_path": "/uploads/doc.pdf",
    "file_name": "document.pdf",
    "file_size": 1024000,
    "mime_type": "application/pdf",
    "topic_id": 42,
    "task_types": ["file_embedding", "document_parsing"]
  }'

# 获取任务状态
curl "http://localhost:8000/api/v1/tasks/status/task_id_here"

# 获取主题任务列表
curl "http://localhost:8000/api/v1/tasks/topic/42?status=processing"

# 获取处理摘要
curl "http://localhost:8000/api/v1/tasks/summary?topic_id=42"
```

## 处理流程

### 嵌入处理流程

1. **文件验证** (10%) - 检查文件存在性和可读性
2. **内容提取** (30%) - 从文件中提取文本内容
3. **文档分块** (50%) - 将内容分割成适当大小的块
4. **生成嵌入** (70%) - 为每个块生成向量嵌入
5. **存储向量** (90%) - 将向量存储到向量数据库
6. **更新元数据** (100%) - 更新文件处理状态

### 状态更新流程

```
文件上传完成 → 创建处理任务 → 加入队列 → Worker处理 → 状态更新 → 客户端通知
     ↓              ↓           ↓         ↓        ↓         ↓
  [pending]    [pending]   [pending] [processing] [completed] [UI更新]
```

## 配置选项

### 嵌入配置

```python
EMBEDDING_CONFIG = {
    "chunk_size": 1000,           # 分块大小
    "chunk_overlap": 200,         # 重叠长度
    "embedding_model": "text-embedding-ada-002",  # 嵌入模型
    "vector_dimension": 1536,     # 向量维度
    "batch_size": 10             # 批处理大小
}
```

### 队列配置

```python
# 初始化任务服务
service = TaskService(
    max_workers=3,           # 最大worker数量
    max_queue_size=1000,     # 最大队列长度
    task_timeout=300         # 任务超时时间（秒）
)
```

## 监控和指标

### 队列统计

- `pending_tasks` - 等待处理的任务数
- `processing_tasks` - 正在处理的任务数
- `completed_tasks` - 已完成任务数
- `failed_tasks` - 失败任务数
- `average_processing_time` - 平均处理时间
- `queue_length` - 当前队列长度
- `active_workers` - 活跃worker数量

### 错误监控

- 按错误类型分类统计
- 错误率监控和告警
- 重试成功率跟踪
- 模式匹配的智能错误处理

## 部署和扩展

### 单机部署

```python
# 启动任务服务
from infrastructure.tasks import get_task_service

async def startup():
    service = await get_task_service()
    print("Task service started")

# FastAPI应用集成
from api.task_routes import router
app.include_router(router)
```

### 分布式扩展

系统设计支持以下扩展方式：

1. **多Worker进程** - 增加worker数量处理更多并发任务
2. **Redis队列** - 使用Redis作为分布式任务队列
3. **专用Worker** - 为不同任务类型分配专门的worker
4. **负载均衡** - 在多个处理节点间分配任务

## 与现有系统集成

### 文件上传集成

```python
from infrastructure.tasks.integration_example import FileProcessingIntegration

# 文件上传完成后的回调
async def on_file_upload_complete(file_info):
    integration = FileProcessingIntegration()
    await integration.initialize()
    
    result = await integration.on_file_uploaded(
        file_id=file_info["id"],
        file_path=file_info["path"],
        file_name=file_info["name"],
        file_size=file_info["size"],
        mime_type=file_info["mime_type"],
        topic_id=file_info["topic_id"],
        user_id=file_info["user_id"]
    )
    
    return result
```

### 数据库更新

任务完成后自动更新文件表的处理状态：

```sql
UPDATE files 
SET 
    is_processed = true,
    processing_status = 'completed',
    embedding_status = 'success',
    vector_count = 25,
    processed_at = NOW()
WHERE id = 'file_123';
```

## 性能优化

### 并发处理

- 异步任务处理，避免阻塞
- Worker池管理，支持并发处理
- 批量嵌入生成，提高效率

### 内存管理

- 流式文件处理，避免大文件内存占用
- 及时清理临时数据
- 智能垃圾回收

### 网络优化

- WebSocket长连接复用
- 压缩嵌入向量数据
- 分页查询大量任务

## 安全考虑

### 访问控制

- 用户只能访问自己的任务
- Topic级别的权限控制
- API密钥验证

### 数据安全

- 文件路径验证，防止路径遍历
- 输入数据验证和清理
- 错误信息脱敏

## 故障恢复

### 任务恢复

- 系统重启后自动恢复处理中的任务
- 失败任务的智能重试
- 持久化任务状态

### 错误处理

- 分类错误处理策略
- 自动故障转移
- 人工干预机制

## 扩展点

### 新增处理器

```python
from infrastructure.tasks.processors import BaseProcessor

class CustomProcessor(BaseProcessor):
    async def process(self, task: ProcessingTask) -> TaskResult:
        # 自定义处理逻辑
        return TaskResult(success=True, data={})

# 注册处理器
TASK_PROCESSORS[TaskType.CUSTOM_TASK] = CustomProcessor
```

### 新增错误模式

```python
from infrastructure.tasks.error_handler import get_error_handler, ErrorPattern

handler = get_error_handler()
handler.add_pattern(ErrorPattern(
    name="custom_error",
    category=ErrorCategory.TRANSIENT,
    retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    max_retries=3,
    message_patterns=["custom error pattern"]
))
```

## 总结

这个嵌入处理系统提供了：

1. **完整的任务处理流水线** - 从文件上传到嵌入生成的全流程
2. **实时状态跟踪** - WebSocket/SSE支持，前端可实时显示处理进度
3. **健壮的错误处理** - 智能重试和故障恢复机制
4. **高性能架构** - 异步处理、并发控制、资源优化
5. **易于扩展** - 模块化设计，支持新增处理器和错误模式
6. **完善的监控** - 详细的统计指标和健康检查

系统完全满足UI设计中展示的文件处理状态跟踪需求，并提供了超出需求的扩展能力和企业级特性。