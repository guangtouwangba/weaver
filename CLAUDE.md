# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent research paper analysis system that supports multiple LLM providers (OpenAI, DeepSeek, Anthropic). The system uses specialized AI agents to analyze academic papers from ArXiv and provides a modern web interface for research and discussion.

## Core Architecture

### Backend Structure
- **FastAPI Server** (`backend/main.py`): Main API server with health checks and middleware
- **Multi-Agent System** (`backend/agents/`): Specialized AI agents for research analysis
  - `orchestrator.py`: Coordinates agent interactions and manages research sessions
  - `google_engineer_agent.py`: Engineering implementation perspectives
  - `mit_researcher_agent.py`: Academic research analysis
  - `industry_expert_agent.py`: Commercial applications focus
  - `paper_analyst_agent.py`: Deep paper analysis
- **Vector Database Integration** (`backend/database/vector_db/`): Multiple vector DB adapters (ChromaDB, Weaviate, Pinecone, Qdrant)
- **ArXiv Integration** (`backend/retrieval/arxiv_client.py`): Academic paper retrieval
- **Task System** (`backend/tasks/`): Celery-based async job processing
- **Job Logging** (`backend/utils/job_logger.py`, `backend/services/job_log_service.py`): Comprehensive logging with Elasticsearch integration

### Frontend Structure
- **Next.js Application** (`frontend/`): Modern React-based UI
- **Dashboard Pages** (`frontend/app/(dashboard)/`): Job management, history, and real-time logs
- **Component Library** (`frontend/components/`): Reusable UI components with shadcn/ui
- **API Integration** (`frontend/lib/api.ts`): SWR-based data fetching hooks

### Infrastructure
- **Docker Compose Setup** (`infra/docker/`): Complete containerized development environment
- **Database Migrations** (`backend/database/migrations/`): SQL migration system
- **Middleware Services**: PostgreSQL, Redis, Weaviate, Elasticsearch, Kibana

## Development Commands

### Start Development Environment
```bash
# Start all middleware services (PostgreSQL, Redis, Weaviate, Elasticsearch)
make docker-run-middleware

# Start API server
make run-api

# Start frontend development server
cd frontend && npm run dev
```

### Build and Test
```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run tests with coverage
make test-cov

# Build frontend
cd frontend && npm run build

# Build all components
make build
```

### Docker Operations
```bash
# Full stack with Docker
make docker-run

# Stop all services
make docker-stop

# Check service health
make docker-health

# View logs
make docker-logs
```

### Database Operations
```bash
# Run database migrations
cd backend && python run_migration.py

# Access PostgreSQL shell
make docker-db-shell

# Access Redis shell
make docker-redis-shell
```

## Key Configuration

### Environment Setup
Copy `infra/docker/env.template` to `.env` and configure:
- API keys for OpenAI, DeepSeek, Anthropic
- Database connection strings
- Service ports and credentials

### Agent Configuration
Each agent can be configured independently in `backend/config.py` with different LLM providers, models, and parameters.

### Vector Database Configuration
The system supports multiple vector databases configured in `backend/database/vector_db/`. Default is ChromaDB for development.

## Important Development Notes

### Multi-Agent System
- The `ResearchOrchestrator` in `backend/agents/orchestrator.py` manages agent interactions
- Each agent extends `BaseAgent` and implements specialized analysis methods
- Agents can run in parallel or sequential workflows

### Async Task Processing
- Uses Celery for background job processing
- Job progress and logs are tracked in PostgreSQL
- Real-time updates via WebSocket integration

### Database Schema
- Main tables: `cronjobs`, `job_runs`, `job_logs`, `job_log_entries`
- Vector embeddings stored in chosen vector database
- Migration system handles schema evolution

### Frontend Architecture
- Server-side rendering with Next.js App Router
- Real-time job monitoring with WebSocket hooks
- Data fetching with SWR for caching and revalidation
- Component library based on Radix UI and Tailwind CSS

### Testing Strategy
- Backend tests in `tests/` directory using pytest
- Frontend tests with built-in Next.js testing
- Docker-based integration testing
- Comprehensive health checks for all services

## Service Ports
- Backend API: 8000
- Frontend: 3000
- PostgreSQL: 5433
- Redis: 6379
- Weaviate: 8080
- Elasticsearch: 9200
- Kibana: 5601

## Common Workflows

### Adding New Agents
1. Create new agent class extending `BaseAgent` in `backend/agents/`
2. Implement required analysis methods
3. Register agent in `orchestrator.py`
4. Add configuration in `config.py`

### Database Changes
1. Create migration file in `backend/database/migrations/`
2. Run migration: `cd backend && python run_migration.py`
3. Update models in `backend/database/models.py`

### Frontend Components
1. Create components in `frontend/components/`
2. Follow existing patterns for API integration
3. Use shadcn/ui components for consistency
4. Implement proper TypeScript types