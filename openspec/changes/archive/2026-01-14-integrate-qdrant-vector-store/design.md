# Design: Qdrant Vector Store Integration

## Context

### Current Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                       Application Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ stream_message  │  │  chat.py (API)  │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
│           └──────────┬─────────┘                             │
│                      ▼                                       │
│             ┌────────────────┐                               │
│             │  VectorStore   │  (abstract interface)         │
│             │     (base)     │                               │
│             └────────┬───────┘                               │
│                      │                                       │
│                      ▼                                       │
│             ┌────────────────┐                               │
│             │  PgVectorStore │  (only implementation)        │
│             └────────┬───────┘                               │
│                      │                                       │
│                      ▼                                       │
│             ┌────────────────┐                               │
│             │   PostgreSQL   │  (pgvector extension)         │
│             │ document_chunks│                               │
│             └────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                       Application Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ stream_message  │  │  chat.py (API)  │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                             │
│           └──────────┬─────────┘                             │
│                      ▼                                       │
│             ┌────────────────┐                               │
│             │  Factory       │  get_vector_store()           │
│             └────────┬───────┘                               │
│                      │                                       │
│     ┌────────────────┼────────────────┐                      │
│     ▼                ▼                ▼                      │
│ ┌──────────┐   ┌──────────┐    ┌──────────────┐             │
│ │PgVector  │   │ Qdrant   │    │  Future...   │             │
│ │  Store   │   │  Store   │    │ (Weaviate?)  │             │
│ └────┬─────┘   └────┬─────┘    └──────────────┘             │
│      │              │                                        │
│      ▼              ▼                                        │
│ ┌──────────┐   ┌──────────┐                                  │
│ │PostgreSQL│   │  Qdrant  │                                  │
│ │ pgvector │   │  Server  │                                  │
│ └──────────┘   └──────────┘                                  │
└─────────────────────────────────────────────────────────────┘
```

## Goals / Non-Goals

### Goals
1. 实现 Qdrant 向量存储，与 pgvector 功能对等
2. Factory 模式支持运行时切换 provider
3. Docker Compose 一键部署本地 Qdrant
4. 完整的异步支持，符合项目 async-first 设计
5. **应用启动时自动创建 Collection**

### Non-Goals
1. Qdrant Cloud 托管版本（复杂度高，需要单独提案）
2. 自动数据同步（用户自行选择 provider）
3. 多 provider 同时写入（仅单 provider 模式）
4. Qdrant Snapshot/Backup 管理
5. **数据迁移工具**（不在 scope 内）

## Technical Decisions

### Decision 1: Provider Factory Pattern

**选择**: 使用 `get_vector_store(session, provider=None)` 工厂函数

**理由**:
- 简单直接，无需引入 DI 框架
- 与项目现有模式一致（如 `parser/factory.py`, `url_extractor/factory.py`）
- 支持运行时切换，方便测试

**实现**:
```python
# infrastructure/vector_store/factory.py
from research_agent.config import get_settings

def get_vector_store(session: AsyncSession, provider: str | None = None) -> VectorStore:
    settings = get_settings()
    provider = provider or settings.vector_store_provider
    
    if provider == "qdrant":
        from .qdrant import QdrantVectorStore
        return QdrantVectorStore()  # Qdrant is stateless, no session needed
    else:  # default: pgvector
        from .pgvector import PgVectorStore
        return PgVectorStore(session)
```

### Decision 2: Qdrant Collection Schema

**选择**: 使用单一 Collection，通过 payload 过滤

**Schema**:
```json
{
  "collection_name": "document_chunks",
  "vectors": {
    "size": 1536,  // OpenAI text-embedding-3-small
    "distance": "Cosine"
  },
  "payload_schema": {
    "project_id": "keyword",
    "document_id": "keyword",
    "chunk_id": "keyword",
    "content": "text",
    "page_number": "integer"
  }
}
```

**理由**:
- 单 Collection 简化运维
- payload 索引支持高效过滤
- 与 pgvector 数据模型一致

**替代方案 (Rejected)**:
- 每个 project 独立 Collection：运维复杂，Collection 数量爆炸
- 多租户分区：Qdrant CE 不支持

### Decision 3: Hybrid Search Implementation

**选择**: 使用 Qdrant 内置的稀疏向量 + BM25

**实现方式**:
```python
# 方案 A: 仅密集向量 (初期实现)
results = await client.search(
    collection_name="document_chunks",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[FieldCondition(key="project_id", match=MatchValue(value=str(project_id)))]
    ),
    limit=k,
)

# 方案 B: 混合搜索 (后续迭代)
# 需要在 ingestion 时存储稀疏向量
```

**初期实现**: 仅密集向量搜索，与 pgvector 功能对等
**后续迭代**: 添加稀疏向量支持，实现真正的 hybrid search

### Decision 4: Connection Management

**选择**: 使用 Singleton AsyncQdrantClient

**理由**:
- Qdrant client 内部管理连接池
- 无需与 SQLAlchemy session 绑定
- 减少连接开销

**实现**:
```python
_qdrant_client: AsyncQdrantClient | None = None

async def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
        )
    return _qdrant_client
```

### Decision 5: Data Ingestion Strategy

**策略**: 不实现双写。用户选择使用哪个 provider，数据就写入哪个存储。
- 如果使用 `pgvector`：数据存入 PostgreSQL `document_chunks` 表
- 如果使用 `qdrant`：数据存入 Qdrant Collection（需要实现 Qdrant ingestion 路径）

> **Note**: 初期实现仅支持检索，ingestion 仍走 PostgreSQL。后续可扩展 Qdrant ingestion。

## Startup Behavior

### Collection Initialization
应用启动时自动检查并创建 Qdrant Collection：

```python
# 在 app startup 事件中
@app.on_event("startup")
async def init_qdrant():
    if settings.vector_store_provider == "qdrant":
        client = await get_qdrant_client()
        await ensure_collection_exists(client, settings.qdrant_collection_name)
```

**ensure_collection_exists 实现**:
```python
async def ensure_collection_exists(client: AsyncQdrantClient, collection_name: str):
    """Create collection if it doesn't exist."""
    collections = await client.get_collections()
    existing_names = [c.name for c in collections.collections]
    
    if collection_name not in existing_names:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # OpenAI embedding dimension
                distance=Distance.COSINE,
            ),
        )
        # Create payload indexes for efficient filtering
        await client.create_payload_index(
            collection_name=collection_name,
            field_name="project_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        await client.create_payload_index(
            collection_name=collection_name,
            field_name="document_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
```

### Rollback Strategy
- `VECTOR_STORE_PROVIDER=pgvector` 立即切换回 pgvector
- 无需数据迁移，pgvector 数据始终保留
- Qdrant 容器可停止，不影响主系统

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Qdrant 服务宕机 | RAG 功能不可用 | 保持 pgvector 作为 fallback；健康检查 |
| 冷启动延迟 | 首次查询慢 | 应用启动时预创建 Collection |
| 资源占用 | 开发环境变重 | Qdrant 可选启动；配置 profile |

## Open Questions (Resolved)

1. ~~**Collection 初始化时机**: 应用启动时 vs 首次使用时？~~
   - **决定：应用启动时检查并创建**

2. **Embedding 维度变更**: 如果用户切换 embedding 模型？
   - 推荐：Collection 名称包含维度信息，如 `document_chunks_1536`

3. **多环境 Collection 隔离**: dev/staging/prod 如何区分？
   - 推荐：使用 `QDRANT_COLLECTION_NAME` 配置不同名称
