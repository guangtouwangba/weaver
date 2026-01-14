# vector-store Spec Delta

## MODIFIED Requirements

### Requirement: Vector Store Abstract Interface

The `VectorStore` abstract base class SHALL define the contract for all vector store implementations, including mandatory `user_id` parameter for data isolation.

#### Scenario: Search method signature (MODIFIED)
- **WHEN** implementing a vector store
- **THEN** the `search()` method SHALL accept:
  - `query_embedding: List[float]`
  - `project_id: UUID`
  - `limit: int = 5`
  - `document_id: UUID | None = None`
  - `user_id: str | None = None`
- **AND** return `List[SearchResult]`

#### Scenario: Hybrid search method (MODIFIED)
- **WHEN** implementing a vector store that supports hybrid search
- **THEN** the `hybrid_search()` method SHALL accept:
  - `query_embedding: List[float]`
  - `query_text: str`
  - `project_id: UUID`
  - `limit: int = 5`
  - `vector_weight: float = 0.7`
  - `keyword_weight: float = 0.3`
  - `document_id: UUID | None = None`
  - `user_id: str | None = None`
- **AND** return `List[SearchResult]`

## ADDED Requirements

### Requirement: User Isolation in Vector Search

The system SHALL filter vector search results by `user_id` when provided.

#### Scenario: Search with user_id filter
- **WHEN** `search()` is called with `user_id="user-123"`
- **THEN** the query SHALL include a filter `user_id = 'user-123'`
- **AND** only return chunks belonging to that user

#### Scenario: Search without user_id (legacy)
- **WHEN** `search()` is called with `user_id=None`
- **THEN** the query SHALL NOT filter by user_id
- **AND** return all matching chunks (backward compatible behavior)
- **AND** the system SHOULD log a warning in multi-tenant deployments
