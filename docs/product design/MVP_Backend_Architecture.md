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
| **LLM** | OpenAI GPT-4o-mini | 成本低、速度快、足够 MVP 验证 |
| **Embedding** | OpenAI text-embedding-3-small | 1536 维向量，与 LLM 统一供应商 |
| **PDF Parser** | PyMuPDF (fitz) | 速度快、支持文本提取和页面信息 |
| **Task Queue** | 无 (MVP 同步处理) | 简化架构，PDF 处理同步完成 |

### 为什么选择 pgvector 而不是 FAISS？
| 对比项 | FAISS | pgvector |
|--------|-------|----------|
| 数据可见性 | ❌ 二进制文件，无法直接查看 | ✅ SQL 可查询，方便调试 |
| 元数据过滤 | ❌ 不支持 | ✅ `WHERE project_id = ?` |
| 部署复杂度 | 需要额外管理索引文件 | ✅ 与数据库统一 |
| 数据迁移 | ❌ 需要重建索引 | ✅ pg_dump 即可 |
| Fly.io 支持 | 需要 Volume 存储 | ✅ 原生 Postgres 扩展 |

### 项目结构
```
app/
├── api/                    # FastAPI 应用
│   ├── __init__.py
│   ├── main.py             # FastAPI 入口
│   ├── config.py           # 配置管理
│   ├── dependencies.py     # 依赖注入
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── projects.py     # 项目 CRUD
│   │   ├── documents.py    # PDF 上传与管理
│   │   ├── chat.py         # RAG 对话
│   │   └── canvas.py       # 画布数据
│   ├── models/             # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── document.py
│   │   └── canvas.py
│   ├── schemas/            # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── chat.py
│   │   └── canvas.py
│   └── services/           # 业务逻辑
│       ├── __init__.py
│       ├── pdf_service.py      # PDF 解析与切片
│       ├── embedding_service.py # 向量化
│       ├── rag_service.py      # RAG 检索与生成
│       └── storage_service.py  # 文件存储
├── frontend/               # Next.js 前端 (已有)
└── shared/                 # 共享代码 (如有)
```

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

## 4. 核心服务实现要点

### 4.1 PDF 处理服务 (`pdf_service.py`)
```python
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path: str) -> list[dict]:
    """提取 PDF 文本，按页返回"""
    doc = fitz.open(file_path)
    pages = []
    for page_num, page in enumerate(doc):
        text = page.get_text()
        pages.append({
            "page_number": page_num + 1,
            "content": text
        })
    return pages

def chunk_text(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """将文本切片，保留页码信息"""
    chunks = []
    for page in pages:
        # 简单按字符切片，可优化为按句子/段落
        text = page["content"]
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append({
                "content": text[i:i + chunk_size],
                "page_number": page["page_number"]
            })
    return chunks
```

### 4.2 RAG 服务 (`rag_service.py`)
```python
from openai import OpenAI

SYSTEM_PROMPT = """You are a research assistant. Answer questions based on the provided context.
If the answer is not in the context, say "I don't have enough information to answer this."
Always cite the source page numbers when possible."""

async def generate_answer(query: str, context_chunks: list[dict]) -> dict:
    """基于检索到的上下文生成回答"""
    context = "\n\n".join([
        f"[Page {c['page_number']}]: {c['content']}" 
        for c in context_chunks
    ])
    
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ],
        stream=False
    )
    
    return {
        "answer": response.choices[0].message.content,
        "sources": [{"page": c["page_number"], "snippet": c["content"][:100]} for c in context_chunks]
    }
```

### 4.3 向量检索 (`embedding_service.py`)
```python
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

client = OpenAI()

def get_embedding(text: str) -> list[float]:
    """获取文本的向量表示"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

async def search_similar_chunks(
    db: AsyncSession, 
    query_embedding: list[float], 
    project_id: str, 
    k: int = 5
) -> list[dict]:
    """使用 pgvector 在指定项目中检索最相似的切片"""
    
    # 将 embedding 转换为 pgvector 格式
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    result = await db.execute(
        text("""
            SELECT id, content, page_number, document_id,
                   1 - (embedding <=> :embedding) AS similarity
            FROM document_chunks
            WHERE project_id = :project_id
            ORDER BY embedding <=> :embedding
            LIMIT :k
        """),
        {
            "embedding": embedding_str,
            "project_id": project_id,
            "k": k
        }
    )
    
    rows = result.fetchall()
    return [
        {
            "id": str(row.id),
            "content": row.content,
            "page_number": row.page_number,
            "document_id": str(row.document_id),
            "similarity": float(row.similarity)
        }
        for row in rows
    ]
```

---

## 5. 环境变量配置

```bash
# .env
# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/research_rag

# OpenAI
OPENAI_API_KEY=sk-xxx

# Storage (PDF 文件存储)
UPLOAD_DIR=./data/uploads

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-frontend.fly.dev

# Optional
LOG_LEVEL=INFO
```

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

## 8. 下一步行动

1. **创建后端项目骨架** - FastAPI + SQLAlchemy 基础结构
2. **实现 Projects API** - 先跑通最简单的 CRUD
3. **实现 PDF 上传** - 文件存储 + 文本提取
4. **实现 RAG Chat** - 核心价值验证
5. **实现 Canvas API** - 数据持久化
6. **前后端联调** - 打通完整流程

