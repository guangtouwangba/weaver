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

1. topic 管理
 - 用户可以创建、编辑和删除 topic
 - 用户可以将 topic 关联到文档

2. RAG
  - 用户可以上传文档
  - 系统会自动将文档转换为知识片段
  - 用户可以和文档进行chat
  - 用户可以对文档进行搜索

3. 知识图谱
    - 用户可以创建、编辑和删除知识图谱
    - 用户可以将知识片段关联到知识图谱
    - 用户可以在知识图谱中进行搜索


## 开发指导

- 确保内容是模块化的内容
- 每个模块都有自己职责
- 遵循 SOLID 原则
- 不要动不动就写Markdown文件进行总结
- 使用TDD来进行开发，最小化代码变更
- 所有的注释和文档都需要英文描述