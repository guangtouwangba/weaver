# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed - Rebrand to Weaver (2025-11-27)

**Project renamed to "Weaver"** (@aqiu)

- **Renamed** project title to "Weaver"
- **Slogan**: "Weave knowledge into insights"
- **Added** new logo (`weaver-logo.svg`) with Indigo-Teal gradient nodes
- **Updated** frontend metadata and backend API info

### Fixed - TypeScript Build Error (2025-11-27)

**修复前端构建时的 TypeScript 命名冲突** (@aqiu)

- **Renamed** `Document` interface to `ProjectDocument` in `app/frontend/src/lib/api.ts`
  - `Document` is a reserved DOM type in TypeScript, causing build conflicts
- **Updated** `app/frontend/src/app/api-test/page.tsx` to use `ProjectDocument`

### Changed - Migrate from Fly.io to Zeabur (2025-11-27)

**Deployment platform migration to Zeabur**

- **Migrated** deployment from Fly.io to Zeabur for better Chinese support and simpler workflow
- **Created** `app/backend/Dockerfile` - Standalone Dockerfile for backend (adapted from root Dockerfile.api)
- **Removed** Fly.io configuration files:
  - `Dockerfile.api` (moved to app/backend/Dockerfile)
  - `fly.api.dev.toml`, `fly.api.prod.toml`
  - `app/frontend/fly.dev.toml`
  - `web/fly.prod.toml`
- **Removed** GitHub Actions workflows (Zeabur auto-deploy replaces them):
  - `.github/workflows/deploy-api.yml`
  - `.github/workflows/deploy-web.yml`
- **Removed** Fly.io scripts:
  - `scripts/deploy.sh`
  - `scripts/fly-setup.sh`

**Zeabur deployment structure (2 projects, multiple services):**

| 环境 | 项目 | 服务 |
|------|------|------|
| Dev | `research-rag-dev` | api, frontend |
| Prod | `research-rag-prod` | api, frontend, web |

**Documentation:**
- Added `docs/deployment/zeabur-deployment.md` - Complete deployment guide

### Changed - MVP Scope Cleanup (2025-11-26)

**Frontend cleanup to align with MVP scope (PDF-only, Canvas-focused)**

- **Removed** `PodcastView.tsx` - AI-generated podcast view (out of MVP scope)
- **Removed** `WriterView.tsx` - Concept mixer writing view (out of MVP scope)
- **Simplified** `app/frontend/src/app/studio/page.tsx` (1560 → 876 lines, -44%):
  - Removed multi-media player support (Video/Audio)
  - Removed multi-tab system (Podcast/Writer/Slides/Flashcards)
  - Removed Canvas Copilot AI panel (out of MVP scope)
  - Removed Quiet Mode toggle
  - Simplified resource list to PDF-only
  - Simplified AI Assistant panel to basic chat interface
  - Retained core Canvas functionality with nodes and connections
  - Retained PDF text drag-and-drop to Canvas feature

**Removed Pages (out of MVP scope)**
- Deleted `/brain` page - Global knowledge graph (not needed until 5+ projects)
- Deleted `/inbox` page - Pre-processing inbox (direct upload to project is simpler)
- Deleted `/projects` page - Standalone projects list (Dashboard already has this)
- Simplified `GlobalSidebar.tsx` - Only Dashboard & Studio navigation

**Documentation**
- Added `docs/product design/MVP_Scope.md` - MVP feature specification document
- Added `docs/product design/MVP_Backend_Architecture.md` - Backend architecture design

### Added - Backend MVP Implementation (2025-11-26)

**Complete backend implementation with Clean Architecture**

**Project Structure** (`app/backend/`)
- FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + pgvector
- Clean Architecture: API → Application → Domain → Infrastructure
- Docker Compose for local development (PostgreSQL + pgvector)

**API Endpoints**
- `GET/POST/DELETE /api/v1/projects` - Project CRUD
- `GET/POST/DELETE /api/v1/projects/{id}/documents` - Document management
- `POST /api/v1/projects/{id}/chat` - RAG chat (sync)
- `POST /api/v1/projects/{id}/chat/stream` - RAG chat (SSE streaming)
- `GET/PUT /api/v1/projects/{id}/canvas` - Canvas persistence
- `GET /health` - Health check

**Core Features**
- PDF upload with text extraction (PyMuPDF)
- Text chunking with overlap for RAG
- Vector embeddings via OpenRouter (text-embedding-3-small)
- Vector search via pgvector
- LLM chat via OpenRouter (gpt-4o-mini default)
- Canvas data persistence (JSONB)

**Infrastructure**
- OpenRouter integration for LLM/Embedding (400+ models)
- pgvector for vector similarity search
- Local file storage for PDF uploads
- Alembic database migrations

