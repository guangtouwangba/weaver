# Makefile for Research Agent RAG Project
# Usage: make <target>

.PHONY: help install install-dev install-test install-docs install-prod
.PHONY: start stop restart status logs clean clean-all
.PHONY: test test-cov lint format check pre-commit
.PHONY: db-init db-migrate db-upgrade db-downgrade
.PHONY: docker-build docker-push docker-pull

# 默认目标
.DEFAULT_GOAL := help

# Variable definitions
PROJECT_NAME := research-agent-rag
PYTHON := python3
UV := uv
DOCKER_COMPOSE := docker-compose -f docker-compose.middleware.yaml
ENV_FILE := .env

# Color definitions
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Help information
help: ## Show help information
	@echo "$(BLUE)$(PROJECT_NAME) - Makefile Help$(NC)"
	@echo ""
	@echo "$(YELLOW)Dependency Management:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(install|deps)"
	@echo ""
	@echo "$(YELLOW)Middleware Management:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(start|stop|restart|status|logs)"
	@echo ""
	@echo "$(YELLOW)Development Tools:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(test|lint|format|check)"
	@echo ""
	@echo "$(YELLOW)Database Management:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(db-)"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(clean)"

# =============================================================================
# Dependency Management
# =============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(UV) pip install -e .
	@echo "$(GREEN)Production dependencies installed!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(UV) pip install -e ".[dev]"
	@echo "$(GREEN)Development dependencies installed!$(NC)"

install-test: ## Install test dependencies
	@echo "$(BLUE)Installing test dependencies...$(NC)"
	$(UV) pip install -e ".[test]"
	@echo "$(GREEN)Test dependencies installed!$(NC)"

install-docs: ## Install documentation dependencies
	@echo "$(BLUE)Installing documentation dependencies...$(NC)"
	$(UV) pip install -e ".[docs]"
	@echo "$(GREEN)Documentation dependencies installed!$(NC)"

install-prod: ## Install production environment dependencies
	@echo "$(BLUE)Installing production environment dependencies...$(NC)"
	$(UV) pip install -e ".[prod]"
	@echo "$(GREEN)Production environment dependencies installed!$(NC)"

install-all: install install-dev install-test install-docs install-prod ## Install all dependencies
	@echo "$(GREEN)All dependencies installed!$(NC)"

# =============================================================================
# Middleware Management
# =============================================================================

start: ## Start all middleware services
	@echo "$(BLUE)Starting middleware services...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(YELLOW)Warning: .env file not found, using default configuration$(NC)"; \
	fi
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Middleware services started!$(NC)"
	@echo "$(BLUE)Service status:$(NC)"
	@make status

stop: ## Stop all middleware services
	@echo "$(BLUE)Stopping middleware services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Middleware services stopped!$(NC)"

restart: stop start ## Restart all middleware services

status: ## Check middleware service status
	@echo "$(BLUE)Middleware service status:$(NC)"
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(BLUE)Service health check:$(NC)"
	@make health-check

logs: ## View all service logs
	@echo "$(BLUE)Displaying all service logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f

logs-service: ## View specific service logs (Usage: make logs-service SERVICE=postgres)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: Please specify service name, e.g.: make logs-service SERVICE=postgres$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Displaying $(SERVICE) service logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f $(SERVICE)

health-check: ## Check service health status
	@echo "$(BLUE)Checking service health status...$(NC)"
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@if curl -s http://localhost:5432 > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo "$(YELLOW)Weaviate:$(NC)"
	@if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo "$(YELLOW)Redis:$(NC)"
	@if curl -s http://localhost:6379 > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi

# =============================================================================
# Development Tools
# =============================================================================

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(UV) run pytest

test-cov: ## Run tests and generate coverage report
	@echo "$(BLUE)Running tests and generating coverage report...$(NC)"
	$(UV) run pytest --cov=rag --cov-report=html --cov-report=term

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(UV) run pytest tests/unit/

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(UV) run pytest tests/integration/ -m integration

lint: ## Run code linting
	@echo "$(BLUE)Running code linting...$(NC)"
	$(UV) run flake8 rag/ tests/
	$(UV) run mypy rag/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	$(UV) run black rag/ tests/
	$(UV) run isort rag/ tests/

check: format lint ## Format code and run linting

pre-commit: ## Run pre-commit checks
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	$(UV) run pre-commit run --all-files

# =============================================================================
# Database Management
# =============================================================================

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	@make start
	@echo "$(YELLOW)Waiting for database to start...$(NC)"
	@sleep 10
	$(UV) run alembic upgrade head
	@echo "$(GREEN)Database initialization completed!$(NC)"

db-migrate: ## Create new database migration
	@echo "$(BLUE)Creating new database migration...$(NC)"
	@read -p "Please enter migration description: " description; \
	$(UV) run alembic revision --autogenerate -m "$$description"

db-upgrade: ## Upgrade database to latest version
	@echo "$(BLUE)Upgrading database...$(NC)"
	$(UV) run alembic upgrade head

db-downgrade: ## Rollback database to previous version
	@echo "$(BLUE)Rolling back database...$(NC)"
	$(UV) run alembic downgrade -1

db-reset: ## Reset database (Dangerous operation!)
	@echo "$(RED)Warning: This will delete all data!$(NC)"
	@read -p "Confirm database reset? (Type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(UV) run alembic downgrade base; \
		$(UV) run alembic upgrade head; \
		echo "$(GREEN)Database reset completed!$(NC)"; \
	else \
		echo "$(YELLOW)Database reset cancelled$(NC)"; \
	fi

# =============================================================================
# Docker Management
# =============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(PROJECT_NAME):latest .

docker-push: ## Push Docker image to registry
	@echo "$(BLUE)Pushing Docker image...$(NC)"
	docker push $(PROJECT_NAME):latest

docker-pull: ## Pull latest Docker image
	@echo "$(BLUE)Pulling latest Docker image...$(NC)"
	docker pull $(PROJECT_NAME):latest

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean Python cache and temporary files
	@echo "$(BLUE)Cleaning Python cache and temporary files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-all: clean ## Clean all content including Docker data
	@echo "$(BLUE)Cleaning Docker data...$(NC)"
	$(DOCKER_COMPOSE) down -v
	docker system prune -f
	@echo "$(GREEN)Complete cleanup finished!$(NC)"

# =============================================================================
# Utility Tools
# =============================================================================

shell: ## Start Python interactive shell
	@echo "$(BLUE)Starting Python interactive shell...$(NC)"
	$(UV) run ipython

jupyter: ## Start Jupyter Notebook
	@echo "$(BLUE)Starting Jupyter Notebook...$(NC)"
	$(UV) run jupyter notebook

docs-serve: ## Start documentation server
	@echo "$(BLUE)Starting documentation server...$(NC)"
	$(UV) run mkdocs serve

# =============================================================================
# Environment Management
# =============================================================================

env-create: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(UV) venv
	@echo "$(GREEN)Virtual environment created!$(NC)"

env-activate: ## Activate virtual environment (manual execution required)
	@echo "$(YELLOW)Please manually execute the following commands to activate virtual environment:$(NC)"
	@echo "source .venv/bin/activate  # Linux/Mac"
	@echo ".venv\\Scripts\\activate     # Windows"

# =============================================================================
# Project Information
# =============================================================================

info: ## Display project information
	@echo "$(BLUE)Project information:$(NC)"
	@echo "  Name: $(PROJECT_NAME)"
	@echo "  Python: $(shell $(PYTHON) --version)"
	@echo "  UV: $(shell $(UV) --version)"
	@echo "  Virtual Environment: $(shell if [ -d .venv ]; then echo "Created"; else echo "Not created"; fi)"
	@echo ""
	@echo "$(BLUE)Available commands:$(NC)"
	@make help

version: ## Display project version
	@echo "$(BLUE)Project version:$(NC)"
	$(UV) run python -c "import rag; print(rag.__version__)"
