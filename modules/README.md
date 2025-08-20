# 模块化RAG系统

一个简单、解耦的文档处理和检索系统，重构自原有的DDD架构。

## 🚀 特性

- **简单易用**：提供简洁的API接口，隐藏复杂的内部实现
- **模块化设计**：每个模块职责明确，可独立开发和测试
- **高度可扩展**：轻松添加新的文件格式、处理策略和搜索后端
- **向后兼容**：提供兼容层，确保原有API调用方式仍然可用
- **性能优化**：内置缓存、并发处理和错误恢复机制

## 📁 架构概览

```
modules/
├── models.py              # 统一数据模型
├── file_loader/           # 文件加载模块
├── document_processor/    # 文档处理模块
├── orchestrator/          # 编排模块
├── api/                   # 模块化API
├── compatibility/         # 兼容层
└── examples/              # 使用示例
```

## 🔧 核心模块

### 1. 文件加载模块 (file_loader)
- **职责**：从各种来源加载文件并转换为统一的Document对象
- **支持格式**：文本、PDF、Word、HTML、Markdown等
- **特性**：自动格式检测、内容提取、元数据解析

### 2. 文档处理模块 (document_processor)
- **职责**：文档分块、内容清理、质量评分
- **分块策略**：固定大小、语义分块、段落分块、句子分块
- **特性**：智能分块优化、质量评分、嵌入向量生成

### 3. 编排模块 (orchestrator)
- **职责**：协调各模块交互，提供端到端处理流程
- **特性**：并发控制、错误处理、状态管理、健康检查

### 4. API模块 (api)
- **职责**：提供简单统一的外部接口
- **特性**：异步处理、批量操作、错误恢复、性能监控

### 5. 兼容层 (compatibility)
- **职责**：保持与原有DDD架构API的兼容性
- **特性**：透明适配、平滑迁移、功能映射

## 🚀 快速开始

### 基础使用

```python
import asyncio
from modules import RagAPI

async def main():
    # 创建API实例
    api = RagAPI()
    
    # 处理文档
    result = await api.process_file(
        file_path="document.pdf",
        chunking_strategy="paragraph",
        chunk_size=1000
    )
    
    print(f"处理结果: {result['success']}")
    print(f"文档ID: {result['document_id']}")
    print(f"创建块数: {result['chunks_created']}")
    
    # 搜索文档
    search_result = await api.search(
        query="关键词",
        limit=10
    )
    
    print(f"找到 {len(search_result['results'])} 个结果")
    
    # 获取文档信息
    doc_info = await api.get_document(result['document_id'])
    print(f"文档标题: {doc_info['title']}")

asyncio.run(main())
```

### 批量处理

```python
# 批量处理多个文件
files = ["doc1.txt", "doc2.pdf", "doc3.html"]

results = await api.process_files(
    file_paths=files,
    chunking_strategy="semantic",
    max_concurrent=3
)

success_count = sum(1 for r in results if r['success'])
print(f"成功处理: {success_count}/{len(files)}")
```

### 使用兼容层

```python
from modules import APIAdapter

# 兼容原有API调用方式
adapter = APIAdapter()

# 文件上传确认（原有接口）
result = await adapter.confirm_upload_completion(
    file_id="123",
    file_path="document.pdf"
)

# 知识库搜索（原有接口）
search_result = await adapter.search_knowledge(
    query="查询内容",
    limit=10
)
```

## 📊 与原有DDD架构的对比

| 方面 | 原有DDD架构 | 新模块化架构 |
|------|-------------|--------------|
| **复杂度** | 高（多层抽象） | 低（直接映射） |
| **学习曲线** | 陡峭 | 平缓 |
| **API接口** | 复杂事件驱动 | 简单函数调用 |
| **依赖注入** | 复杂的DI容器 | 简单工厂模式 |
| **错误处理** | 分散在各层 | 集中统一处理 |
| **性能** | 需要优化配置 | 内置优化 |
| **测试** | 需要复杂mock | 独立模块测试 |
| **扩展性** | 需要了解架构 | 插件式扩展 |

## 🔧 配置选项

### API配置

```python
api = RagAPI(
    enable_caching=True,          # 启用缓存
    default_chunk_size=1000,      # 默认块大小
    default_chunk_overlap=200     # 默认重叠大小
)
```

### 编排器配置

```python
from modules import DocumentOrchestrator, MultiFormatLoader, ChunkingProcessor

orchestrator = DocumentOrchestrator(
    file_loader=MultiFormatLoader(),
    document_processor=ChunkingProcessor(),
    max_concurrent_operations=5,   # 最大并发数
    enable_caching=True           # 启用缓存
)
```

## 🧪 运行示例

```bash
# 基础使用示例
python modules/examples/basic_usage.py

# 兼容性示例
python modules/examples/compatibility_example.py
```

## 📈 性能特性

- **并发处理**：支持同时处理多个文件
- **智能缓存**：自动缓存处理结果，避免重复计算
- **流式处理**：大文件分块处理，减少内存占用
- **错误恢复**：自动重试和故障转移机制
- **性能监控**：内置处理时间和质量指标

## 🔍 监控和调试

### 健康检查

```python
status = await api.get_status()
print(f"系统状态: {status['components']['overall_status']}")
```

### 错误处理

```python
try:
    result = await api.process_file("file.pdf")
except APIError as e:
    print(f"API错误: {e}")
    print(f"错误码: {e.error_code}")
    print(f"状态码: {e.status_code}")
```

## 🔧 扩展开发

### 添加新的文件加载器

```python
from modules.file_loader import IFileLoader

class CustomFileLoader(IFileLoader):
    async def load_file(self, file_path: str, metadata=None):
        # 实现自定义加载逻辑
        pass
```

### 添加新的文档处理器

```python
from modules.document_processor import IDocumentProcessor

class CustomDocumentProcessor(IDocumentProcessor):
    async def process_document(self, request):
        # 实现自定义处理逻辑
        pass
```

## 🚀 迁移指南

### 从DDD架构迁移

1. **评估当前使用**：确定使用了哪些原有API
2. **使用兼容层**：通过`APIAdapter`保持功能正常
3. **逐步替换**：将调用替换为新的`RagAPI`
4. **验证功能**：确保所有功能正常工作
5. **移除兼容层**：完全迁移到新架构

### 常见迁移场景

| 原有调用 | 新API调用 |
|----------|-----------|
| `file_upload_service.confirm_completion()` | `api.process_file()` |
| `knowledge_service.search()` | `api.search()` |
| `document_service.get_info()` | `api.get_document()` |
| `topic_service.create()` | 使用文档标签系统 |

## 📚 更多资源

- [API参考文档](api/) - 详细的API文档
- [使用示例](examples/) - 完整的使用示例
- [架构设计](../docs/architecture.md) - 详细的架构说明
- [性能优化](../docs/performance.md) - 性能优化指南

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。
