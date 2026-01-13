# Change: Integrate Qdrant Vector Database

## Why
当前项目使用 PostgreSQL + pgvector 作为唯一的向量存储方案。虽然 pgvector 对于中小规模数据表现良好，但存在以下局限：
1. **查询性能**：随着 embedding 数据量增长，pgvector 的 ANN 搜索性能会下降，需要依赖 HNSW/IVF 索引调优
2. **功能局限**：不支持原生的 payload 过滤、多向量搜索、稀疏向量等高级特性
3. **运维复杂**：与主数据库共享资源，高并发检索可能影响事务性能

Qdrant 是专为向量搜索设计的数据库，提供：
- 高性能 HNSW 索引，亚毫秒级搜索
- 原生 payload 过滤，无需后处理
- 稀疏向量支持，可用于混合搜索
- 内置 gRPC API，适合高吞吐场景

## What Changes

### 1. Vector Store Provider Factory (Core)
- 创建 `infrastructure/vector_store/factory.py`，实现 provider factory 模式
- 支持通过 `VECTOR_STORE_PROVIDER` 环境变量切换 `pgvector` / `qdrant`
- 保持 `VectorStore` 抽象接口不变，确保向后兼容

### 2. Qdrant Vector Store Implementation
- 新增 `infrastructure/vector_store/qdrant.py`，实现 `QdrantVectorStore` 类
- 继承 `VectorStore` 抽象接口，实现 `search` 和 `hybrid_search` 方法
- 使用 `AsyncQdrantClient` 进行异步操作
- 支持 payload 过滤（project_id, document_id）

### 3. Docker Compose Configuration
- 添加 Qdrant 服务到 `docker-compose.yml`
- 配置持久化存储卷
- 添加健康检查

### 4. Configuration & Environment
- 更新 `config.py` 添加 Qdrant 相关配置（URL、collection name、API key）
- 更新 `.env.example` 文档

### 5. Data Migration Utility
- 提供 pgvector → Qdrant 的数据迁移工具（可选）
- 支持增量同步模式

## Impact

### Affected Specs
- `specs/vector-store` (new capability)

### Affected Code

**Infrastructure Layer:**
- `infrastructure/vector_store/base.py` - 可能需要扩展接口以支持 hybrid_search
- `infrastructure/vector_store/factory.py` (new) - Provider factory
- `infrastructure/vector_store/qdrant.py` (new) - Qdrant implementation

**Configuration:**
- `config.py` - Add Qdrant settings
- `.env.example` - Document new environment variables
- `docker-compose.yml` - Add Qdrant service

**Dependencies:**
- `pyproject.toml` - Add `qdrant-client` dependency

**Use Cases (minimal change):**
- `application/use_cases/chat/stream_message.py` - Already uses factory pattern
- `api/v1/chat.py` - May need to use factory instead of direct PgVectorStore

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Qdrant 服务不可用导致 RAG 功能中断 | 保持 pgvector 作为 fallback；factory 模式支持运行时切换 |
| 数据一致性问题（PostgreSQL chunks vs Qdrant vectors） | 在 document processor 层实现双写；提供一致性检查工具 |
| Collection schema 变更需要重建索引 | 版本化 collection 命名；提供迁移脚本 |
| 开发环境资源占用增加 | Qdrant 可选启动；默认仍使用 pgvector |

## Non-Goals
- 不替换 pgvector，两者并存
- 不实现 Qdrant Cloud 托管版本支持（仅本地部署）
- 不实现跨 provider 的自动数据同步
