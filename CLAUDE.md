# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) knowledge management system based on the NotebookLM concept, implementing an intelligent agent for solving the "island problem" between PDF documents. The project follows Domain-Driven Design (DDD) architecture with clean separation of concerns and SOLID principles.

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
- `make server` or `make server-dev` - Start development server with hot reload
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

## Architecture Overview

### Domain-Driven Design Structure
The codebase implements clean DDD architecture with strict layer separation:

```
domain/           # Core business logic and interfaces
├── topic.py      # Topic entities and value objects
├── fileupload.py # File upload domain models
└── rag_interfaces.py # RAG system contracts (SOLID interfaces)

application/      # Use cases and DTOs (DEPRECATED - moved to services/)
└── dtos/         # Data Transfer Objects
    ├── fileupload/ # File upload request/response DTOs
    └── rag/        # RAG operation DTOs

services/         # Application services (business orchestration)
├── topic_service.py      # Topic management
├── fileupload_services.py # File upload workflows
└── rag_services.py       # RAG document processing

infrastructure/   # External integrations and implementations
├── database/     # PostgreSQL models and repositories
├── storage/      # Multi-provider object storage (MinIO/AWS/GCP/Alibaba)
├── tasks/        # Async task processing system
├── messaging/    # Redis-based pub/sub
└── rag_dependencies.py # RAG dependency injection

api/             # HTTP endpoints and validation
├── topic_routes.py       # Topic CRUD operations
├── file_routes.py        # File upload/download
├── rag_routes.py         # RAG document management
└── task_routes.py        # Async task monitoring
```

### Core Business Flows

1. **File Upload → RAG Processing Pipeline**:
   - File uploaded via signed URL (MinIO/S3)
   - Metadata saved to PostgreSQL
   - Async task triggered for RAG processing
   - Document processed, chunked, embedded, and indexed

2. **Topic-Based Knowledge Organization**:
   - Topics serve as knowledge containers
   - Files associated with topics for organization
   - Cross-topic knowledge discovery and linking

3. **Async Task Processing**:
   - Priority-based Redis queue
   - Background workers for file processing
   - Real-time status updates via WebSocket/SSE
   - Comprehensive error handling and retry logic

### RAG System Architecture

The RAG implementation follows SOLID principles with interface-driven design:

- **Domain Interfaces** (`domain/rag_interfaces.py`): Clean contracts for all RAG components
- **Application Services** (`services/rag_services.py`): Business workflow orchestration
- **Infrastructure** (`infrastructure/rag_dependencies.py`): Concrete implementations and DI
- **API Layer** (`api/rag_routes.py`): REST endpoints for RAG operations

Key RAG interfaces:
- `IDocumentLoader` - Document loading from various sources
- `IDocumentProcessor` - Text chunking and preprocessing  
- `IEmbeddingService` - Vector embedding generation
- `IVectorStore` - Vector similarity search
- `IKnowledgeManager` - Document metadata management
- `ISearchService` - Multi-strategy search (semantic, keyword, hybrid)

### Storage Architecture

Multi-provider storage abstraction supporting:
- **MinIO** (default) - Self-hosted S3-compatible
- **AWS S3** - Amazon cloud storage
- **Google Cloud Storage** - Google cloud storage  
- **Alibaba OSS** - Alibaba cloud storage

Storage factory automatically configures based on environment variables.

### Task Processing System

Sophisticated async task management:
- **Priority Queues**: Normal, High, Critical priority levels
- **Status Tracking**: Pending, Running, Completed, Failed states
- **Error Handling**: Automatic retries with exponential backoff
- **Real-time Updates**: WebSocket and SSE for live progress
- **Metrics**: Task duration, success rates, queue sizes

## Configuration Management

Environment-based configuration via `infrastructure/config.py`:
- **Database**: PostgreSQL connection settings
- **Storage**: Multi-provider storage configuration
- **Redis**: Cache and messaging configuration  
- **Security**: CORS, authentication settings
- **Feature Flags**: Environment-specific toggles

## Testing Strategy

Comprehensive testing approach:
- **Unit Tests**: `tests/unit/` - Domain logic testing
- **Integration Tests**: `tests/integration/` - Service integration
- **API Tests**: End-to-end API functionality
- **Load Tests**: Performance and scalability testing

## Key Development Patterns

1. **Dependency Injection**: Services receive dependencies via constructor injection
2. **Repository Pattern**: Data access abstraction with clean interfaces
3. **CQRS-like Separation**: Clear read/write operation separation
4. **Event-Driven**: Async events for cross-service communication
5. **Factory Pattern**: Multi-provider service instantiation
6. **Strategy Pattern**: Pluggable algorithms (search strategies, storage providers)

## Important Implementation Notes

- **DTOs vs Domain Objects**: Strict separation between API DTOs and domain entities
- **Async-First**: All I/O operations are async for scalability
- **Type Safety**: Comprehensive type hints enforced via mypy
- **Error Boundaries**: Structured error handling with custom exceptions
- **Observability**: Integrated logging, metrics, and health checks
- **Security**: Input validation, content type verification, access controls