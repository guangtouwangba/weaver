# Research Agent RAG - Backend

AI-powered research assistant with knowledge cards.

## Tech Stack

- **Framework**: FastAPI + SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16 + pgvector
- **LLM**: OpenRouter (unified access to 400+ models)
- **PDF Processing**: PyMuPDF

## Quick Start

### 1. Start Database

```bash
docker-compose up -d
```

### 2. Install Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Or using uv (recommended)
uv pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Server

```bash
# Development mode with auto-reload
uvicorn research_agent.main:app --reload --port 8000

# Or using the module directly
python -m research_agent.main
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
src/research_agent/
├── api/              # HTTP endpoints (Presentation Layer)
├── application/      # Use cases and DTOs (Application Layer)
├── domain/           # Business logic (Domain Layer)
├── infrastructure/   # External services (Infrastructure Layer)
└── shared/           # Common utilities
```

## Development

### Run Tests

```bash
pytest
```

### Format Code

```bash
ruff format .
ruff check --fix .
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

