# MVP Backend Architecture

| Document Info | Details |
| --- | --- |
| **Version** | v1.0 |
| **Date** | 2025-11-26 |
| **Status** | Draft |

---

## 1. 技术栈选型

### 核心框架
| 组件 | 技术选型 | 理由 |
|------|----------|------|
| **Web Framework** | FastAPI | 异步支持、自动 OpenAPI 文档、类型安全 |
| **ORM** | SQLAlchemy 2.0 | 成熟稳定、支持异步 |
| **Database** | PostgreSQL + pgvector | 统一存储业务数据和向量，支持 JSONB、全文搜索 |
| **Vector Store** | **pgvector** | 数据可见、支持 SQL 过滤、与 PG 统一、Fly.io 原生支持 |
| **LLM Gateway** | **OpenRouter** | 400+ 模型统一接口、自动故障转移、按需选择最优模型 |
| **Embedding** | OpenAI text-embedding-3-small (via OpenRouter) | 1536 维向量，通过 OpenRouter 调用 |
| **PDF Parser** | PyMuPDF (fitz) | 速度快、支持文本提取和页面信息 |
| **Task Queue** | 无 (MVP 同步处理) | 简化架构，PDF 处理同步完成 |

### 为什么选择 OpenRouter？
| 对比项 | 直接用 OpenAI | OpenRouter |
|--------|---------------|------------|
| 模型选择 | 仅 OpenAI 模型 | ✅ 400+ 模型 (GPT-4, Claude, Gemini, Llama 等) |
| API 格式 | OpenAI 格式 | ✅ 兼容 OpenAI 格式，迁移成本低 |
| 故障转移 | ❌ 需自己实现 | ✅ 自动切换备用供应商 |
| 成本控制 | 固定价格 | ✅ 可选最便宜的模型，按需切换 |
| 供应商锁定 | 绑定 OpenAI | ✅ 随时切换模型供应商 |

### 为什么选择 pgvector 而不是 FAISS？
| 对比项 | FAISS | pgvector |
|--------|-------|----------|
| 数据可见性 | ❌ 二进制文件，无法直接查看 | ✅ SQL 可查询，方便调试 |
| 元数据过滤 | ❌ 不支持 | ✅ `WHERE project_id = ?` |
| 部署复杂度 | 需要额外管理索引文件 | ✅ 与数据库统一 |
| 数据迁移 | ❌ 需要重建索引 | ✅ pg_dump 即可 |
| Fly.io 支持 | 需要 Volume 存储 | ✅ 原生 Postgres 扩展 |

### 项目结构 (Clean Architecture + DDD)

采用**分层架构**，确保关注点分离、可测试性和可扩展性：

```
app/
├── backend/
│   ├── pyproject.toml              # 依赖管理 (Poetry/PDM)
│   ├── alembic/                    # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/                      # 测试
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   └── src/
│       └── research_agent/         # 主包
│           ├── __init__.py
│           │
│           ├── main.py             # FastAPI 入口 (组装所有组件)
│           ├── config.py           # 配置管理 (pydantic-settings)
│           │
│           │ ══════════════════════════════════════════════════
│           │ 【表现层 Presentation Layer】- HTTP 接口
│           │ ══════════════════════════════════════════════════
│           ├── api/
│           │   ├── __init__.py
│           │   ├── deps.py             # 依赖注入 (get_db, get_current_user)
│           │   ├── errors.py           # 统一错误处理
│           │   ├── middleware.py       # 中间件 (CORS, Logging, RateLimit)
│           │   │
│           │   └── v1/                 # API 版本控制
│           │       ├── __init__.py
│           │       ├── router.py       # 路由聚合
│           │       ├── projects.py     # /api/v1/projects
│           │       ├── documents.py    # /api/v1/documents
│           │       ├── chat.py         # /api/v1/chat
│           │       └── canvas.py       # /api/v1/canvas
│           │
│           │ ══════════════════════════════════════════════════
│           │ 【应用层 Application Layer】- 用例编排
│           │ ══════════════════════════════════════════════════
│           ├── application/
│           │   ├── __init__.py
│           │   │
│           │   ├── dto/                # Data Transfer Objects (API 请求/响应)
│           │   │   ├── __init__.py
│           │   │   ├── project.py
│           │   │   ├── document.py
│           │   │   ├── chat.py
│           │   │   └── canvas.py
│           │   │
│           │   └── use_cases/          # 业务用例 (一个用例 = 一个业务操作)
│           │       ├── __init__.py
│           │       ├── project/
│           │       │   ├── create_project.py
│           │       │   ├── list_projects.py
│           │       │   └── delete_project.py
│           │       ├── document/
│           │       │   ├── upload_document.py
│           │       │   ├── process_document.py  # PDF 解析 + 向量化
│           │       │   └── delete_document.py
│           │       ├── chat/
│           │       │   ├── send_message.py      # RAG 对话
│           │       │   └── stream_message.py    # 流式对话
│           │       └── canvas/
│           │           ├── get_canvas.py
│           │           └── save_canvas.py
│           │
│           │ ══════════════════════════════════════════════════
│           │ 【领域层 Domain Layer】- 核心业务逻辑
│           │ ══════════════════════════════════════════════════
│           ├── domain/
│           │   ├── __init__.py
│           │   │
│           │   ├── entities/           # 领域实体 (纯 Python 类，无框架依赖)
│           │   │   ├── __init__.py
│           │   │   ├── project.py      # Project 实体
│           │   │   ├── document.py     # Document 实体
│           │   │   ├── chunk.py        # DocumentChunk 实体
│           │   │   └── canvas.py       # Canvas 实体 (Node, Edge)
│           │   │
│           │   ├── value_objects/      # 值对象 (不可变)
│           │   │   ├── __init__.py
│           │   │   ├── embedding.py    # Embedding 向量
│           │   │   └── file_path.py    # 文件路径
│           │   │
│           │   ├── repositories/       # 仓储接口 (抽象)
│           │   │   ├── __init__.py
│           │   │   ├── project_repo.py
│           │   │   ├── document_repo.py
│           │   │   ├── chunk_repo.py
│           │   │   └── canvas_repo.py
│           │   │
│           │   ├── services/           # 领域服务 (跨实体的业务逻辑)
│           │   │   ├── __init__.py
│           │   │   ├── chunking_service.py     # 文本切片策略
│           │   │   └── retrieval_service.py    # 检索策略
│           │   │
│           │   └── events/             # 领域事件 (可选，用于解耦)
│           │       ├── __init__.py
│           │       └── document_events.py      # DocumentUploaded, DocumentProcessed
│           │
│           │ ══════════════════════════════════════════════════
│           │ 【基础设施层 Infrastructure Layer】- 外部依赖实现
│           │ ══════════════════════════════════════════════════
│           ├── infrastructure/
│           │   ├── __init__.py
│           │   │
│           │   ├── database/           # 数据库相关
│           │   │   ├── __init__.py
│           │   │   ├── session.py      # SQLAlchemy 会话管理
│           │   │   ├── models.py       # ORM 模型 (SQLAlchemy)
│           │   │   └── repositories/   # 仓储实现
│           │   │       ├── __init__.py
│           │   │       ├── sqlalchemy_project_repo.py
│           │   │       ├── sqlalchemy_document_repo.py
│           │   │       ├── sqlalchemy_chunk_repo.py
│           │   │       └── sqlalchemy_canvas_repo.py
│           │   │
│           │   ├── vector_store/       # 向量存储
│           │   │   ├── __init__.py
│           │   │   ├── base.py         # 抽象接口
│           │   │   └── pgvector.py     # pgvector 实现
│           │   │
│           │   ├── llm/                # LLM 集成
│           │   │   ├── __init__.py
│           │   │   ├── base.py         # 抽象接口 (方便切换 LLM)
│           │   │   ├── openai.py       # OpenAI 实现
│           │   │   └── prompts/        # Prompt 模板
│           │   │       ├── __init__.py
│           │   │       └── rag_prompt.py
│           │   │
│           │   ├── embedding/          # Embedding 服务
│           │   │   ├── __init__.py
│           │   │   ├── base.py         # 抽象接口
│           │   │   └── openai.py       # OpenAI Embedding
│           │   │
│           │   ├── pdf/                # PDF 处理
│           │   │   ├── __init__.py
│           │   │   ├── base.py         # 抽象接口
│           │   │   └── pymupdf.py      # PyMuPDF 实现
│           │   │
│           │   └── storage/            # 文件存储
│           │       ├── __init__.py
│           │       ├── base.py         # 抽象接口
│           │       ├── local.py        # 本地存储
│           │       └── s3.py           # S3 存储 (可选)
│           │
│           │ ══════════════════════════════════════════════════
│           │ 【共享内核 Shared Kernel】- 通用工具
│           │ ══════════════════════════════════════════════════
│           └── shared/
│               ├── __init__.py
│               ├── types.py            # 通用类型定义 (UUID, Timestamp)
│               ├── exceptions.py       # 自定义异常
│               └── utils/
│                   ├── __init__.py
│                   ├── logger.py       # 日志配置
│                   └── security.py     # 安全工具 (哈希、JWT)
│
├── frontend/               # Next.js 前端 (已有)
└── docker-compose.yml      # 本地开发环境
```

### 架构分层说明

| 层级 | 职责 | 依赖方向 |
|------|------|----------|
| **Presentation (API)** | HTTP 路由、请求验证、响应格式化 | → Application |
| **Application** | 用例编排、事务管理、DTO 转换 | → Domain |
| **Domain** | 核心业务逻辑、实体、仓储接口 | 无外部依赖 |
| **Infrastructure** | 数据库、LLM、存储等外部服务实现 | → Domain (实现接口) |

**依赖规则**：外层依赖内层，内层不知道外层的存在。Domain 层是纯净的业务逻辑，不依赖任何框架。

### 关键设计模式

1. **Repository Pattern** - 数据访问抽象，Domain 定义接口，Infrastructure 实现
2. **Use Case Pattern** - 每个业务操作封装为独立类，单一职责
3. **Dependency Injection** - FastAPI 的 Depends 实现依赖注入
4. **DTO Pattern** - API 层与 Domain 层数据隔离
5. **Strategy Pattern** - LLM/Embedding/Storage 可插拔替换

---

## 2. 数据模型设计

### 2.1 Project (项目)
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2.2 Document (文档)
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,      -- 存储路径
    file_size INTEGER,
    page_count INTEGER,
    status VARCHAR(50) DEFAULT 'processing', -- processing | ready | error
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2.3 DocumentChunk (文档切片 - 用于 RAG)
```sql
-- 首先启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,  -- 冗余字段，方便按项目过滤
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    embedding VECTOR(1536),  -- pgvector 向量类型，1536 维 (text-embedding-3-small)
    metadata JSONB,          -- 额外元数据
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建向量索引 (IVFFlat 适合中小规模数据)
CREATE INDEX ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 创建项目过滤索引
CREATE INDEX ON document_chunks (project_id);
```

**向量检索 SQL 示例：**
```sql
-- 在指定项目中检索最相似的 5 个切片
SELECT id, content, page_number, 
       1 - (embedding <=> $1) AS similarity  -- 余弦相似度
FROM document_chunks
WHERE project_id = $2
ORDER BY embedding <=> $1  -- <=> 是 pgvector 的余弦距离运算符
LIMIT 5;
```

### 2.4 Canvas (画布数据)
```sql
CREATE TABLE canvases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    data JSONB NOT NULL,     -- 存储节点和连线的完整 JSON
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Canvas JSON 结构示例：**
```json
{
  "nodes": [
    {
      "id": "c1",
      "type": "card",
      "title": "Self-Attention",
      "content": "The core mechanism...",
      "x": 100,
      "y": 200,
      "color": "blue",
      "tags": ["#transformer"],
      "sourceId": "doc-uuid",
      "sourcePage": 3
    }
  ],
  "edges": [
    { "source": "c1", "target": "c2" }
  ],
  "viewport": { "x": 0, "y": 0, "scale": 1 }
}
```

---

## 3. API 接口设计

### 3.1 Projects API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects` | 获取项目列表 |
| `POST` | `/api/projects` | 创建新项目 |
| `GET` | `/api/projects/{id}` | 获取项目详情 |
| `PUT` | `/api/projects/{id}` | 更新项目 |
| `DELETE` | `/api/projects/{id}` | 删除项目 |

**Request/Response 示例：**
```typescript
// POST /api/projects
Request: { "name": "Transformer Research" }
Response: { "id": "uuid", "name": "...", "created_at": "..." }

// GET /api/projects
Response: {
  "items": [
    { "id": "uuid", "name": "...", "updated_at": "...", "document_count": 3 }
  ]
}
```

---

### 3.2 Documents API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects/{id}/documents` | 获取项目下的文档列表 |
| `POST` | `/api/projects/{id}/documents` | 上传 PDF 文件 |
| `GET` | `/api/documents/{id}` | 获取文档详情 |
| `DELETE` | `/api/documents/{id}` | 删除文档 |
| `GET` | `/api/documents/{id}/content` | 获取文档全文 (用于前端渲染) |

**上传流程：**
```
1. 前端 POST multipart/form-data 上传 PDF
2. 后端保存文件到 storage (本地/S3)
3. 后端同步解析 PDF → 提取文本 → 切片 → 向量化 → 存入 FAISS
4. 返回 document 对象 (status: ready)
```

**Request/Response 示例：**
```typescript
// POST /api/projects/{id}/documents (multipart/form-data)
Request: file: <binary>
Response: { 
  "id": "uuid", 
  "filename": "attention.pdf", 
  "page_count": 15, 
  "status": "ready" 
}
```

---

### 3.3 Chat API (RAG)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/projects/{id}/chat` | 基于项目文档的 RAG 对话 |
| `POST` | `/api/projects/{id}/chat/stream` | 流式输出版本 (SSE) |

**RAG 流程：**
```
1. 用户发送 query
2. 将 query 向量化
3. 在项目的所有文档 chunks 中检索 Top-K 相似片段
4. 构建 Prompt: System + Retrieved Context + User Query
5. 调用 LLM 生成回答
6. 返回回答 + 引用来源
```

**Request/Response 示例：**
```typescript
// POST /api/projects/{id}/chat
Request: { 
  "message": "What is self-attention?",
  "document_id": "uuid"  // 可选：限制在特定文档内
}
Response: { 
  "answer": "Self-attention is a mechanism...",
  "sources": [
    { "document_id": "uuid", "page": 3, "snippet": "..." }
  ]
}

// POST /api/projects/{id}/chat/stream (SSE)
Request: { "message": "Summarize this paper" }
Response: Server-Sent Events stream
  data: {"type": "token", "content": "Self"}
  data: {"type": "token", "content": "-attention"}
  data: {"type": "done", "sources": [...]}
```

---

### 3.4 Canvas API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects/{id}/canvas` | 获取画布数据 |
| `PUT` | `/api/projects/{id}/canvas` | 保存画布数据 |

**Request/Response 示例：**
```typescript
// GET /api/projects/{id}/canvas
Response: {
  "nodes": [...],
  "edges": [...],
  "viewport": { "x": 0, "y": 0, "scale": 1 }
}

// PUT /api/projects/{id}/canvas
Request: {
  "nodes": [...],
  "edges": [...],
  "viewport": { "x": 100, "y": 50, "scale": 0.8 }
}
Response: { "success": true, "updated_at": "..." }
```

---

## 4. 核心代码示例 (Clean Architecture 风格)

### 4.1 Domain Layer - 实体与仓储接口

```python
# src/research_agent/domain/entities/document.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

@dataclass
class Document:
    """文档领域实体 - 纯业务逻辑，无框架依赖"""
    id: UUID = field(default_factory=uuid4)
    project_id: UUID = None
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    page_count: int = 0
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def mark_processing(self) -> None:
        self.status = DocumentStatus.PROCESSING
    
    def mark_ready(self, page_count: int) -> None:
        self.page_count = page_count
        self.status = DocumentStatus.READY
    
    def mark_error(self) -> None:
        self.status = DocumentStatus.ERROR
```

```python
# src/research_agent/domain/repositories/document_repo.py
from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional, List
from ..entities.document import Document

class DocumentRepository(ABC):
    """文档仓储接口 - 定义在 Domain 层，实现在 Infrastructure 层"""
    
    @abstractmethod
    async def save(self, document: Document) -> Document:
        """保存文档"""
        pass
    
    @abstractmethod
    async def find_by_id(self, doc_id: UUID) -> Optional[Document]:
        """根据 ID 查找"""
        pass
    
    @abstractmethod
    async def find_by_project(self, project_id: UUID) -> List[Document]:
        """查找项目下所有文档"""
        pass
    
    @abstractmethod
    async def delete(self, doc_id: UUID) -> bool:
        """删除文档"""
        pass
```

### 4.2 Application Layer - Use Case

```python
# src/research_agent/application/use_cases/document/upload_document.py
from dataclasses import dataclass
from uuid import UUID
from typing import BinaryIO

from ....domain.entities.document import Document
from ....domain.repositories.document_repo import DocumentRepository
from ....infrastructure.storage.base import StorageService
from ....infrastructure.pdf.base import PDFParser
from ....infrastructure.embedding.base import EmbeddingService
from ....domain.repositories.chunk_repo import ChunkRepository

@dataclass
class UploadDocumentInput:
    project_id: UUID
    filename: str
    file_content: BinaryIO

@dataclass
class UploadDocumentOutput:
    document_id: UUID
    filename: str
    page_count: int
    status: str

class UploadDocumentUseCase:
    """上传文档用例 - 编排多个服务完成业务操作"""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        storage: StorageService,
        pdf_parser: PDFParser,
        embedding_service: EmbeddingService,
    ):
        self._document_repo = document_repo
        self._chunk_repo = chunk_repo
        self._storage = storage
        self._pdf_parser = pdf_parser
        self._embedding_service = embedding_service
    
    async def execute(self, input: UploadDocumentInput) -> UploadDocumentOutput:
        # 1. 创建文档实体
        document = Document(
            project_id=input.project_id,
            filename=input.filename,
        )
        document.mark_processing()
        
        # 2. 保存文件到存储
        file_path = await self._storage.save(
            f"projects/{input.project_id}/{document.id}.pdf",
            input.file_content
        )
        document.file_path = file_path
        
        # 3. 解析 PDF
        pages = await self._pdf_parser.extract_text(file_path)
        
        # 4. 切片并向量化
        chunks = self._create_chunks(pages, document.id, input.project_id)
        embeddings = await self._embedding_service.embed_batch(
            [c.content for c in chunks]
        )
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # 5. 保存切片
        await self._chunk_repo.save_batch(chunks)
        
        # 6. 更新文档状态
        document.mark_ready(page_count=len(pages))
        await self._document_repo.save(document)
        
        return UploadDocumentOutput(
            document_id=document.id,
            filename=document.filename,
            page_count=document.page_count,
            status=document.status.value,
        )
    
    def _create_chunks(self, pages, document_id, project_id):
        # 切片逻辑...
        pass
```

### 4.3 Infrastructure Layer - 仓储实现

```python
# src/research_agent/infrastructure/database/repositories/sqlalchemy_document_repo.py
from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ....domain.entities.document import Document, DocumentStatus
from ....domain.repositories.document_repo import DocumentRepository
from ..models import DocumentModel

class SQLAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy 实现的文档仓储"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, document: Document) -> Document:
        model = self._to_model(document)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)
    
    async def find_by_id(self, doc_id: UUID) -> Optional[Document]:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def find_by_project(self, project_id: UUID) -> List[Document]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.project_id == project_id)
            .order_by(DocumentModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars()]
    
    async def delete(self, doc_id: UUID) -> bool:
        result = await self._session.execute(
            select(DocumentModel).where(DocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False
    
    def _to_model(self, entity: Document) -> DocumentModel:
        return DocumentModel(
            id=entity.id,
            project_id=entity.project_id,
            filename=entity.filename,
            file_path=entity.file_path,
            file_size=entity.file_size,
            page_count=entity.page_count,
            status=entity.status.value,
            created_at=entity.created_at,
        )
    
    def _to_entity(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            project_id=model.project_id,
            filename=model.filename,
            file_path=model.file_path,
            file_size=model.file_size,
            page_count=model.page_count,
            status=DocumentStatus(model.status),
            created_at=model.created_at,
        )
```

### 4.4 Infrastructure Layer - LLM 抽象 (OpenRouter)

```python
# src/research_agent/infrastructure/llm/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
from enum import Enum

class ModelProvider(str, Enum):
    """支持的模型供应商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta-llama"

@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str

@dataclass
class ChatResponse:
    content: str
    model: str  # 实际使用的模型
    usage: dict  # {"prompt_tokens": ..., "completion_tokens": ...}
    cost: Optional[float] = None  # OpenRouter 返回的成本

class LLMService(ABC):
    """LLM 服务抽象接口"""
    
    @abstractmethod
    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """同步对话"""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        """流式对话"""
        pass
```

```python
# src/research_agent/infrastructure/llm/openrouter.py
from typing import AsyncIterator, List, Optional
from openai import AsyncOpenAI
import httpx

from .base import LLMService, ChatMessage, ChatResponse

# OpenRouter 推荐的模型 (按成本从低到高)
OPENROUTER_MODELS = {
    # 便宜快速 - 适合简单任务
    "cheap": "meta-llama/llama-3.2-3b-instruct:free",  # 免费
    "fast": "google/gemini-flash-1.5-8b",              # $0.0375/1M tokens
    
    # 平衡 - 适合大多数场景 (MVP 推荐)
    "balanced": "anthropic/claude-3.5-haiku",          # $0.80/1M input
    "default": "openai/gpt-4o-mini",                   # $0.15/1M input
    
    # 高质量 - 适合复杂推理
    "quality": "anthropic/claude-3.5-sonnet",          # $3/1M input
    "best": "openai/gpt-4o",                           # $2.50/1M input
}

class OpenRouterLLMService(LLMService):
    """
    OpenRouter 实现 - 统一接口访问 400+ 模型
    
    优势:
    - 兼容 OpenAI SDK，迁移成本低
    - 自动故障转移
    - 按需选择模型
    """
    
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "openai/gpt-4o-mini",
        site_url: Optional[str] = None,      # 你的网站 URL (用于 OpenRouter 统计)
        site_name: Optional[str] = None,     # 你的应用名称
    ):
        self._api_key = api_key
        self._model = model
        self._site_url = site_url
        self._site_name = site_name
        
        # 使用 OpenAI SDK，只需修改 base_url
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,
            default_headers=self._get_headers(),
        )
    
    def _get_headers(self) -> dict:
        """OpenRouter 推荐的额外 headers"""
        headers = {}
        if self._site_url:
            headers["HTTP-Referer"] = self._site_url
        if self._site_name:
            headers["X-Title"] = self._site_name
        return headers
    
    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        
        return ChatResponse(
            content=response.choices[0].message.content,
            model=response.model,  # OpenRouter 返回实际使用的模型
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )
    
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def with_model(self, model: str) -> "OpenRouterLLMService":
        """切换模型 (返回新实例)"""
        return OpenRouterLLMService(
            api_key=self._api_key,
            model=model,
            site_url=self._site_url,
            site_name=self._site_name,
        )


# 便捷工厂函数
def create_llm_service(
    api_key: str,
    tier: str = "default",  # "cheap" | "fast" | "balanced" | "default" | "quality" | "best"
) -> OpenRouterLLMService:
    """根据需求创建 LLM 服务"""
    model = OPENROUTER_MODELS.get(tier, OPENROUTER_MODELS["default"])
    return OpenRouterLLMService(
        api_key=api_key,
        model=model,
        site_name="Research Agent RAG",
    )
```

```python
# src/research_agent/infrastructure/embedding/openrouter.py
from typing import List
from openai import AsyncOpenAI

class OpenRouterEmbeddingService:
    """
    通过 OpenRouter 调用 Embedding 模型
    
    支持的模型:
    - openai/text-embedding-3-small (1536 维, $0.02/1M tokens)
    - openai/text-embedding-3-large (3072 维, $0.13/1M tokens)
    """
    
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "openai/text-embedding-3-small"
    ):
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,
        )
        self._model = model
    
    async def embed(self, text: str) -> List[float]:
        """获取单个文本的向量"""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取向量"""
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]
```

### 4.5 API Layer - 路由与依赖注入

```python
# src/research_agent/api/v1/documents.py
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from ...application.dto.document import DocumentResponse, DocumentListResponse
from ...application.use_cases.document.upload_document import (
    UploadDocumentUseCase, 
    UploadDocumentInput
)
from ..deps import get_upload_document_use_case

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

@router.post("", response_model=DocumentResponse)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case),
):
    """上传 PDF 文档"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    
    result = await use_case.execute(
        UploadDocumentInput(
            project_id=project_id,
            filename=file.filename,
            file_content=file.file,
        )
    )
    
    return DocumentResponse(
        id=result.document_id,
        filename=result.filename,
        page_count=result.page_count,
        status=result.status,
    )
```

```python
# src/research_agent/api/deps.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.database.session import get_session
from ..infrastructure.database.repositories.sqlalchemy_document_repo import SQLAlchemyDocumentRepository
from ..infrastructure.database.repositories.sqlalchemy_chunk_repo import SQLAlchemyChunkRepository
from ..infrastructure.storage.local import LocalStorageService
from ..infrastructure.pdf.pymupdf import PyMuPDFParser
from ..infrastructure.embedding.openai import OpenAIEmbeddingService
from ..application.use_cases.document.upload_document import UploadDocumentUseCase
from ..config import settings

async def get_upload_document_use_case(
    session: AsyncSession = Depends(get_session),
) -> UploadDocumentUseCase:
    """依赖注入 - 组装 Use Case 所需的所有依赖"""
    return UploadDocumentUseCase(
        document_repo=SQLAlchemyDocumentRepository(session),
        chunk_repo=SQLAlchemyChunkRepository(session),
        storage=LocalStorageService(settings.UPLOAD_DIR),
        pdf_parser=PyMuPDFParser(),
        embedding_service=OpenRouterEmbeddingService(settings.OPENROUTER_API_KEY),
    )

async def get_llm_service() -> OpenRouterLLMService:
    """获取 LLM 服务"""
    return OpenRouterLLMService(
        api_key=settings.OPENROUTER_API_KEY,
        model=settings.LLM_MODEL,
        site_name="Research Agent RAG",
    )
```

---

## 5. 环境变量配置

```bash
# .env
# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/research_rag

# OpenRouter (替代直接调用 OpenAI)
OPENROUTER_API_KEY=sk-or-v1-xxx
# 可选：指定默认模型
LLM_MODEL=openai/gpt-4o-mini
EMBEDDING_MODEL=openai/text-embedding-3-small

# Storage (PDF 文件存储)
UPLOAD_DIR=./data/uploads

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-frontend.fly.dev

# Optional
LOG_LEVEL=INFO
```

### OpenRouter 模型推荐 (MVP)

| 用途 | 推荐模型 | 价格 |
|------|----------|------|
| **RAG 对话** | `openai/gpt-4o-mini` | $0.15/1M input |
| **备选便宜** | `google/gemini-flash-1.5-8b` | $0.0375/1M input |
| **备选免费** | `meta-llama/llama-3.2-3b-instruct:free` | 免费 |
| **Embedding** | `openai/text-embedding-3-small` | $0.02/1M tokens |

**获取 API Key**: https://openrouter.ai/keys

## 5.1 Fly.io PostgreSQL + pgvector 配置

```bash
# 1. 创建 Fly Postgres 集群
fly postgres create --name research-rag-db

# 2. 连接到数据库
fly postgres connect -a research-rag-db

# 3. 启用 pgvector 扩展 (在 psql 中执行)
CREATE EXTENSION IF NOT EXISTS vector;

# 4. 验证安装
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**注意**：Fly.io 的 PostgreSQL 镜像已预装 pgvector，只需 `CREATE EXTENSION` 即可。

---

## 6. MVP 开发优先级

### Phase 1: 基础 CRUD (1-2 天)
- [ ] 项目管理 API (Projects CRUD)
- [ ] 数据库初始化脚本
- [ ] 基础 FastAPI 骨架

### Phase 2: PDF 处理 (2-3 天)
- [ ] 文件上传接口
- [ ] PDF 文本提取
- [ ] 文本切片与向量化
- [ ] 向量存入 pgvector

### Phase 3: RAG 对话 (2-3 天)
- [ ] 向量检索
- [ ] LLM 调用与 Prompt 工程
- [ ] 流式输出 (SSE)

### Phase 4: 画布持久化 (1 天)
- [ ] Canvas CRUD API
- [ ] 前端对接

---

## 7. 部署架构 (Fly.io)

```
┌─────────────────────────────────────────────────────────┐
│                      Fly.io                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Frontend   │    │   API       │    │  PostgreSQL │  │
│  │  (Next.js)  │───▶│  (FastAPI)  │───▶│  (Fly PG)   │  │
│  │  Port 3000  │    │  Port 8000  │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                            │                             │
│                            ▼                             │
│                     ┌─────────────┐                      │
│                     │   Volume    │                      │
│                     │  (uploads)  │                      │
│                     └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   OpenAI    │
                     │     API     │
                     └─────────────┘
```

---

## 8. 架构优势

| 特性 | 好处 |
|------|------|
| **分层架构** | 关注点分离，每层职责清晰 |
| **依赖倒置** | Domain 层不依赖框架，纯业务逻辑可独立测试 |
| **Use Case 模式** | 每个业务操作独立封装，易于理解和维护 |
| **Repository 模式** | 数据访问抽象，可轻松切换数据库实现 |
| **策略模式** | LLM/Embedding/Storage 可插拔，方便切换供应商 |
| **API 版本控制** | `/api/v1/` 前缀，支持未来 API 演进 |
| **依赖注入** | 组件解耦，方便单元测试 mock |

---

## 9. 下一步行动

1. **创建后端项目骨架** - 按照 Clean Architecture 结构初始化
2. **配置开发环境** - Poetry + Docker Compose (PostgreSQL + pgvector)
3. **实现 Domain 层** - 定义实体和仓储接口
4. **实现 Infrastructure 层** - SQLAlchemy 模型和仓储实现
5. **实现 Projects Use Case** - 先跑通最简单的 CRUD
6. **实现 PDF 上传 Use Case** - 文件存储 + 文本提取 + 向量化
7. **实现 RAG Chat Use Case** - 核心价值验证
8. **实现 Canvas Use Case** - 数据持久化
9. **前后端联调** - 打通完整流程

