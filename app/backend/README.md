# Research Agent RAG - Backend API

AI-powered research assistant with knowledge cards.

## Features

- PDF document upload and processing
- RAG-based Q&A with citations
- Infinite canvas for knowledge organization
- Project management

## Tech Stack

- FastAPI + SQLAlchemy 2.0 (async)
- PostgreSQL + pgvector
- OpenRouter (LLM Gateway)

## Development

```bash
# Start database
docker compose up -d

# Start server (migrations run automatically)
./start.sh
```

**Note:** Database migrations run automatically on startup. No need to run `alembic upgrade head` manually!

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
