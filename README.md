# Knowledge Platform Monorepo

This repository hosts a modular Retrieval-Augmented Generation (RAG) platform aimed at building a personal knowledge-learning management system. The structure supports a FastAPI backend today and leaves first-class room for future worker processes and a dedicated web client.

## Repository Layout

```
apps/
  api/          # FastAPI app entrypoint and transport concerns
  web/          # Placeholder for React/Vite (or other) front-end
  worker/       # Placeholder for async tasks, pipelines, schedulers
packages/
  rag-core/     # Core RAG domain logic (chains, graphs, pipelines, processors)
  domain-models/# Shared domain entities for API ↔ web ↔ workers
  shared-config/# Centralized settings, logging, feature flags
  ui-kit/       # Placeholder for future shared UI components/assets
infra/
  docker/       # Container, compose and local orchestration assets
  terraform/    # IaC placeholders for future environments
docs/
  architecture/ # Architecture notes, specifications, diagrams
  functional_spec.md
Makefile        # Common developer tasks (install, lint, test)
pyproject.toml  # Root Python project definition (API depends on core packages)
uv.lock         # Resolved dependency lock produced by uv
```

`packages/rag-core` contains the existing LangChain/LangGraph implementation that powers document ingest, retrieval, and QA. The API service in `apps/api` consumes those modules today; additional packages capture shared concerns to keep front-end and worker code aligned as the platform grows.

## Getting Started (Backend)

1. **Install [uv](https://github.com/astral-sh/uv)** if not already available.

2. **Create a virtual environment and install dependencies**:
   ```bash
   make install-dev
   ```

3. **Configure environment variables**:
   ```bash
   # Copy the example configuration
   cp env.example .env
   
   # Edit .env and configure your embedding provider
   # For development, use the default fake provider
   # For production, configure OpenAI or OpenRouter
   ```
   
   See [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) for detailed configuration options.

4. **Launch the FastAPI service locally**:
   ```bash
   make run
   ```

5. **Available endpoints** (subject to change as the refactor progresses):
   - `POST /documents/` – enqueue document ingest (multipart/form-data with file upload)
   - `POST /search/` – semantic retrieval API
   - `POST /qa/` – question answering pipeline

### Embedding Providers

This platform supports multiple embedding providers:

- **`fake`** (default): Random embeddings for development/testing (no API key needed)
- **`openai`**: OpenAI embeddings (requires `OPENAI_API_KEY`)
- **`openrouter`**: Access multiple models via OpenRouter (Google Gemini, Cohere, etc.)

Configure your provider in `.env`:

```bash
# Development (default)
EMBEDDING_PROVIDER=fake

# Production with OpenAI
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Production with OpenRouter (recommended for multi-model support)
EMBEDDING_PROVIDER=openrouter
EMBEDDING_MODEL=google/gemini-embedding-001
OPENROUTER_API_KEY=sk-or-v1-...
```

For complete configuration options, see [OPENROUTER_SETUP.md](./OPENROUTER_SETUP.md).

### Retrieval Strategies

The platform supports multiple retrieval strategies with optional reranking:

#### 1. Retrieval Methods

- **`vector`**: Pure semantic search using embeddings (default, faster)
- **`hybrid`**: Combines BM25 keyword search with vector similarity for better accuracy
  - Recommended for production use
  - Especially effective for technical terms, proper nouns, and exact matches
  - Requires: `pip install rank-bm25`

#### 2. Reranking (Optional)

After initial retrieval, use a **Cross-Encoder** to rerank results for higher accuracy:
- Improves top result accuracy by 40%+
- Recommended: Retrieve top-20, rerank to top-5
- Requires: `pip install sentence-transformers`

Configure in `.env`:

```bash
# Basic: Vector retrieval only
RETRIEVER_TYPE=vector
VECTOR_TOP_K=4

# Better: Hybrid retrieval
RETRIEVER_TYPE=hybrid
RETRIEVER_VECTOR_WEIGHT=0.7
RETRIEVER_BM25_WEIGHT=0.3
VECTOR_TOP_K=5

# Best: Hybrid retrieval + Reranking (recommended for production)
RETRIEVER_TYPE=hybrid
VECTOR_TOP_K=20                                      # Retrieve more candidates
RERANKER_ENABLED=true
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANKER_TOP_N=5                                     # Rerank to top-5
```

For detailed information:
- Hybrid Retrieval: [docs/HYBRID_RETRIEVER.md](./docs/HYBRID_RETRIEVER.md)
- Reranking: [docs/RERANKER.md](./docs/RERANKER.md)

## Next Steps

- Flesh out the `rag_core` subpackages (preprocessing, routing, memory, evaluation) following the architecture blueprint in `docs/architecture/generic_rag_architecture.md`.
- Define domain schemas in `packages/domain-models` and publish OpenAPI/JSON Schema for front-end SDK generation.
- Scaffold `apps/web` with build tooling and shared config, and add background workers under `apps/worker` for ingest queues and scheduled evaluations.

This structure keeps knowledge assets centralized while enabling independent evolution of backend, front-end, and automation surfaces.
