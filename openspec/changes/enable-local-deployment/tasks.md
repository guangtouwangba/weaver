# Tasks: Enable Local Deployment

## 1. LLM Provider Abstraction

### 1.1 Configuration Layer
- [ ] 1.1.1 Add `LLM_PROVIDER_TYPE` enum to config (openrouter|openai|local)
- [ ] 1.1.2 Add `LOCAL_LLM_BASE_URL` config (default: http://localhost:11434/v1)
- [ ] 1.1.3 Add `LOCAL_LLM_MODEL` config (default: llama3.2:3b)
- [ ] 1.1.4 Add `LOCAL_LLM_API_KEY` config (default: ollama)

### 1.2 Provider Factory
- [ ] 1.2.1 Create `infrastructure/llm/factory.py` with `create_chat_model()` function
- [ ] 1.2.2 Update `api/deps.py` to use LLM factory instead of direct OpenRouterLLMService
- [ ] 1.2.3 Create `infrastructure/llm/local.py` for local LLM service implementation
- [ ] 1.2.4 Refactor `langchain_openrouter.py` to accept configurable base URL

### 1.3 RAG Graph Updates
- [ ] 1.3.1 Update `application/graphs/rag_graph.py` to accept abstract LLM type
- [ ] 1.3.2 Update `infrastructure/strategies/generation/basic.py` to use factory
- [ ] 1.3.3 Update `infrastructure/strategies/generation/long_context.py` to use factory

### 1.4 Model Configuration
- [ ] 1.4.1 Add local model context windows to `model_config.py`
- [ ] 1.4.2 Add context window lookup for unknown local models (conservative default)

## 2. Embedding Service Abstraction

### 2.1 Configuration Layer
- [ ] 2.1.1 Add `EMBEDDING_PROVIDER_TYPE` config (openrouter|openai|local)
- [ ] 2.1.2 Add `EMBEDDING_DIMENSION` config (default: 1536)
- [ ] 2.1.3 Add `LOCAL_EMBEDDING_BASE_URL` config
- [ ] 2.1.4 Add `LOCAL_EMBEDDING_MODEL` config (default: nomic-embed-text)

### 2.2 Embedding Factory
- [ ] 2.2.1 Create `infrastructure/embedding/factory.py` with `create_embedding_service()`
- [ ] 2.2.2 Create `infrastructure/embedding/local.py` for Ollama embeddings
- [ ] 2.2.3 Update `api/deps.py` to use embedding factory
- [ ] 2.2.4 Add `dimension` property to base embedding service interface

### 2.3 Database Dimension Handling
- [ ] 2.3.1 Refactor `infrastructure/database/models.py` to read dimension from config
- [ ] 2.3.2 Add startup validation: compare config dimension vs database schema
- [ ] 2.3.3 Document migration process for dimension changes in README
- [ ] 2.3.4 Add clear error message if dimension mismatch detected

## 3. Docker Compose Integration

### 3.1 Ollama Service
- [ ] 3.1.1 Add Ollama service to `docker-compose.yml` with `local` profile
- [ ] 3.1.2 Add volume mount for Ollama model storage
- [ ] 3.1.3 Add GPU passthrough configuration (optional)
- [ ] 3.1.4 Add health check for Ollama service

### 3.2 Documentation
- [ ] 3.2.1 Update backend env.example with local deployment variables
- [ ] 3.2.2 Add LOCAL_DEPLOYMENT.md guide with:
  - Ollama installation instructions
  - Recommended models for RAG
  - Docker profile usage
  - Embedding dimension migration steps

## 4. Testing & Validation

### 4.1 Unit Tests
- [ ] 4.1.1 Add tests for LLM factory with mocked local endpoint
- [ ] 4.1.2 Add tests for embedding factory with mocked local endpoint
- [ ] 4.1.3 Add tests for dimension validation logic

### 4.2 Integration Tests
- [ ] 4.2.1 Add integration test for local LLM chat completion (requires Ollama)
- [ ] 4.2.2 Add integration test for local embedding generation (requires Ollama)
- [ ] 4.2.3 Add integration test for RAG pipeline with local providers

### 4.3 Manual Validation
- [ ] 4.3.1 Test full RAG query flow with Ollama locally
- [ ] 4.3.2 Test embedding generation with nomic-embed-text
- [ ] 4.3.3 Verify context window limits are respected
- [ ] 4.3.4 Test Docker Compose local profile startup

## Dependencies

```
1.1 Configuration → 1.2 Factory → 1.3 RAG Graph
                  ↘ 1.4 Model Config
2.1 Config → 2.2 Factory → 2.3 Database
3.1 Docker → 3.2 Documentation
4.x (parallel after all implementation complete)
```

## Estimated Effort

| Section | Estimated Time |
|---------|----------------|
| 1. LLM Abstraction | 4-6 hours |
| 2. Embedding Abstraction | 4-6 hours |
| 3. Docker Integration | 2-3 hours |
| 4. Testing | 3-4 hours |
| **Total** | **13-19 hours** |
