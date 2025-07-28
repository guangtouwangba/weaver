.PHONY: help install install-dev setup clean lint format test test-cov run-web run-cli run-demo run-api build docs docker-build docker-run update-deps check-deps security-check

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Default target
help: ## Show this help message
	@echo "$(CYAN)Research Agent RAG System - Makefile Commands$(NC)"
	@echo "=================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  1. make setup     - Complete project setup"
	@echo "  2. make run-demo  - Run demonstration"
	@echo "  3. make run-web   - Launch web interface"
	@echo ""

# Installation and Setup
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	poetry install --only=main
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: ## Install all dependencies including development tools
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	poetry install --with=dev --extras=all
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

setup: install-dev setup-env setup-git ## Complete project setup (install deps, setup env, git hooks)
	@echo "$(GREEN)✓ Project setup complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env file and add your API keys"
	@echo "  2. Run 'make run-demo' to test the system"
	@echo "  3. Run 'make run-web' to start the web interface"

setup-env: ## Setup environment file
	@echo "$(BLUE)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)⚠ Created .env file from template. Please add your API keys!$(NC)"; \
	else \
		echo "$(GREEN)✓ .env file already exists$(NC)"; \
	fi
	@mkdir -p data/vector_db
	@mkdir -p logs
	@echo "$(GREEN)✓ Environment setup complete$(NC)"

setup-git: ## Setup git hooks and pre-commit
	@echo "$(BLUE)Setting up git hooks...$(NC)"
	@if command -v git >/dev/null 2>&1; then \
		if [ -d .git ]; then \
			poetry run pre-commit install; \
			echo "$(GREEN)✓ Git hooks installed$(NC)"; \
		else \
			echo "$(YELLOW)⚠ Not a git repository, skipping git hooks$(NC)"; \
		fi \
	else \
		echo "$(YELLOW)⚠ Git not found, skipping git hooks$(NC)"; \
	fi

# Development Tools
lint: ## Run all linting tools
	@echo "$(BLUE)Running linting tools...$(NC)"
	poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	poetry run mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black .
	poetry run isort .
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	poetry run black --check .
	poetry run isort --check-only .
	@echo "$(GREEN)✓ Code formatting check complete$(NC)"

# Testing
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	poetry run pytest -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	poetry run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Tests with coverage complete$(NC)"
	@echo "$(CYAN)Coverage report available at: htmlcov/index.html$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	poetry run pytest -v -m integration
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	poetry run pytest -v -m unit
	@echo "$(GREEN)✓ Unit tests complete$(NC)"

# Running the Application
run-web: ## Launch Streamlit web interface
	@echo "$(BLUE)Launching web interface...$(NC)"
	@echo "$(CYAN)🌐 Open your browser to: http://localhost:8501$(NC)"
	cd $(CURDIR) && poetry run streamlit run chat/chat_interface.py

run-cli: ## Start command-line interface
	@echo "$(BLUE)Starting CLI mode...$(NC)"
	cd $(CURDIR) && poetry run python main.py --mode cli

run-demo: ## Run comprehensive demonstration
	@echo "$(BLUE)Running demonstration...$(NC)"
	cd $(CURDIR) && poetry run python main.py --mode demo

run-api: ## Start API server (when implemented)
	@echo "$(BLUE)Starting API server...$(NC)"
	cd $(CURDIR) && poetry run python main.py --mode api

run-debug: ## Run with debug logging
	@echo "$(BLUE)Running with debug logging...$(NC)"
	cd $(CURDIR) && poetry run python main.py --debug

debug-chat: ## Test chat functionality without Streamlit
	@echo "$(BLUE)Testing chat functionality...$(NC)"
	cd $(CURDIR) && poetry run python debug_chat.py

# Database Management
db-reset: ## Reset vector database
	@echo "$(BLUE)Resetting vector database...$(NC)"
	rm -rf data/vector_db/*
	@echo "$(GREEN)✓ Vector database reset$(NC)"

db-backup: ## Backup vector database
	@echo "$(BLUE)Backing up vector database...$(NC)"
	tar -czf "backups/vector_db_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz" data/vector_db/
	@echo "$(GREEN)✓ Database backup complete$(NC)"

# Documentation
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	poetry run sphinx-build -b html docs/ docs/_build/
	@echo "$(GREEN)✓ Documentation built$(NC)"
	@echo "$(CYAN)Documentation available at: docs/_build/index.html$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	cd docs/_build && python -m http.server 8080

# Docker Support
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t research-agent-rag:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 8501:8501 -v $(PWD)/.env:/app/.env research-agent-rag:latest

docker-dev: ## Run Docker container in development mode
	@echo "$(BLUE)Running Docker container in development mode...$(NC)"
	docker run -it -p 8501:8501 -v $(PWD):/app research-agent-rag:latest bash

# Dependency Management
update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	poetry update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

check-deps: ## Check for dependency vulnerabilities
	@echo "$(BLUE)Checking dependencies for vulnerabilities...$(NC)"
	poetry run pip-audit
	@echo "$(GREEN)✓ Dependency check complete$(NC)"

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	poetry run bandit -r . -x tests/
	@echo "$(GREEN)✓ Security check complete$(NC)"

show-deps: ## Show dependency tree
	@echo "$(BLUE)Dependency tree:$(NC)"
	poetry show --tree

# Build and Release
build: ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	poetry build
	@echo "$(GREEN)✓ Package built$(NC)"

clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

clean-all: clean db-reset ## Clean everything including database
	@echo "$(GREEN)✓ Complete clean finished$(NC)"

# Quality Assurance
qa: format-check lint test ## Run all quality assurance checks
	@echo "$(GREEN)✓ All QA checks passed$(NC)"

pre-commit: qa ## Run pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	poetry run pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks complete$(NC)"

# Environment Management
shell: ## Open poetry shell
	@echo "$(BLUE)Opening poetry shell...$(NC)"
	poetry shell

env-info: ## Show environment information
	@echo "$(CYAN)Environment Information:$(NC)"
	@echo "Python version: $(shell python --version)"
	@echo "Poetry version: $(shell poetry --version)"
	@echo "Virtual env: $(shell poetry env info --path)"
	@echo "Dependencies: $(shell poetry show | wc -l) packages"
	@if [ -f .env ]; then \
		echo "Environment file: ✓ Present"; \
		echo "API Keys configured: $(shell grep -c "API_KEY.*=" .env 2>/dev/null || echo 0)"; \
	else \
		echo "Environment file: ✗ Missing"; \
	fi

# Monitoring and Logs
logs: ## Show application logs
	@echo "$(BLUE)Recent application logs:$(NC)"
	@if [ -d logs ]; then \
		if [ -f logs/chat_interface.log ]; then \
			echo "$(CYAN)=== Chat Interface Logs ===$(NC)"; \
			tail -n 50 logs/chat_interface.log; \
		else \
			echo "$(YELLOW)No chat interface logs found$(NC)"; \
		fi; \
		echo ""; \
		echo "$(CYAN)=== All Log Files ===$(NC)"; \
		ls -la logs/; \
	else \
		echo "$(YELLOW)No log directory found$(NC)"; \
	fi

logs-follow: ## Follow application logs in real-time
	@echo "$(BLUE)Following application logs (Ctrl+C to stop)...$(NC)"
	@if [ -f logs/chat_interface.log ]; then \
		tail -f logs/chat_interface.log; \
	else \
		echo "$(YELLOW)No chat interface log file found$(NC)"; \
	fi

monitor: ## Monitor system resources during development
	@echo "$(BLUE)Monitoring system resources...$(NC)"
	watch -n 2 'echo "Memory usage:"; ps aux | grep -E "(python|streamlit)" | grep -v grep; echo ""; echo "Disk usage:"; df -h data/'

# Maintenance
maintenance: update-deps security-check qa ## Run maintenance tasks
	@echo "$(GREEN)✓ Maintenance tasks complete$(NC)"

health-check: ## Check system health
	@echo "$(BLUE)Performing health check...$(NC)"
	@poetry check
	@echo "$(GREEN)✓ Poetry configuration is valid$(NC)"
	@python -c "import sys; print(f'Python version: {sys.version}')"
	@echo "$(GREEN)✓ Python is working$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✓ Environment file exists$(NC)"; \
	else \
		echo "$(RED)✗ Environment file missing$(NC)"; \
	fi
	@echo "$(GREEN)✓ Health check complete$(NC)"

# Development Shortcuts
dev: install-dev setup-env ## Quick development setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"

quick-start: setup run-demo ## Complete quick start (setup + demo)
	@echo "$(GREEN)✓ Quick start complete$(NC)"

# Help for specific workflows
help-setup: ## Show setup help
	@echo "$(CYAN)Setup Help:$(NC)"
	@echo "1. make setup          - Install everything and setup environment"
	@echo "2. Edit .env file      - Add your OpenAI API key"
	@echo "3. make run-demo       - Test the system"
	@echo "4. make run-web        - Start using the web interface"

help-dev: ## Show development workflow help
	@echo "$(CYAN)Development Workflow:$(NC)"
	@echo "1. make dev            - Setup development environment"
	@echo "2. make format         - Format your code"
	@echo "3. make test           - Run tests"
	@echo "4. make pre-commit     - Run all checks before committing"

help-docker: ## Show Docker help
	@echo "$(CYAN)Docker Workflow:$(NC)"
	@echo "1. make docker-build   - Build Docker image"
	@echo "2. make docker-run     - Run in container"
	@echo "3. make docker-dev     - Development container with shell"