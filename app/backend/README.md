# Weaver Backend API

AI-powered research assistant backend with RAG (Retrieval-Augmented Generation), infinite canvas, and knowledge card management.

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#-quick-start)
- [Prerequisites](#-prerequisites)
- [Configuration](#️-configuration)
- [Running the Server](#-running-the-server)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)

---

## Features

- 📄 **PDF Document Processing** — Upload and OCR support (Gemini, Docling, Unstructured)
- 🌐 **Web Page Extraction** — Fetch and parse content from URLs
- 🎬 **Video Transcription** — YouTube, Bilibili, Douyin support
- 💬 **RAG-based Q&A** — Ask questions with citation support
- 🧠 **Mindmap Generation** — Auto-generate structured mindmaps
- 📇 **Flashcard Generation** — Create study cards from documents
- 🎨 **Infinite Canvas** — Visual knowledge organization

---

## 🚀 Quick Start

### 1. Start Infrastructure Services

```bash
# From app/backend directory
docker compose up -d
```

This starts:
| Service | Port | Description |
|---------|------|-------------|
| **PostgreSQL** | 5432 | Database with pgvector extension |
| **Redis** | 6379 | Task queue for async processing |
| **Qdrant** | 6333/6334 | Vector database (optional) |

### 2. Configure Environment

```bash
# Copy example config
cp env.example .env

# Edit .env and add your API keys (at minimum):
# - OPENROUTER_API_KEY=sk-or-v1-your-key
```

### 3. Install Dependencies

```bash
# From project root
make install-backend

# Or directly with uv
cd app/backend && uv sync
```

### 4. Run the Server

```bash
# From project root (recommended)
make run-backend

# Or directly
cd app/backend && ./start.sh
```

> 💡 **Note:** Database migrations run automatically on startup.

---

## 📦 Prerequisites

### Required

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| Docker | Latest | Infrastructure services |
| uv | Latest | Package manager |

### System Dependencies

```bash
# macOS
brew install poppler ffmpeg

# Ubuntu/Debian
sudo apt install poppler-utils ffmpeg

# Or use make command from project root
make install-system-deps
```

| Tool | Purpose |
|------|---------|
| **poppler** | PDF to image conversion (for Gemini OCR) |
| **ffmpeg** | Audio/video processing (for transcription) |

---

## ⚙️ Configuration

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete configuration reference.

### Essential Environment Variables

```bash
# Database (required)
DATABASE_URL=postgresql+asyncpg://research_rag:research_rag_dev@localhost:5432/research_rag

# LLM API (required - choose one)
OPENROUTER_API_KEY=sk-or-v1-your-key    # Recommended
# OPENAI_API_KEY=sk-your-key            # Alternative

# Redis (required for async tasks)
REDIS_URL=redis://localhost:6379

# Auth (for production)
SUPABASE_JWT_SECRET=your-jwt-secret
AUTH_BYPASS_ENABLED=false   # Set true for local dev without auth

# CORS (adjust for your frontend URL)
CORS_ORIGINS=http://localhost:3000
```

### Configuration Categories

| Category | Key Variables |
|----------|---------------|
| **Database** | `DATABASE_URL`, `DATABASE_CLIENT_TYPE` |
| **Vector Store** | `VECTOR_STORE_PROVIDER`, `QDRANT_URL` |
| **LLM** | `OPENROUTER_API_KEY`, `LLM_MODEL`, `EMBEDDING_MODEL` |
| **Vision/OCR** | `GOOGLE_API_KEY`, `OCR_MODE` |
| **YouTube** | `YOUTUBE_COOKIES_PATH`, `YOUTUBE_PROXY_URL` |
| **Storage** | `UPLOAD_DIR`, `SUPABASE_URL`, `STORAGE_BUCKET` |
| **RAG** | `RAG_MODE`, `RETRIEVAL_TOP_K`, `RETRIEVAL_MIN_SIMILARITY` |
| **Observability** | `LOG_LEVEL`, `LOKI_URL`, `LANGFUSE_ENABLED` |
| **Security** | `CORS_ORIGINS`, `SUPABASE_JWT_SECRET`, `AUTH_BYPASS_ENABLED` |

---

## 🏃 Running the Server

### Development Mode

```bash
# From project root
make run-backend

# Or directly from app/backend
./start.sh
```

The server starts at `http://localhost:8000` with:
- Auto-reload on code changes
- Automatic database migrations
- Swagger UI at `/docs`

### Running the Task Worker

For async tasks (document processing, URL extraction):

```bash
# From app/backend directory
uv run python -m research_agent.worker.main
```

### Using Docker

```bash
# Build and run with docker-compose
docker compose -f docker-compose.yml up --build
```

---

## 📚 API Documentation

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc (alternative) |
| `http://localhost:8000/openapi.json` | OpenAPI schema |

### Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/projects` | Create project |
| `POST` | `/api/v1/resources/upload` | Upload document |
| `POST` | `/api/v1/chat/stream` | Chat with RAG |
| `GET` | `/api/v1/canvases/{id}` | Get canvas |
| `POST` | `/api/v1/generations/mindmap` | Generate mindmap |

---

## 🏗️ Architecture

```
src/research_agent/
├── api/                    # FastAPI routes
│   ├── routes/             # API endpoints by domain
│   └── middleware/         # Request/Response middleware
├── domain/                 # Business logic
│   ├── entities/           # Domain models
│   └── services/           # Domain services
├── infrastructure/         # External integrations
│   ├── database/           # SQLAlchemy models & repos
│   ├── llm/                # LLM providers (OpenRouter, etc.)
│   ├── vector_store/       # pgvector, Qdrant
│   └── extractors/         # PDF, YouTube, Web extractors
├── rag/                    # RAG implementation (LangGraph)
└── worker/                 # Async task processing (ARQ)
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| **FastAPI** | Web framework |
| **SQLAlchemy 2.0** | Async ORM |
| **LangChain / LangGraph** | RAG orchestration |
| **pgvector** | Vector similarity search |
| **ARQ** | Redis-based task queue |
| **Pydantic** | Settings & validation |

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
cd app/backend && uv run pytest --cov=research_agent
```

---

## 📖 Additional Documentation

- [Configuration Reference](docs/CONFIGURATION.md) — Complete environment variable reference
- [env.example](env.example) — Annotated example configuration
