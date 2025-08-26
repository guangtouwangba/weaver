# Makefile for Research Agent RAG Project
# Usage: make <target>

.PHONY: help install install-dev install-test install-docs install-prod install-server
.PHONY: install-all setup-dev setup-server
.PHONY: start stop restart status logs clean clean-all
.PHONY: test test-cov lint format check pre-commit
.PHONY: db-init db-migrate db-upgrade db-downgrade
.PHONY: docker-build docker-push docker-pull
.PHONY: server server-dev server-prod server-test server-debug server-gunicorn
.PHONY: server-stop server-status server-restart server-logs server-background
.PHONY: server-full server-quick api-test api-test-quick api-test-health api-test-topics load-test

# Default target
.DEFAULT_GOAL := help

# Variable definitions
PROJECT_NAME := research-agent-rag
PYTHON := python3
# Check if in container, if so use system path
ifeq ($(DEV_CONTAINER),true)
UV := /usr/local/bin/uv
else
UV := $(shell which uv 2>/dev/null || echo uv)
endif
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
	@echo "$(YELLOW)Server Management:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(server)"
	@echo ""
	@echo "$(YELLOW)Worker Management:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(worker)"
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

install-server: ## Install dependencies for server
	@echo "$(BLUE)Installing server dependencies...$(NC)"
	$(UV) pip install -e .
	@echo "$(YELLOW)Installing additional server packages...$(NC)"
	$(UV) pip install minio redis httpx uvicorn[standard] gunicorn
	@echo "$(GREEN)Server dependencies installed!$(NC)"

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

setup-dev: ## Complete development setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@echo "$(YELLOW)Step 1: Installing dependencies...$(NC)"
	@make install-dev
	@echo "$(YELLOW)Step 2: Installing pre-commit hooks...$(NC)"
	@$(UV) run pre-commit install
	@echo "$(YELLOW)Step 3: Starting middleware services...$(NC)"
	@make start
	@echo "$(YELLOW)Step 4: Waiting for services...$(NC)"
	@sleep 10
	@echo "$(YELLOW)Step 5: Initializing database...$(NC)"
	@make db-init
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(BLUE)You can now run: make server$(NC)"

setup-server: ## Complete server setup (production-like)
	@echo "$(BLUE)Setting up server environment...$(NC)"
	@echo "$(YELLOW)Step 1: Installing server dependencies...$(NC)"
	@make install-server
	@echo "$(YELLOW)Step 2: Starting middleware services...$(NC)"
	@make start
	@echo "$(YELLOW)Step 3: Waiting for services...$(NC)"
	@sleep 10
	@echo "$(YELLOW)Step 4: Initializing database...$(NC)"
	@make db-init
	@echo "$(GREEN)Server environment ready!$(NC)"
	@echo "$(BLUE)You can now run: make server-prod$(NC)"

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
	@echo "$(YELLOW)Weaviate UI:$(NC)"
	@if curl -s http://localhost:8091 > /dev/null 2>&1; then \
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
# Server Management
# =============================================================================

server: server-dev ## Start development server (default)

server-dev: ## Start development server with hot reload
	@echo "$(BLUE)Starting RAG API development server...$(NC)"
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@make start > /dev/null 2>&1 || true
	@echo "$(YELLOW)Waiting for middleware services to be ready...$(NC)"
	@sleep 5
	@echo "$(BLUE)Starting FastAPI server with auto-reload...$(NC)"
	@echo "$(YELLOW)Server will be available at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API documentation: http://localhost:8000/docs$(NC)"
	@echo "$(YELLOW)Health check: http://localhost:8000/health$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop the server$(NC)"
	$(UV) run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

server-prod: ## Start production server
	@echo "$(BLUE)Starting RAG API production server...$(NC)"
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@make start > /dev/null 2>&1 || true
	@echo "$(YELLOW)Waiting for middleware services to be ready...$(NC)"
	@sleep 5
	@echo "$(BLUE)Starting FastAPI server for production...$(NC)"
	@echo "$(YELLOW)Server will be available at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Health check: http://localhost:8000/health$(NC)"
	$(UV) run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level warning

server-test: ## Start server for testing
	@echo "$(BLUE)Starting RAG API test server...$(NC)"
	@echo "$(YELLOW)Starting test environment...$(NC)"
	@make start > /dev/null 2>&1 || true
	@sleep 3
	@echo "$(BLUE)Starting FastAPI server for testing...$(NC)"
	$(UV) run uvicorn main:app --host 0.0.0.0 --port 8001 --log-level debug

server-debug: ## Start server with debug logging
	@echo "$(BLUE)Starting RAG API debug server...$(NC)"
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@make start > /dev/null 2>&1 || true
	@sleep 5
	@echo "$(BLUE)Starting FastAPI server with debug logging...$(NC)"
	@echo "$(YELLOW)Server will be available at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)API documentation: http://localhost:8000/docs$(NC)"
	@echo "$(YELLOW)Debug mode enabled - detailed logging$(NC)"
	$(UV) run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

server-gunicorn: ## Start server with Gunicorn (production alternative)
	@echo "$(BLUE)Starting RAG API with Gunicorn...$(NC)"
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@make start > /dev/null 2>&1 || true
	@sleep 5
	@echo "$(BLUE)Starting Gunicorn server...$(NC)"
	$(UV) run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --log-level info

server-status: ## Check server status
	@echo "$(BLUE)Checking RAG API server status...$(NC)"
	@echo "$(YELLOW)Health Check:$(NC)"
	@if curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Server is running$(NC)"; \
		echo "  $(BLUE)Server Info:$(NC)"; \
		curl -s http://localhost:8000/info | python3 -m json.tool 2>/dev/null || echo "  Unable to fetch server info"; \
	else \
		echo "  $(RED)✗ Server is not running$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Available Endpoints:$(NC)"
	@echo "  $(GREEN)Health Check:$(NC)      http://localhost:8000/health"
	@echo "  $(GREEN)Server Info:$(NC)       http://localhost:8000/info"
	@echo "  $(GREEN)API Documentation:$(NC) http://localhost:8000/docs"
	@echo "  $(GREEN)ReDoc:$(NC)             http://localhost:8000/redoc"
	@echo "  $(GREEN)OpenAPI Schema:$(NC)    http://localhost:8000/openapi.json"
	@echo "  $(GREEN)Topics API:$(NC)        http://localhost:8000/api/v1/topics"
	@echo "  $(GREEN)Metrics:$(NC)           http://localhost:8000/metrics"
	@echo ""
	@echo "$(YELLOW)Middleware Services:$(NC)"
	@echo "  $(GREEN)Weaviate UI:$(NC)       http://localhost:8091"
	@echo "  $(GREEN)MinIO Console:$(NC)     http://localhost:9001"
	@echo "  $(GREEN)Grafana:$(NC)           http://localhost:3000"

server-stop: ## Stop server (find and kill process)
	@echo "$(BLUE)Stopping RAG API server...$(NC)"
	@if pgrep -f "uvicorn main:app" > /dev/null; then \
		echo "$(YELLOW)Found running server process(es):$(NC)"; \
		pgrep -f "uvicorn main:app" | xargs ps -p; \
		echo "$(BLUE)Stopping server...$(NC)"; \
		pkill -f "uvicorn main:app"; \
		sleep 2; \
		if pgrep -f "uvicorn main:app" > /dev/null; then \
			echo "$(YELLOW)Force killing server...$(NC)"; \
			pkill -9 -f "uvicorn main:app"; \
		fi; \
		echo "$(GREEN)Server stopped!$(NC)"; \
	else \
		echo "$(YELLOW)No running server found$(NC)"; \
	fi

server-restart: server-stop server-dev ## Restart development server

server-logs: ## Show server logs (if running in background)
	@echo "$(BLUE)Showing server logs...$(NC)"
	@echo "$(YELLOW)Note: This shows logs if server was started in background$(NC)"
	@if [ -f server.log ]; then \
		tail -f server.log; \
	else \
		echo "$(YELLOW)No log file found. Start server with: make server-background$(NC)"; \
	fi

server-background: ## Start server in background with logging
	@echo "$(BLUE)Starting RAG API server in background...$(NC)"
	@make start > /dev/null 2>&1 || true
	@sleep 5
	@echo "$(BLUE)Starting FastAPI server in background...$(NC)"
	@nohup $(UV) run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > server.log 2>&1 &
	@echo "$$!" > server.pid
	@sleep 2
	@echo "$(GREEN)Server started in background (PID: $$(cat server.pid))$(NC)"
	@echo "$(YELLOW)Server available at: http://localhost:8000$(NC)"
	@echo "$(YELLOW)View logs with: make server-logs$(NC)"
	@echo "$(YELLOW)Stop server with: make server-stop$(NC)"

server-full: ## Start full stack (middleware + server)
	@echo "$(BLUE)Starting full RAG system...$(NC)"
	@echo "$(YELLOW)Step 1: Starting middleware services...$(NC)"
	@make start
	@echo "$(YELLOW)Step 2: Waiting for services to be ready...$(NC)"
	@sleep 10
	@echo "$(YELLOW)Step 3: Running database migrations...$(NC)"
	@make db-upgrade
	@echo "$(YELLOW)Step 4: Starting API server...$(NC)"
	@make server-dev

server-quick: ## Quick start (assumes middleware is running)
	@echo "$(BLUE)Quick starting RAG API server...$(NC)"
	@echo "$(YELLOW)Assuming middleware services are already running...$(NC)"
	@echo "$(YELLOW)Use 'make server-full' for complete startup$(NC)"
	$(UV) run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

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

db-status: ## Check database migration status
	@echo "$(BLUE)Checking database migration status...$(NC)"
	$(UV) run alembic current
	@echo ""
	@echo "$(BLUE)Migration history:$(NC)"
	$(UV) run alembic history --verbose

db-create-migration: ## Create new migration with auto-generated name (Usage: make db-create-migration MSG="your message")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please provide migration message, e.g.: make db-create-migration MSG='add user table'$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating new migration: $(MSG)$(NC)"
	$(UV) run alembic revision --autogenerate -m "$(MSG)"

db-upgrade-to: ## Upgrade to specific migration (Usage: make db-upgrade-to REV=revision_id)
	@if [ -z "$(REV)" ]; then \
		echo "$(RED)Error: Please provide revision ID, e.g.: make db-upgrade-to REV=001$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Upgrading database to revision: $(REV)$(NC)"
	$(UV) run alembic upgrade $(REV)

db-downgrade-to: ## Downgrade to specific migration (Usage: make db-downgrade-to REV=revision_id)
	@if [ -z "$(REV)" ]; then \
		echo "$(RED)Error: Please provide revision ID, e.g.: make db-downgrade-to REV=001$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Downgrading database to revision: $(REV)$(NC)"
	$(UV) run alembic downgrade $(REV)

db-show-sql: ## Show SQL for next upgrade (dry-run)
	@echo "$(BLUE)Showing SQL for next upgrade (dry-run):$(NC)"
	$(UV) run alembic upgrade head --sql

db-stamp: ## Mark database as up-to-date without running migrations (Usage: make db-stamp REV=head)
	@if [ -z "$(REV)" ]; then \
		REV="head"; \
	fi
	@echo "$(BLUE)Stamping database with revision: $(REV)$(NC)"
	$(UV) run alembic stamp $(REV)

db-apply-optimized: ## Apply the optimized database schema directly
	@echo "$(BLUE)Applying optimized database schema...$(NC)"
	@echo "$(YELLOW)Warning: This will replace current schema!$(NC)"
	@read -p "Confirm applying optimized schema? (Type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "$(BLUE)Connecting to database and applying schema...$(NC)"; \
		$(DOCKER_COMPOSE) exec -T postgres psql -U rag_user -d rag_db -f /tmp/database_schema_optimized.sql; \
		echo "$(GREEN)Optimized schema applied!$(NC)"; \
		$(UV) run alembic stamp head; \
		echo "$(GREEN)Database marked as up-to-date$(NC)"; \
	else \
		echo "$(YELLOW)Schema application cancelled$(NC)"; \
	fi

db-backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	$(DOCKER_COMPOSE) exec -T postgres pg_dump -U rag_user -d rag_db > backups/rag_db_backup_$$timestamp.sql; \
	echo "$(GREEN)Database backup created: backups/rag_db_backup_$$timestamp.sql$(NC)"

db-restore: ## Restore database from backup (Usage: make db-restore BACKUP=filename)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)Error: Please provide backup filename, e.g.: make db-restore BACKUP=rag_db_backup_20241215_143022.sql$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "backups/$(BACKUP)" ]; then \
		echo "$(RED)Error: Backup file backups/$(BACKUP) not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring database from backup: $(BACKUP)$(NC)"
	@echo "$(RED)Warning: This will overwrite current database!$(NC)"
	@read -p "Confirm database restore? (Type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(DOCKER_COMPOSE) exec -T postgres psql -U rag_user -d rag_db < backups/$(BACKUP); \
		echo "$(GREEN)Database restored from backup!$(NC)"; \
	else \
		echo "$(YELLOW)Database restore cancelled$(NC)"; \
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

api-test: ## Test API endpoints with Python test script
	@echo "$(BLUE)Running comprehensive API tests...$(NC)"
	$(UV) run python scripts/test_api.py --test full

api-test-quick: ## Quick API health test with curl
	@echo "$(BLUE)Quick testing API endpoints...$(NC)"
	@echo "$(YELLOW)Health Check:$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Server not running"
	@echo ""
	@echo "$(YELLOW)Server Info:$(NC)"
	@curl -s http://localhost:8000/info | python3 -m json.tool || echo "Server not running"

api-test-health: ## Test only health endpoint
	@echo "$(BLUE)Testing health endpoint...$(NC)"
	$(UV) run python scripts/test_api.py --test health

api-test-topics: ## Test topics endpoints
	@echo "$(BLUE)Testing topics endpoints...$(NC)"
	$(UV) run python scripts/test_api.py --test topics

load-test: ## Run simple load test
	@echo "$(BLUE)Running load test on API...$(NC)"
	@echo "$(YELLOW)Note: Make sure server is running$(NC)"
	@if command -v ab > /dev/null; then \
		echo "$(BLUE)Running Apache Bench load test...$(NC)"; \
		ab -n 100 -c 10 http://localhost:8000/health; \
	elif command -v wrk > /dev/null; then \
		echo "$(BLUE)Running wrk load test...$(NC)"; \
		wrk -t10 -c10 -d10s http://localhost:8000/health; \
	else \
		echo "$(YELLOW)No load testing tool found. Install 'ab' or 'wrk'$(NC)"; \
		echo "$(BLUE)Running simple curl test...$(NC)"; \
		for i in $$(seq 1 10); do \
			curl -s http://localhost:8000/health > /dev/null && echo "Request $$i: OK" || echo "Request $$i: FAILED"; \
		done; \
	fi

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


# =============================================================================
# Worker Management
# =============================================================================

worker: ## Start unified worker (all queues)
	@echo "$(BLUE)Starting unified worker for all task types...$(NC)"
	@echo "$(YELLOW)Worker will handle: file, rag, document, workflow tasks$(NC)"
	$(UV) run python worker.py --loglevel=info --specialized=unified

worker-background: ## Start unified worker in background
	@echo "$(BLUE)Starting unified worker in background...$(NC)"
	@mkdir -p logs
	$(UV) run python worker.py --loglevel=info --specialized=unified > logs/worker_unified.log 2>&1 &
	@echo "$(GREEN)Unified worker started in background$(NC)"
	@echo "$(YELLOW)View logs with: tail -f logs/worker_unified.log$(NC)"

worker-stop: ## Stop all workers
	@echo "$(BLUE)Stopping all worker processes...$(NC)"
	@if pgrep -f "worker.py" > /dev/null; then \
		echo "$(YELLOW)Found running worker process(es):$(NC)"; \
		pgrep -f "worker.py" | xargs ps -p; \
		echo "$(BLUE)Stopping workers...$(NC)"; \
		pkill -f "worker.py"; \
		sleep 2; \
		if pgrep -f "worker.py" > /dev/null; then \
			echo "$(YELLOW)Force killing workers...$(NC)"; \
			pkill -9 -f "worker.py"; \
		fi; \
		echo "$(GREEN)All workers stopped!$(NC)"; \
	else \
		echo "$(YELLOW)No running workers found$(NC)"; \
	fi

worker-status: ## Check worker status
	@echo "$(BLUE)Checking worker status...$(NC)"
	@if pgrep -f "worker.py" > /dev/null; then \
		echo "$(GREEN)✓ Workers are running:$(NC)"; \
		ps aux | grep worker.py | grep -v grep | awk '{print "  PID:", $$2, "CPU:", $$3"%", "MEM:", $$4"%", "CMD:", $$11, $$12, $$13, $$14, $$15}'; \
	else \
		echo "$(RED)✗ No workers running$(NC)"; \
	fi

worker-logs: ## Show worker logs
	@echo "$(BLUE)Showing unified worker logs...$(NC)"
	@if [ -f logs/worker_unified.log ]; then \
		tail -f logs/worker_unified.log; \
	else \
		echo "$(YELLOW)No unified worker log found. Start worker with: make worker-background$(NC)"; \
	fi

worker-restart: worker-stop worker-background ## Restart unified worker

# Legacy worker commands (for backward compatibility)
worker-file: ## Start file processing worker (legacy)
	@echo "$(YELLOW)Note: Consider using 'make worker' for unified processing$(NC)"
	$(UV) run python worker.py --loglevel=info --specialized=file

worker-rag: ## Start RAG processing worker (legacy)
	@echo "$(YELLOW)Note: Consider using 'make worker' for unified processing$(NC)"
	$(UV) run python worker.py --loglevel=info --specialized=rag

worker-document: ## Start document processing worker (legacy)
	@echo "$(YELLOW)Note: Consider using 'make worker' for unified processing$(NC)"
	$(UV) run python worker.py --loglevel=info --specialized=document