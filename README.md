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

1. Install [uv](https://github.com/astral-sh/uv) if not already available.
2. Create a virtual environment and install dependencies:
   ```bash
   make install-dev
   ```
3. Launch the FastAPI service locally:
   ```bash
   make run
   ```
4. Available endpoints (subject to change as the refactor progresses):
   - `POST /documents/` – enqueue document ingest
   - `POST /search/` – semantic retrieval API
   - `POST /qa/` – question answering pipeline

## Next Steps

- Flesh out the `rag_core` subpackages (preprocessing, routing, memory, evaluation) following the architecture blueprint in `docs/architecture/generic_rag_architecture.md`.
- Define domain schemas in `packages/domain-models` and publish OpenAPI/JSON Schema for front-end SDK generation.
- Scaffold `apps/web` with build tooling and shared config, and add background workers under `apps/worker` for ingest queues and scheduled evaluations.

This structure keeps knowledge assets centralized while enabling independent evolution of backend, front-end, and automation surfaces.
