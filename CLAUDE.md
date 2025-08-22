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


### Core Business Flows

1. Topic Management
 - Users can create, edit and delete topics
 - Users can associate topics with documents

2. RAG
  - Users can upload documents
  - System automatically converts documents to knowledge chunks
  - Users can chat with documents
  - Users can search documents

3. Knowledge Graph
    - Users can create, edit and delete knowledge graphs
    - Users can associate knowledge chunks with knowledge graphs
    - Users can search within knowledge graphs


## Development Guidelines

- Ensure content is modular
- Each module has its own responsibilities
- Follow SOLID principles
- Don't write Markdown files for summaries unnecessarily
- Use TDD for development, minimize code changes
- All comments and documentation should be in English