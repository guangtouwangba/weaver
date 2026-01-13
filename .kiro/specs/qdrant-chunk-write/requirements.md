# Requirements Document

## Introduction

实现当 `VECTOR_STORE_PROVIDER=qdrant` 时，文档上传流程中的 chunks 向量数据写入到 Qdrant 而不是 PostgreSQL 的 pgvector。

## Glossary

- **ChunkRepository**: 抽象接口，定义 chunk 数据的存储操作
- **SQLAlchemyChunkRepository**: 当前实现，将 chunks（包括 embedding）存入 PostgreSQL
- **QdrantChunkRepository**: 新实现，将 embedding 存入 Qdrant，metadata 存入 PostgreSQL
- **VectorStore**: 向量存储抽象接口，用于检索
- **VECTOR_STORE_PROVIDER**: 环境变量，控制使用 pgvector 还是 qdrant

## Requirements

### Requirement 1: 创建 Qdrant Chunk Repository

**User Story:** As a developer, I want chunks to be stored in Qdrant when VECTOR_STORE_PROVIDER=qdrant, so that I can use Qdrant for both read and write operations.

#### Acceptance Criteria

1. WHEN `VECTOR_STORE_PROVIDER=qdrant` AND a document is uploaded, THE System SHALL store chunk embeddings in Qdrant
2. WHEN `VECTOR_STORE_PROVIDER=qdrant` AND a document is uploaded, THE System SHALL store chunk metadata (without embedding) in PostgreSQL
3. WHEN `VECTOR_STORE_PROVIDER=qdrant` AND a document is deleted, THE System SHALL delete chunks from both Qdrant and PostgreSQL
4. WHEN `VECTOR_STORE_PROVIDER=pgvector`, THE System SHALL maintain current behavior (all data in PostgreSQL)

### Requirement 2: 创建 ChunkRepository 工厂函数

**User Story:** As a developer, I want a factory function to get the correct ChunkRepository implementation based on configuration, so that the code is clean and follows existing patterns.

#### Acceptance Criteria

1. THE Factory Function SHALL return `QdrantChunkRepository` when `VECTOR_STORE_PROVIDER=qdrant`
2. THE Factory Function SHALL return `SQLAlchemyChunkRepository` when `VECTOR_STORE_PROVIDER=pgvector`
3. THE Factory Function SHALL accept an AsyncSession parameter for database operations

### Requirement 3: 更新 API 端点使用工厂函数

**User Story:** As a developer, I want all document-related API endpoints to use the factory function, so that the correct repository is used based on configuration.

#### Acceptance Criteria

1. WHEN uploading a document via deprecated sync endpoint, THE System SHALL use the factory function to get ChunkRepository
2. WHEN deleting a document, THE System SHALL use the factory function to get ChunkRepository
3. WHEN getting document chunks, THE System SHALL use the factory function to get ChunkRepository

### Requirement 4: 确保 Qdrant Collection 自动创建

**User Story:** As a developer, I want Qdrant collection to be created automatically if it doesn't exist, so that the system works out of the box.

#### Acceptance Criteria

1. WHEN saving chunks to Qdrant AND collection doesn't exist, THE System SHALL create the collection automatically
2. THE System SHALL create payload indexes for `project_id` and `document_id` fields
