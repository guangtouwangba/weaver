# Project Context

## Purpose
Visual Thinking Assistant (research-agent-rag).
A tool to help users analyze relationships, build knowledge systems, and visualize thinking paths through a spatial canvas interface, going beyond simple knowledge management or Q&A.

## Tech Stack
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, MUI v7, Konva/React-Konva (Canvas), Lucide React.
- **Backend:** Python 3.13+, FastAPI, SQLAlchemy (Async), AsyncPG, Alembic, LangChain/LangGraph, OpenAI SDK.
- **Database:** PostgreSQL with pgvector (Supabase or local).
- **Infrastructure:** Docker, Docker Compose, Modal (OCR service), Loki/Grafana (Logging).
- **AI/ML:** RAG pipeline, OpenAI models, Unstructured/PyMuPDF/Docling (Document Processing).

## Project Conventions

### Code Style
- **Python:** Strict typing (`mypy`), `ruff` for linting/formatting (target Python 3.13).
- **Frontend:** TypeScript strict mode, ESLint, Functional React components with Hooks.
- **Styling:** Tailwind CSS for layout/utility, MUI for core components.
- **Language:** English for all code, comments, and UI text.

### Architecture Patterns
- **Frontend:** Client-side canvas logic (Konva) + Server Components (Next.js) for data fetching.
- **Backend:** Modular monolith (`src/research_agent`). Async-first API design.
- **Data Flow:** Upload -> Process (Async) -> Vector Store -> Knowledge Graph/Canvas.

### Testing Strategy
- **Backend:** `pytest` with `pytest-asyncio`. Unit tests for logic, integration tests for API/DB.
- **Frontend:** Component testing (implied).

### Git Workflow
- Feature branches.
- Commit messages should be descriptive.
- Versioning managed via `pyproject.toml` and `package.json`.

## Domain Context
- **Visual Thinking Assistant:** The core product identity.
- **Canvas as Workbench:** Not a repository. Uploads don't automatically populate the canvas; users drag items to focus.
- **Thinking Path:** Visualization of the reasoning process is key, not just the final answer.
- **Drag to Focus:** Interaction model where users pull content into the workspace to analyze it.

## Important Constraints
- **Solo Developer:** Solutions must be maintainable and cost-effective.
- **Open Source + Commercial:** Dual strategy.
- **Performance:** Canvas must remain responsive with many nodes.

## External Dependencies
- **LLM Providers:** OpenAI (via OpenRouter or direct).
- **Supabase:** Database and Auth (optional/configurable).
- **Modal:** Optional remote execution for heavy OCR tasks.
