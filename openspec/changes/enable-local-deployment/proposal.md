# Change: Enable Full Local Deployment

## Why
The project currently requires external API services (OpenRouter/OpenAI) for LLM and embedding functionality, creating barriers for privacy-conscious users, offline development, and cost-sensitive deployments. Enabling full local deployment will expand the project's adoption by supporting users who prefer or require self-hosted AI infrastructure.

## What Changes

### 1. LLM Provider Abstraction Layer
- **BREAKING**: Refactor `ChatOpenAI` hardcoding in RAG graph to use a configurable provider factory
- Add support for local LLM servers (Ollama, vLLM, LocalAI) via OpenAI-compatible API endpoints
- Update `model_config.py` to include local model context window configurations
- Add environment variables for local LLM configuration (base URL, model name)

### 2. Embedding Service Abstraction
- **BREAKING**: Make embedding dimension configurable (currently hardcoded to 1536)
- Add database migration strategy for embedding dimension changes
- Support local embedding models (Ollama embeddings, sentence-transformers via HuggingFace)
- Add dimension auto-detection from model metadata

### 3. Docker Compose Middleware Stack
- Add optional local LLM service (Ollama) to docker-compose.yml
- Ensure PostgreSQL with pgvector works standalone without external dependencies
- Add health checks for local AI services

### 4. Context Window Safety for Local Models
- Add local model context window configurations
- Implement token estimation adjustment for smaller context windows
- Add warning/error handling when context exceeds model capacity

## Impact

### Affected Specs
- `specs/infrastructure` (new capability)
- `specs/llm` (new capability)

### Affected Code

**LLM Layer:**
- `infrastructure/llm/base.py` - Add LLM factory interface
- `infrastructure/llm/openrouter.py` - Refactor to use base class
- `infrastructure/llm/local.py` (new) - Local LLM service implementation
- `infrastructure/llm/langchain_openrouter.py` - Abstract to support local endpoints
- `infrastructure/llm/model_config.py` - Add local model configurations

**Embedding Layer:**
- `infrastructure/embedding/base.py` - Add dimension property
- `infrastructure/embedding/local.py` (new) - Local embedding service
- `infrastructure/database/models.py` - Make vector dimension configurable
- `alembic/versions/` - Migration for dimension flexibility

**Configuration:**
- `config.py` - Add local deployment settings
- `api/deps.py` - Provider factory based on configuration
- `docker-compose.yml` - Add Ollama service

**RAG Graph:**
- `application/graphs/rag_graph.py` - Use LLM factory instead of ChatOpenAI directly
- `infrastructure/strategies/generation/*.py` - Abstract LLM instantiation

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Embedding dimension mismatch breaks existing data | Require manual migration with clear documentation; add dimension validation on startup |
| Local models have smaller context windows | Add context budget calculation with model-specific limits; graceful degradation |
| LangChain version compatibility | Pin langchain-community version; test with Ollama integration |
| Performance regression with local models | Add latency logging; document hardware requirements |

## Non-Goals
- Automatic model downloading/management (users configure Ollama separately)
- Fine-tuning support
- Model quantization tooling
- GPU resource management
