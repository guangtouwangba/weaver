# DDD + RAG 知识管理系统

## 🏗️ 架构概览

本项目采用 **Domain-Driven Design (DDD)** 架构设计，整合了 **RAG (Retrieval-Augmented Generation)** 技术栈，构建了一个现代化的知识管理系统。

### 🎯 核心特性

- **领域驱动设计**: 清晰的业务逻辑分离和领域建模
- **RAG 技术栈**: 语义搜索、知识提取、向量存储
- **微服务友好**: 松耦合的模块化设计
- **事件驱动**: 异步处理和事件发布/订阅
- **多种搜索策略**: 语义搜索、关键词搜索、混合搜索
- **知识图谱**: 结构化知识提取和关联

## 📁 目录结构

```
src/
├── domain/                     # 🏛️ 领域层 - 核心业务逻辑
│   ├── entities/              # 业务实体
│   │   ├── document.py        # 文档实体
│   │   ├── topic.py           # 主题实体
│   │   └── knowledge_base.py  # 知识库实体
│   ├── value_objects/         # 值对象
│   │   ├── file_metadata.py   # 文件元数据
│   │   └── search_criteria.py # 搜索条件
│   ├── services/              # 领域服务
│   │   └── rag_domain_service.py # RAG 核心业务逻辑
│   └── repositories/          # 仓储接口
│       ├── document_repository.py
│       └── topic_repository.py
│
├── application/               # 🔄 应用层 - 用例编排
│   ├── services/              # 应用服务
│   │   ├── rag_app_service.py # RAG 应用服务
│   │   ├── document_app_service.py
│   │   └── topic_app_service.py
│   ├── dtos/                  # 数据传输对象
│   │   ├── requests/          # 请求 DTOs
│   │   └── responses/         # 响应 DTOs
│   └── workflows/             # 业务工作流
│
├── infrastructure/            # 🔧 基础设施层 - 技术实现
│   ├── rag/                   # RAG 技术实现
│   │   ├── vector_stores/     # 向量数据库
│   │   ├── embeddings/        # 嵌入模型
│   │   ├── retrievers/        # 检索器
│   │   └── processors/        # 文档处理器
│   ├── persistence/           # 数据持久化
│   │   ├── repositories/      # 仓储实现
│   │   └── models/            # ORM 模型
│   └── external_apis/         # 外部 API 集成
│
├── interfaces/                # 🌐 接口层 - API 和 UI
│   └── api/                   # REST API
│       ├── controllers/       # HTTP 控制器
│       │   ├── rag_controller.py
│       │   ├── document_controller.py
│       │   └── topic_controller.py
│       ├── middleware/        # 中间件
│       └── serializers/       # 序列化器
│
├── config.py                  # 📋 统一配置管理
└── main.py                    # 🚀 应用程序入口
```

## 🔄 DDD 分层架构

### 1. 领域层 (Domain Layer)

**职责**: 包含核心业务逻辑，不依赖外部技术

- **实体 (Entities)**: `Document`, `Topic`, `Knowledge`
- **值对象 (Value Objects)**: `FileMetadata`, `SearchCriteria`
- **领域服务 (Domain Services)**: `RAGDomainService`
- **仓储接口 (Repository Interfaces)**: 定义数据访问抽象

### 2. 应用层 (Application Layer)

**职责**: 编排用例，协调领域对象和基础设施

- **应用服务**: 实现具体用例，如文档摄取、知识搜索
- **DTOs**: 定义输入输出数据结构
- **工作流**: 复杂业务流程的编排

### 3. 基础设施层 (Infrastructure Layer)

**职责**: 提供技术实现，实现领域层定义的接口

- **RAG 组件**: 向量数据库、嵌入模型、检索器
- **数据持久化**: 数据库访问、ORM 映射
- **外部集成**: 第三方 API、消息队列

### 4. 接口层 (Interface Layer)

**职责**: 处理外部交互，如 HTTP 请求、UI 渲染

- **REST API**: HTTP 端点和控制器
- **中间件**: 认证、CORS、错误处理
- **序列化**: 请求/响应数据转换

## 🧠 RAG 技术栈

### 向量存储
- **Chroma**: 本地向量数据库
- **Pinecone**: 云向量数据库
- **内存存储**: 开发和测试

### 嵌入模型
- **OpenAI**: `text-embedding-ada-002`
- **Hugging Face**: 开源模型
- **本地模型**: 私有部署

### 检索策略
- **语义检索**: 基于向量相似度
- **关键词检索**: 传统文本搜索
- **混合检索**: 结合语义和关键词

### 文档处理
- **智能分块**: 语义感知的文本切分
- **元数据提取**: 自动提取文件信息
- **多格式支持**: PDF, DOCX, Markdown, TXT

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export OPENAI_API_KEY="your-openai-key"
export VECTOR_STORE_PROVIDER="chroma"
export DB_HOST="localhost"
export DB_NAME="rag_db"
```

### 3. 启动应用

```bash
# 开发模式
python src/main.py

# 或使用 uvicorn
uvicorn src.main:app --reload
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📝 API 端点

### 文档管理
```http
POST /api/v1/rag/documents/ingest    # 文档摄取
POST /api/v1/rag/documents/upload    # 文件上传
POST /api/v1/rag/documents/{id}/knowledge  # 知识提取
```

### 知识搜索
```http
POST /api/v1/rag/search              # 知识搜索
POST /api/v1/rag/content/related     # 相关内容
```

### 系统信息
```http
GET /health                          # 健康检查
GET /info                            # 系统信息
```

## 🔧 配置管理

### 环境变量配置
```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_db
DB_USER=rag_user
DB_PASSWORD=rag_password

# 向量存储配置
VECTOR_STORE_PROVIDER=chroma
VECTOR_STORE_HOST=localhost
VECTOR_STORE_PORT=8000

# 嵌入模型配置
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=your-api-key

# 文档处理配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=100

# 搜索配置
SIMILARITY_THRESHOLD=0.7
ENABLE_HYBRID_SEARCH=true
```

### 代码配置
```python
from src.config import get_config

config = get_config()
print(config.vector_store.provider)  # chroma
print(config.embedding.model_name)   # text-embedding-ada-002
```

## 🧪 测试

### 单元测试
```bash
pytest tests/unit/
```

### 集成测试
```bash
pytest tests/integration/
```

### API 测试
```bash
pytest tests/api/
```

## 📊 监控和日志

### 日志配置
```python
import logging

# 在 config.py 中配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### 性能监控
- **Prometheus**: 指标收集
- **Grafana**: 可视化仪表板
- **健康检查**: `/health` 端点

## 🔄 事件驱动架构

### 领域事件
```python
# 文档处理完成事件
class DocumentProcessedEvent:
    document_id: str
    chunk_count: int
    timestamp: datetime

# 知识提取完成事件
class KnowledgeExtractedEvent:
    document_id: str
    knowledge_items: List[str]
    timestamp: datetime
```

### 事件处理
```python
# 异步事件处理
await event_bus.publish("document.processed", event)
await event_bus.subscribe("knowledge.extracted", handler)
```

## 📈 扩展和自定义

### 添加新的向量存储
```python
# 实现 VectorStore 接口
class CustomVectorStore(VectorStore):
    async def store_embedding(self, ...):
        # 自定义实现
        pass

    async def similarity_search(self, ...):
        # 自定义实现
        pass
```

### 添加新的检索策略
```python
# 在领域服务中添加新策略
class RAGDomainService:
    def add_retrieval_strategy(self, name: str, strategy: callable):
        self.strategies[name] = strategy
```

## 📚 文档和资源

- [架构设计文档](../docs/architecture.md)
- [API 文档](../docs/api.md)
- [部署指南](../docs/deployment.md)
- [开发指南](../docs/development.md)
- [迁移指南](../MIGRATION_GUIDE.md)

## 🤝 贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 📄 许可证

本项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **Domain-Driven Design**: Eric Evans 的 DDD 理论
- **RAG 技术**: OpenAI, Anthropic, Hugging Face
- **开源社区**: FastAPI, Chroma, Pinecone 等优秀项目
