# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RAG (Retrieval-Augmented Generation) research project with a modular architecture. The project appears to be in an early development stage with skeleton structure in place.

## Project Structure

The main codebase is in the `rag/` directory with the following components:

- `rag/document_spliter/` - Document splitting/chunking functionality
- `rag/file_loader/` - File loading and processing
- `rag/index/` - Indexing operations
- `rag/knowledge_store/` - Knowledge storage management
- `rag/retriever/` - Information retrieval components
- `rag/router/` - Routing logic
- `rag/vector_store/` - Vector database operations
- `rag/main.py` - Main application entry point

## Development Commands

### Code Quality and Formatting
- `python -m black .` - Format code using Black (configured for line length 88)
- `python -m isort .` - Sort imports using isort (configured with black profile)
- `python -m flake8` - Lint code using flake8 (max line length 88, ignoring E203,W503)
- `python -m mypy .` - Type checking with mypy (ignores missing imports)
- `python -m bandit -r . -x tests/` - Security analysis with bandit

### Pre-commit Hooks
- `pre-commit install` - Install pre-commit hooks
- `pre-commit run --all-files` - Run all pre-commit checks manually

The project uses pre-commit hooks that will automatically run:
- trailing-whitespace removal
- end-of-file-fixer
- yaml validation
- large file checks
- merge conflict detection
- debug statement detection
- docstring checks
- black formatting
- isort import sorting
- flake8 linting
- mypy type checking
- bandit security scanning
- poetry dependency checks

### Testing
- `python -m pytest` - Run tests using pytest

### Package Management
The project uses Poetry for dependency management:
- `poetry check` - Validate pyproject.toml
- `poetry lock` - Update lock file
ge
## Architecture Notes

This appears to be a modular RAG system designed with clear separation of concerns:

1. **File Processing Pipeline**: file_loader → document_spliter → index
2. **Storage Layer**: knowledge_store and vector_store for different data types
3. **Retrieval Layer**: retriever component for information lookup
4. **Routing Layer**: router for request handling and orchestration

The architecture follows a plugin-based approach where each component has a base interface, allowing for different implementations to be swapped in.

## Development Environment

- Python 3.9+ (project uses .venv virtual environment)
- Poetry for dependency management
- Pre-commit hooks for code quality enforcement
- Black, isort, flake8, mypy, and bandit for code standards

## Important Notes

- All Python files in the rag/ directory are currently empty - this appears to be a skeleton project
- The project follows strict code quality standards with comprehensive pre-commit hooks
- Type hints are enforced via mypy
- Security scanning is mandatory via bandit
- The project structure suggests it's designed for extensibility and modularity