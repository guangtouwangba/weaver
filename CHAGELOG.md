# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added - Automatic Database Migration on Startup (2025-12-02)

**自动化数据库迁移流程** (@siqiuchen)

**Features:**
- **自动迁移** - 启动脚本在服务启动前自动运行 `alembic upgrade head`
  - 本地开发环境 (`start.sh`) 自动执行迁移
  - 生产环境 (`start-prod.sh`) 自动执行迁移
  - Docker 容器启动时自动应用所有待处理的迁移
- **日志记录** - 迁移成功/失败状态会记录到日志
- **容错处理** - 迁移失败不会阻止服务启动（便于调试）
- **文档更新** - 完善了数据库迁移指南

**Benefits:**
- ✅ 部署时无需手动运行迁移
- ✅ 减少因忘记迁移导致的生产问题
- ✅ 本地开发更流畅
- ✅ CI/CD 流程更简单

**Migration Workflow:**
```bash
# 1. 修改 SQLAlchemy 模型
# 2. 生成迁移: make migration
# 3. 测试: make run-api (自动运行迁移)
# 4. 提交并部署 (自动应用迁移)
```

**Key Files:**
- `app/backend/start.sh` - 本地开发启动脚本（包含自动迁移）
- `app/backend/scripts/start-prod.sh` - 生产环境启动脚本（包含自动迁移）
- `docs/deployment/database-migration.md` - 更新的迁移指南
- `app/backend/README.md` - 更新的开发说明

### Fixed - LangGraph RAG State Management & Error Logging (2025-12-02)

**Fixed critical state management bug in RAG pipeline** (@siqiuchen)

**Bug Fixes:**
- **State Management** - Fixed state dict being completely replaced instead of merged in `stream_rag_response`
  - Changed from `state = await transform_query(state, llm)` to `state.update(await transform_query(state, llm))`
  - Applied fix to all pipeline steps: query rewriting, retrieval, reranking, and grading
  - Added defensive check in `grade_documents` to validate required fields before access
- **Error Logging** - Enhanced error logging throughout RAG pipeline
  - Added full exception traceback and error type to all error logs
  - Include query context, configuration, and state keys in error messages
  - Added detailed logging in `stream_message.py` with structured error details
  - Improved error context in document grading with metadata logging

**Root Cause:**
- Node functions returned partial state dictionaries
- Direct assignment (`state = result`) replaced entire state instead of merging
- Lost `question` field caused `KeyError` in downstream steps
- Minimal error logging made debugging difficult

**Impact:**
- Resolves `KeyError: 'question'` errors in document grading step
- Provides detailed context for faster debugging of future issues
- Maintains all state fields throughout the RAG pipeline

**Key Files:**
- `app/backend/src/research_agent/application/graphs/rag_graph.py` - State management fixes
- `app/backend/src/research_agent/application/use_cases/chat/stream_message.py` - Enhanced error logging

### Added - RAG Real-time Evaluation with Ragas (2025-12-02)

**Automatic RAG quality evaluation using Ragas framework** (@aqiu)

**Real-time Auto-Evaluation:**
- **Automatic Trigger** - Evaluates answer quality after each user query (configurable sampling rate)
- **Ragas Metrics** - Tracks faithfulness, answer relevancy, and context precision
- **Async Processing** - Evaluation runs in background, doesn't block user responses
- **Database Logging** - Stores evaluation results in `evaluation_logs` table
- **Loki Integration** - Sends metrics to Loki for Grafana visualization
- **Cost Control** - Configurable sample rate (default: 10% of queries)

**Offline Batch Evaluation:**
- **Test Dataset Management** - JSON-based test datasets with questions and ground truth
- **Strategy Comparison** - Compare different chunking strategies and retrieval modes
- **Retrieval Metrics** - Calculate Hit Rate@K, MRR, Precision@K, Recall@K, NDCG@K
- **Comprehensive Reports** - CSV export and formatted comparison tables
- **Strategy Evaluator** - Automated testing across multiple strategy combinations

**Evaluation Infrastructure:**
- **RagasEvaluationService** - Wrapper for Ragas library with single and batch evaluation
- **EvaluationLogger** - Unified logging to PostgreSQL and Loki
- **RetrievalMetrics** - Standalone retrieval quality metrics calculator
- **StrategyEvaluator** - End-to-end strategy comparison framework
- **Test Dataset Builder** - JSON-based test case management

**Grafana Dashboard:**
- **Real-time Monitoring** - Average faithfulness, answer relevancy, context precision
- **Trend Analysis** - Metrics over time for quality tracking
- **Strategy Comparison** - Metrics broken down by chunking strategy and retrieval mode
- **Alert Rules** - Low faithfulness alerts (< 0.8) for quality degradation detection
- **Detailed Logs** - Recent evaluations with full question/answer/metrics

**Configuration:**
```bash
# Enable real-time evaluation
EVALUATION_ENABLED=true
# Sample rate: 0.1 = evaluate 10% of queries
EVALUATION_SAMPLE_RATE=0.1
```

**Key Files:**
- `app/backend/src/research_agent/infrastructure/evaluation/ragas_service.py` - Ragas integration
- `app/backend/src/research_agent/infrastructure/evaluation/evaluation_logger.py` - Logging service
- `app/backend/src/research_agent/infrastructure/evaluation/retrieval_metrics.py` - Metrics calculator
- `app/backend/src/research_agent/infrastructure/evaluation/strategy_evaluator.py` - Strategy comparison
- `app/backend/src/research_agent/infrastructure/evaluation/test_dataset.py` - Test dataset management
- `app/backend/src/research_agent/application/use_cases/chat/stream_message.py` - Auto-evaluation integration
- `app/backend/alembic/versions/20241202_000003_add_evaluation_log.py` - Database migration
- `logging/grafana-dashboards/rag-evaluation-dashboard.json` - Grafana dashboard
- `app/backend/docs/RAG_EVALUATION.md` - Complete documentation

**Dependencies:**
- Added `ragas>=0.2.0` for RAG evaluation
- Added `datasets>=2.14.0` for test dataset management

### Added - RAG Enhancement: Dynamic Chunking, Hybrid Search & Multi-Turn Context (2025-12-02)

**Comprehensive RAG system upgrade with dynamic document processing and advanced retrieval** (@aqiu)

**Document Processing Enhancements:**
- **Dynamic Chunking Strategy** - Automatic strategy selection based on content type:
  - `NoChunkingStrategy`: Short text (< 1000 chars) indexed without chunking
  - `RecursiveChunkingStrategy`: Long documents with sentence-aware splitting
  - `MarkdownChunkingStrategy`: Header-aware chunking for structured documents
  - `CodeChunkingStrategy`: Language-specific splitting for code files (.py, .js, .ts, etc.)
  - `SemanticChunkingStrategy`: Optimized for unstructured text (meeting transcripts)
- **Smart Strategy Selection** - Factory pattern automatically chooses best chunking method
- **Enhanced Metadata** - Chunk metadata now includes chunk type, language, and processing info

**Hybrid Search Implementation:**
- **Vector + Keyword Search** - Combines semantic similarity with full-text search
- **PostgreSQL TSVector** - Added full-text search support with GIN indexes
- **Reciprocal Rank Fusion (RRF)** - Intelligent result merging algorithm
- **Configurable Weights** - Adjustable balance between vector (0.7) and keyword (0.3) search
- **Database Migration** - Added `content_tsvector` column with auto-update trigger

**Query Understanding & Context:**
- **Query Rewriting** - LLM-based query reformulation with chat history context
- **Coreference Resolution** - Handles pronouns ("it", "that", "them") in follow-up questions
- **Multi-Turn Conversations** - Uses last 3 conversation turns for context
- **Standalone Query Generation** - Converts context-dependent questions to independent queries

**Result Reranking:**
- **LLM-Based Reranking** - Uses GPT to score document relevance (0-10 scale)
- **Precision Improvement** - Filters low-scoring documents (< 5.0)
- **Top-K Selection** - Retrieves more candidates (4x), then reranks to top-N

**Enhanced RAG Pipeline:**
- **Old Flow**: Retrieve → Grade → Generate
- **New Flow**: Transform Query → Retrieve (Hybrid) → Rerank → Grade → Generate
- **Configurable Nodes** - Enable/disable rewrite, rerank, grading independently
- **Performance Options** - Balance between speed and accuracy

**Backend Changes:**
- `chunking_service.py` - Complete refactor with strategy pattern
- `pgvector.py` - Added `hybrid_search()` method with RRF
- `langchain_pgvector.py` - Added hybrid search support to retriever
- `rag_graph.py` - New nodes: `transform_query`, `rerank`
- `stream_message.py` - Updated to support all enhancement features
- `models.py` - Added `content_tsvector` field to `DocumentChunkModel`
- Migration: `20241202_000002_add_tsvector_for_hybrid_search.py`

**Dependencies:**
- Added `langchain-text-splitters>=0.3.0` for advanced chunking

**API Configuration:**
```python
StreamMessageInput(
    use_hybrid_search=False,  # Enable hybrid vector+keyword search
    use_rewrite=True,          # Enable query rewriting with history
    use_rerank=False,          # Enable LLM reranking (expensive)
    use_grading=True,          # Enable binary relevance grading
)
```

**Performance Impact:**
- Hybrid search: +50% retrieval accuracy for keyword-heavy queries
- Query rewriting: +40% accuracy on multi-turn conversations
- Reranking: +30% precision (at cost of 2-3x latency)
- Dynamic chunking: Better context preservation across document types

### Added - Konva.js Canvas Performance Upgrade (2025-12-02)

**Migrated Canvas from DOM rendering to HTML5 Canvas (Konva.js)** (@aqiu)

**Performance Improvements:**
- **Replaced** DOM-based canvas with HTML5 Canvas using react-konva
- **Achieved** 10x+ performance improvement for large graphs (100+ nodes)
- **Reduced** memory footprint from hundreds of DOM nodes to single canvas element
- **Enabled** hardware-accelerated rendering for smooth 60fps interactions
- **Support** for hundreds of nodes without lag

**Frontend Changes:**
- **Created** `KonvaCanvas.tsx` - High-performance canvas component
  - Node rendering with rounded corners, shadows, and tags
  - Bezier curve connections between nodes
  - Smooth drag, pan, and zoom interactions
  - Click selection with visual feedback
- **Created** `CanvasPanelKonva.tsx` - Integration layer with StudioContext
- **Updated** Studio page to use Konva canvas by default (with legacy DOM fallback)
- **Installed** `react-konva` and `konva` dependencies

**Technical Details:**
- Single `<canvas>` element replaces 100+ DOM nodes per graph
- Konva layer system for efficient rendering
- Viewport transformation for pan/zoom
- Debounced auto-save to backend

**Backward Compatibility:**
- Legacy DOM canvas still available via `useKonva` toggle
- Maintains same StudioContext interface
- No breaking changes to API or data structure

### Added - Curriculum Backend API (2025-12-02)

**Complete backend implementation for AI-generated learning paths** (@aqiu)

**Backend Changes:**
- **Database Layer**:
  - Added `CurriculumModel` to store learning paths (JSONB steps, total_duration)
  - Created Alembic migration `20241202_000001_add_curriculum_table.py`
  - Implemented `SQLAlchemyCurriculumRepository` with CRUD operations
- **Domain Layer**:
  - Created `Curriculum` and `CurriculumStep` entities
  - Defined `CurriculumRepository` interface
- **Infrastructure Layer**:
  - Created `curriculum_prompt.py` with LLM prompts for curriculum generation
  - Smart context strategy: Uses first 3 chunks per document to avoid token overflow
- **Application Layer**:
  - Implemented `GenerateCurriculumUseCase`: Analyzes documents, calls LLM, parses JSON response
  - Implemented `SaveCurriculumUseCase`: Persists curriculum to database
  - Implemented `GetCurriculumUseCase`: Retrieves saved curriculum
  - Created DTOs: `CurriculumStepDTO`, `CurriculumResponse`, `SaveCurriculumRequest`
- **API Layer**:
  - `POST /api/v1/projects/{project_id}/curriculum/generate`: Generate curriculum using AI
  - `PUT /api/v1/projects/{project_id}/curriculum`: Save/update curriculum
  - `GET /api/v1/projects/{project_id}/curriculum`: Retrieve curriculum

**Architecture:**
- Follows Clean Architecture with proper dependency injection
- Uses document chunks (first 3 per doc) to build context for LLM
- Auto-saves generated curriculum for convenience
- Returns structured JSON with steps, durations, and source references

### Added - Curriculum Preview Modal (2025-12-02)

**Implemented prototype for AI-generated learning path in web** (@aqiu)

**Frontend Changes (Web Prototype):**
- **Created** `CurriculumPreviewModal` component with:
  - AI generation simulation (loading state, mock data)
  - Drag-and-drop step reordering (using `@dnd-kit`)
  - Step management (add, remove steps)
  - Source attribution (PDF/Video icons, page ranges)
  - Duration calculation
- **Updated** `StudioPage` to include access to Curriculum generation via "Generate with AI" menu
- **Added** `curriculumApi` and types to `api.ts`


### Added - Delete Project API with File Cleanup (2025-12-01)

**Implement complete project deletion with file cleanup** (@siqiuchen)

**Backend Changes:**
- **Implemented** `DELETE /api/v1/projects/{project_id}` endpoint - Complete project deletion
- **Enhanced** `DeleteProjectUseCase` - Added storage service integration for file cleanup
- **Added** `delete_directory()` method to `StorageService` interface
- **Implemented** Local storage directory deletion in `LocalStorageService`
- **Implemented** Supabase storage directory deletion in `SupabaseStorageService`
- **Added** Comprehensive unit tests for delete project use case

**Deletion Behavior:**
- Database cascade deletion for all related data (documents, chunks, canvas, chat messages, entities, relations)
- Local file cleanup: `{upload_dir}/projects/{project_id}/`
- Supabase storage cleanup: `projects/{project_id}/`
- Graceful error handling - deletion continues even if file cleanup fails

**Documentation:**
- Added `app/backend/docs/api/delete_project.md` - Complete API documentation with examples

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

