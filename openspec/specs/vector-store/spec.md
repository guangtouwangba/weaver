# vector-store Specification

## Purpose
TBD - created by archiving change integrate-qdrant-vector-store. Update Purpose after archive.
## Requirements
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

### Requirement: Vector Store Provider Factory
The system SHALL provide a factory function to create vector store instances based on configuration.

#### Scenario: Default provider selection
- **WHEN** `get_vector_store()` is called without explicit provider
- **THEN** the factory SHALL return an instance based on `VECTOR_STORE_PROVIDER` environment variable
- **AND** default to `pgvector` if not configured

#### Scenario: Explicit provider selection
- **WHEN** `get_vector_store(provider="qdrant")` is called
- **THEN** the factory SHALL return a `QdrantVectorStore` instance
- **AND** ignore the environment variable setting

---

### Requirement: Qdrant Vector Store Implementation
The system SHALL provide a Qdrant-based vector store implementation that conforms to the `VectorStore` interface.

#### Scenario: Vector similarity search
- **WHEN** `QdrantVectorStore.search()` is called with a query embedding and project_id
- **THEN** the system SHALL return up to `limit` most similar chunks from Qdrant
- **AND** each result SHALL include chunk_id, document_id, content, page_number, and similarity score
- **AND** results SHALL be filtered by project_id

#### Scenario: Document-scoped search
- **WHEN** `search()` is called with `document_id` parameter
- **THEN** results SHALL be filtered to only include chunks from that document

#### Scenario: Hybrid search support
- **WHEN** `QdrantVectorStore.hybrid_search()` is called
- **THEN** the system SHALL combine vector similarity with keyword matching
- **AND** return results ranked by fused score

---

### Requirement: Qdrant Collection Management
The system SHALL automatically manage Qdrant collection lifecycle.

#### Scenario: Collection initialization on startup
- **WHEN** the application starts with `VECTOR_STORE_PROVIDER=qdrant`
- **THEN** the system SHALL check if the target collection exists
- **AND** create the collection with appropriate vector config if not exists

#### Scenario: Collection schema configuration
- **WHEN** a collection is created
- **THEN** it SHALL be configured with:
  - Vector size matching embedding model dimension (default: 1536)
  - Cosine distance metric
  - Payload indexes for project_id and document_id

---

### Requirement: Qdrant Docker Service
The system SHALL provide a Docker Compose configuration for local Qdrant deployment.

#### Scenario: Local development setup
- **WHEN** `docker-compose up` is run
- **THEN** a Qdrant service SHALL be available at `http://localhost:6333`
- **AND** data SHALL be persisted in a Docker volume

#### Scenario: Health checking
- **WHEN** the Qdrant container starts
- **THEN** Docker Compose SHALL wait for the service to be healthy
- **AND** report unhealthy status if Qdrant fails to respond

---

### Requirement: Qdrant Configuration
The system SHALL provide environment-based configuration for Qdrant connection.

#### Scenario: Configuration via environment variables
- **WHEN** the application loads configuration
- **THEN** it SHALL read Qdrant settings from:
  - `QDRANT_URL` (default: `http://localhost:6333`)
  - `QDRANT_API_KEY` (optional, for authenticated deployments)
  - `QDRANT_COLLECTION_NAME` (default: `document_chunks`)

#### Scenario: Connection with API key
- **WHEN** `QDRANT_API_KEY` is set
- **THEN** all Qdrant requests SHALL include the API key for authentication

---

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

