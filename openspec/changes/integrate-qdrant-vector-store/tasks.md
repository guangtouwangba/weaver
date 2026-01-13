# Tasks: Integrate Qdrant Vector Store

## 1. Infrastructure Setup

- [ ] 1.1 Add `qdrant-client` to `pyproject.toml` dependencies
- [ ] 1.2 Add Qdrant service to `docker-compose.yml` with persistent volume and health check
- [ ] 1.3 Update `config.py` with Qdrant configuration settings:
  - `qdrant_url` (default: `http://localhost:6333`)
  - `qdrant_api_key` (optional)
  - `qdrant_collection_name` (default: `document_chunks`)

## 2. Core Implementation

- [ ] 2.1 Extend `VectorStore` base class in `base.py`:
  - Add `hybrid_search()` abstract method with default implementation
  - Add `document_id` parameter to `search()` method signature
- [ ] 2.2 Create `infrastructure/vector_store/qdrant.py`:
  - Implement `QdrantVectorStore` class
  - Implement `search()` method with project_id/document_id filtering
  - Implement `hybrid_search()` method (can defer to simple search initially)
  - Add collection initialization logic
- [ ] 2.3 Create `infrastructure/vector_store/factory.py`:
  - Implement `get_vector_store(session, provider=None)` function
  - Support `pgvector` and `qdrant` providers
  - Default to `config.vector_store_provider`

## 3. Application Startup Integration

- [ ] 3.1 Add Qdrant collection initialization to application startup:
  - Check if collection exists
  - Create collection with vector config if not exists
  - Configure payload indexes for project_id and document_id

## 4. Integration Points

- [ ] 4.1 Update `application/use_cases/chat/stream_message.py`:
  - Ensure `get_vector_store()` factory is used (already imports it)
- [ ] 4.2 Update `api/v1/chat.py`:
  - Replace direct `PgVectorStore(session)` with `get_vector_store(session)`
- [ ] 4.3 Update `infrastructure/evaluation/strategy_evaluator.py`:
  - Replace direct `PgVectorStore(session)` with factory pattern

## 5. Configuration & Documentation

- [ ] 5.1 Update `.env.example` with Qdrant environment variables
- [ ] 5.2 Update `README.md` with Qdrant setup instructions

## 6. Verification

- [ ] 6.1 Create verification script `scripts/verify_qdrant.py`:
  - Test collection creation
  - Test vector insert
  - Test vector search
  - Test payload filtering
- [ ] 6.2 Test RAG pipeline with Qdrant provider:
  - Start docker-compose with Qdrant
  - Set VECTOR_STORE_PROVIDER=qdrant
  - Verify application starts without errors
- [ ] 6.3 Test provider switching:
  - Start with pgvector (default)
  - Switch to qdrant via env var
  - Verify clean startup (empty search results expected)

## Dependencies

- Task 2.1 blocks 2.2
- Task 2.3 blocks 3.1, 4.1, 4.2, 4.3
- Task 1.1, 1.2, 1.3 can be done in parallel
- Task 3.1 requires 2.2 and 2.3
