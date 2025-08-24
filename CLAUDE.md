# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) knowledge management system based on the NotebookLM concept, implementing an intelligent agent for solving the "island problem" between PDF documents. The project follows modular architecture with clean separation of concerns and SOLID principles.

**Key Architecture:** FastAPI + SQLAlchemy + PostgreSQL + Redis + MinIO + Weaviate + Celery with clean layered architecture (Schema → Repository → Service → API).

**Technology Stack:**
- **Backend:** FastAPI with async/await patterns
- **Database:** PostgreSQL with SQLAlchemy ORM + Alembic migrations
- **Vector Store:** Weaviate for semantic search capabilities  
- **Cache/Queue:** Redis for caching + Celery for background tasks
- **Storage:** MinIO for object storage (S3-compatible)
- **Package Management:** UV for fast Python dependency management
- **Monitoring:** Structured logging + health checks + metrics collection

## Development Commands

### Package Management (UV)
The project uses UV for fast Python package management:
- `make install` - Install production dependencies
- `make install-dev` - Install development dependencies  
- `make install-all` - Install all dependencies
- `make setup-dev` - Complete development environment setup
- `uv add package-name` - Add new dependency
- `uv sync` - Sync dependencies from lock file

### Middleware Services
Docker-based middleware stack with PostgreSQL, Weaviate, Redis, MinIO, Elasticsearch:
- `make start` - Start all middleware services
- `make stop` - Stop all middleware services
- `make status` - Check service status
- `make logs` - View all service logs
- `make health-check` - Check service health

### Development Server
FastAPI application with multiple server modes:
- `make server` or `make server-quick` - Start development server with hot reload
- `make server-prod` - Start production server
- `make server-debug` - Start with debug logging
- `make server-status` - Check server status
- `make server-stop` - Stop running server

### Database Management
Alembic-based database migrations:
- `make db-init` - Initialize database and run migrations
- `make db-migrate` - Create new migration
- `make db-upgrade` - Apply pending migrations
- `make db-status` - Check migration status
- `make db-backup` - Create database backup

### Code Quality
- `make format` - Format code with Black and isort
- `make lint` - Run flake8 and mypy linting  
- `make check` - Format and lint code
- `make test` - Run pytest tests
- `make test-cov` - Run tests with coverage
- `make pre-commit` - Run pre-commit hooks

### Testing Individual Components
- `python -m pytest tests/unit/file_loader/` - Run file loader tests
- `python -m pytest tests/integration/ -v` - Run integration tests with verbose output
- `python -m pytest tests/unit/file_loader/test_pdf_loader.py::TestPDFLoader::test_specific_method` - Run specific test
- `python -m pytest -m "not slow"` - Run tests excluding slow ones
- `python -m pytest -m "database"` - Run only database integration tests
- `python -m pytest --cov=modules --cov-report=html` - Generate HTML coverage report

## Architecture Overview

### Core Architecture Layers (Bottom-Up)

**1. Schemas Layer (`modules/schemas/`)**
- Pydantic models for data validation and serialization
- Enums for system-wide constants (FileStatus, ContentType, ProcessingStatus)
- Converter functions between database models and API schemas
- Import pattern: `from modules.schemas import FileSchema, ContentType`

**2. Database Layer (`modules/database/`)**
- SQLAlchemy models and database connection management
- Database service for health checks and basic operations
- Alembic migrations in `alembic/versions/`
- Import pattern: `from modules.database import get_db_session, File, Topic`

**3. Repository Layer (`modules/repository/`)**
- Data access abstraction following Repository pattern
- Interfaces in `interfaces.py`, implementations per entity
- Base repository with common CRUD operations
- Import pattern: `from modules.repository import FileRepository, TopicRepository`

**4. Service Layer (`modules/services/`)**
- Business logic orchestration and domain operations
- Cross-cutting concerns (caching, validation, workflows)
- Task service for async background processing with Celery
- Import pattern: `from modules.services import FileService, TopicService`

**5. API Layer (`modules/api/`)**
- FastAPI routers and HTTP request handling
- Error handlers and response formatting
- Route organization by domain (topics, files, documents)
- Import pattern: `from modules.api import api_router`

### Supporting Modules

**RAG System (`modules/rag/`)**
- Document processing pipeline with orchestrator pattern
- Embedding providers, vector stores, and search capabilities
- Processors for chunking, text processing, and content extraction
- Pipeline management for end-to-end document workflows

**File Processing (`modules/file_loader/`, `modules/file_upload/`)**
- Multi-format file loading (PDF, text, etc.) with factory pattern
- File upload service with signed URLs and storage backends
- Content type detection and metadata extraction
- Support for local, MinIO, and cloud storage

**Storage Backends (`modules/storage/`)**
- Abstracted storage interface with multiple implementations
- MinIO, local filesystem, and mock storage for testing
- Signed URL generation and file management operations

**Task System (`modules/tasks/`)**
- Celery-based async task processing with Redis broker
- Task handlers for file processing, document operations, and RAG workflows
- Priority queues, retry logic, and monitoring
- Decorators for task registration and configuration
- TaskRegistry for managing task handlers and configurations

### Configuration System

**Centralized Config (`config/`)**
- Pydantic Settings with environment variable support and .env file loading
- Nested configuration with delimiter support (e.g., `DATABASE__HOST`)
- Database, storage, Redis, Celery, and AI service configurations
- Environment-specific settings (development, testing, production)
- Comprehensive validation and security checks for production environments
- API documentation settings (Swagger/OpenAPI)

**Import Patterns (All Absolute)**
The codebase uses absolute imports exclusively:
- `from modules.schemas.enums import FileStatus`
- `from modules.services.file_service import FileService`
- `from modules.database.models import Topic, File`

## Core Business Flows

### 1. Topic Management
- Users create, edit, and delete topics through `TopicService`
- Topics can be associated with multiple files and documents
- Status management (active, archived, draft, completed)

### 2. RAG Processing Pipeline
- File upload through signed URLs (`FileService`)
- Document processing via `DocumentOrchestrator`
- Content chunking with multiple strategies (fixed, semantic, paragraph)
- Embedding generation and vector storage
- Semantic search and retrieval capabilities

### 3. Document Lifecycle
- File upload → Processing → Chunking → Embedding → Search Ready
- Background task processing for scalability
- Error handling and retry mechanisms
- Progress tracking and status updates

## Key Development Patterns

### Database Operations
```python
async with get_db_session() as session:
    repository = FileRepository(session)
    file = await repository.create_file(file_data)
```

### Service Layer Usage
```python
file_service = FileService(session, storage_backend)
result = await file_service.confirm_upload(request)
```

### Task Processing
```python
@task_handler("document.process", priority=TaskPriority.HIGH)
class DocumentProcessingHandler(ITaskHandler):
    async def handle(self, document_id: str) -> Dict[str, Any]:
        # Implementation
```

### Error Handling
- Domain-specific exceptions with error codes
- Structured error responses through API layer
- Centralized error handlers in `modules/api/error_handlers.py`

## Database Schema

**Core Tables:**
- `topics` - Topic management with metadata and status
- `files` - File storage with upload status and metadata
- `documents` - Processed document content and chunks
- `topic_files` - Many-to-many relationship between topics and files

**Key Relationships:**
- Topics have many Files (M:N through topic_files)
- Files have many Documents (1:N)
- Documents have many DocumentChunks (1:N)

## Docker Middleware Services

The development environment uses Docker Compose with these services:

- **PostgreSQL** (port 5432): Main database with health checks
- **Weaviate** (port 8080): Vector database for semantic search
- **Redis** (port 6379): Cache and Celery task broker
- **MinIO** (port 9000): S3-compatible object storage
- **Elasticsearch** (port 9200): Full-text search capabilities
- **Grafana** (port 3000): Monitoring dashboards
- **Prometheus** (port 9090): Metrics collection

**Service Management:**
- All services include health checks and automatic restart policies
- Data persistence through named Docker volumes
- Network isolation through `rag-network`
- Service discovery through container names

## Development Guidelines

- All modules follow SOLID principles with clear separation of concerns
- Use absolute imports exclusively (already implemented): `from modules.service import FileService`
- Repository pattern for data access with interface abstractions
- Service layer for business logic orchestration
- Async/await throughout for scalable I/O operations
- Pydantic for data validation and serialization
- Use TDD approach with pytest for all new features
- All comments and documentation in English

## Testing Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions  
- `tests/conftest.py` - Shared test fixtures and configuration
- Mock external dependencies (storage, databases) in unit tests
- Use real services for integration tests with Docker middleware

**Testing Patterns:**
- Automatic test marking based on file location and naming
- Database fixtures with automatic setup/teardown per test
- Async test client with dependency overrides for API testing
- Test database isolation using NullPool and separate test DB
- Comprehensive pytest markers: `integration`, `slow`, `database`, `api`, `fullstack`

## Monitoring and Observability

- Structured logging through `logging_system/` module
- Task monitoring service for Celery queue management
- Health check endpoints for system components
- Prometheus/Grafana integration for metrics collection

## Known Architectural Issues

⚠️ **IMPORTANT: Model/Schema Overlap Issues** - There are currently significant overlaps and unclear responsibilities between models and schemas:

- **Duplicate Enums**: Same enums defined in `modules/models.py` AND `modules/schemas/enums.py`
- **Conflicting DocumentChunk Models**: Three different DocumentChunk definitions with different field names
- **Mixed Responsibilities**: `modules/models.py` contains domain models, API models, enums, and exceptions
- **Inconsistent Field Naming**: Same concepts use different field names across layers

**When Working With Models/Schemas:**
- Be aware of these overlaps when making changes
- Check both `modules/models.py` and `modules/schemas/` for existing definitions
- Consider consolidating duplicate enums and standardizing field names
- Prefer using schemas from `modules/schemas/` for API-related work

## Common Troubleshooting

**Import Issues**: All imports are absolute - use `from modules.package import ClassName`
**Database Issues**: Check middleware services with `make status`, run `make db-upgrade`
**Task Processing**: Monitor Celery workers and check task queues in Redis
**File Processing**: Verify storage backend configuration and file permissions
**Model Conflicts**: Check both `modules/models.py` and `modules/schemas/` for duplicate definitions