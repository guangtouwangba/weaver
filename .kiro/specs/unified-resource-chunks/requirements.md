# Requirements Document

## Introduction

统一所有资源类型（Document、URL Content、未来的 Note 等）的 chunk 存储和检索架构。所有资源的内容都通过统一的 `ResourceChunk` 存储，支持语义检索，通过 metadata 区分资源类型。

## Glossary

- **Resource**: 统一的内容抽象，包括 Document、Video、Article、Note 等
- **ResourceChunk**: 统一的 chunk 实体，替代原有的 DocumentChunk
- **ResourceType**: 资源类型枚举（document, video, audio, web_page, note 等）
- **VectorStore**: 向量存储抽象（Qdrant 或 pgvector）

## Requirements

### Requirement 1: 统一的 ResourceChunk 实体

**User Story:** As a developer, I want a unified chunk entity that can represent content from any resource type, so that all content can be stored and retrieved consistently.

#### Acceptance Criteria

1. THE ResourceChunk entity SHALL contain: id, resource_id, resource_type, project_id, chunk_index, content, embedding, metadata
2. THE ResourceChunk metadata SHALL include: title, platform, page_number (for documents), timestamp (for video/audio)
3. THE ResourceChunk SHALL support all ResourceType values: document, video, audio, web_page, note

### Requirement 2: 统一的 ChunkRepository 接口

**User Story:** As a developer, I want a single repository interface for all chunk operations, so that I don't need different code paths for different resource types.

#### Acceptance Criteria

1. THE ChunkRepository interface SHALL support save_batch, find_by_resource, delete_by_resource, search operations
2. THE search method SHALL support filtering by project_id, resource_type, and resource_id
3. THE ChunkRepository SHALL work with both Qdrant and pgvector backends

### Requirement 3: 统一的 Chunking Service

**User Story:** As a developer, I want a unified chunking service that can process any resource type, so that all content is chunked consistently.

#### Acceptance Criteria

1. THE ChunkingService SHALL accept Resource entity as input
2. THE ChunkingService SHALL apply appropriate chunking strategy based on ResourceType
3. WHEN chunking video/audio content, THE ChunkingService SHALL preserve timestamp metadata
4. WHEN chunking documents, THE ChunkingService SHALL preserve page_number metadata

### Requirement 4: 统一的检索体验

**User Story:** As a user, I want to ask questions and get answers from all my resources (PDFs, videos, articles), so that I don't need to manually select which resources to search.

#### Acceptance Criteria

1. WHEN a user sends a chat message, THE System SHALL search across all resource types in the project
2. THE search results SHALL include resource_type and title for source attribution
3. THE System SHALL support optional filtering by resource_type if user wants to narrow scope

### Requirement 5: 向量存储统一

**User Story:** As a developer, I want all embeddings stored in a single collection/table, so that retrieval is simple and efficient.

#### Acceptance Criteria

1. WHEN VECTOR_STORE_PROVIDER=qdrant, THE System SHALL store all chunks in a single Qdrant collection
2. THE Qdrant payload SHALL include: resource_id, resource_type, project_id, title, platform, content
3. THE System SHALL create payload indexes for: project_id, resource_type, resource_id
