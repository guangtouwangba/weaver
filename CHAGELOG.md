# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed - Knowledge Graph Extraction Bugs (2025-11-28)

**Fix multiple import and configuration issues** (@siqiuchen)

**Backend Fixes:**
- **Fixed** Canvas sync not finding entities - added explicit commit before canvas sync to ensure entities are visible
- **Fixed** SQLAlchemy reserved `metadata` attribute name conflict in `EntityModel` and `RelationModel`
  - Renamed Python attributes to `entity_metadata`/`relation_metadata` while keeping DB column as `metadata`
- **Fixed** `settings` import error - use `get_settings()` function instead of direct import
- **Fixed** PDF parser import - corrected from `PyPDFParser` to `PyMuPDFParser`
- **Fixed** `EXTRACTION_PROMPT` format string - escaped JSON curly braces with `{{` and `}}`
- **Added** OpenRouter API key validation before graph extraction with clear warning log
- **Improved** Error logging with `exc_info=True` for better debugging

**Frontend Fixes:**
- **Fixed** `SourcePanel` document polling - correctly access `response.items` array from API response

### Added - Async Document Processing & Knowledge Graph (2025-11-28)

**Implement async task queue and knowledge graph extraction** (@aqiu)

**Architecture:**
- Database-backed task queue for reliable background processing
- Knowledge Graph storage using Postgres tables (`entities`, `relations`)
- Automatic Canvas sync with extracted graph data

**Backend Changes:**
- **Created** `worker/` module - Modular background task processing system
  - `TaskQueueService` - Push/pop tasks from database queue
  - `TaskDispatcher` - Route tasks to handlers
  - `BackgroundWorker` - Poll loop with graceful shutdown
- **Created** `DocumentProcessorTask` - Orchestrates full document pipeline
- **Created** `GraphExtractorTask` - LLM-based entity/relation extraction via OpenRouter
- **Created** `CanvasSyncerTask` - Auto-layout and sync graph to canvas
- **Added** Alembic migration for `task_queue`, `entities`, `relations` tables
- **Added** SQLAlchemy models: `TaskQueueModel`, `EntityModel`, `RelationModel`
- **Added** Domain entities: `Task`, `Entity`, `Relation`, `KnowledgeGraph`
- **Refactored** `POST /documents/confirm` - Now returns `202 Accepted` and schedules async processing

**Processing Pipeline:**
```
Upload → Confirm → Task Queue → Worker picks up
  → Text Extraction → Chunking → Embedding
  → Graph Extraction (LLM) → Canvas Sync
  → Status: ready
```

**Frontend Changes:**
- **Added** Document status polling (3s interval for pending/processing docs)
- **Added** Status badges: Queued (yellow), Processing (blue), Ready (green), Error (red)
- **Added** Processing indicator (progress bar) on file cards
- **Updated** File cards to be non-clickable while processing

### Added - Supabase Storage Integration (2025-11-28)

**Migrate file uploads from local storage to Supabase Storage** (@aqiu)

**Backend Changes:**
- **Created** `supabase_storage.py` - Supabase Storage service with presigned URL support
- **Added** `POST /documents/presign` endpoint - Generate presigned upload URLs
- **Added** `POST /documents/confirm` endpoint - Confirm upload and process document
- **Updated** `GET /documents/{id}/file` endpoint - Support redirect to signed download URLs
- **Added** Supabase config options: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `STORAGE_BUCKET`

**Frontend Changes:**
- **Added** `uploadWithPresignedUrl()` method - Direct upload to Supabase Storage
- **Added** upload progress indicator with percentage display
- **Added** processing state indicator after upload completes
- **Implemented** fallback to direct backend upload if presigned URL not available

**Supabase Storage Configuration:**
- Created `documents` bucket (private, 50MB limit)
- Configured RLS policies for service role and authenticated users
- Supported MIME types: PDF, text, markdown, DOCX

**Architecture:**
```
Frontend → Backend (presign) → Supabase Storage
Frontend → Supabase Storage (direct upload)
Frontend → Backend (confirm) → Process & Store metadata
```

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

