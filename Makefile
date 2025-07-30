.PHONY: help install install-dev setup clean lint format test test-cov run-web run-cli run-demo run-api run-frontend run-fullstack build docs docker-build docker-run update-deps check-deps security-check

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Project structure
BACKEND_DIR := backend
FRONTEND_DIR := frontend
INFRA_DIR := infra

# Default target
help: ## Show this help message
	@echo "$(CYAN)Research Agent RAG System - Makefile Commands$(NC)"
	@echo "=================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  1. make setup        - Complete project setup"
	@echo "  2. make run-demo     - Run demonstration"
	@echo "  3. make run-api      - Launch FastAPI server"
	@echo "  4. make run-frontend - Launch modern UI"
	@echo "  5. make run-fullstack- Launch both backend + frontend"
	@echo ""

# Installation and Setup
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	poetry install --only=main
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: ## Install all dependencies including development tools
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	@if ! poetry install --with=dev --extras=all 2>/dev/null; then \
		echo "$(YELLOW)⚠ Standard install failed, trying fallback approach...$(NC)"; \
		make fix-onnxruntime; \
	else \
		echo "$(GREEN)✓ All dependencies installed successfully$(NC)"; \
	fi

fix-onnxruntime: ## Fix onnxruntime compatibility issues
	@echo "$(BLUE)Fixing onnxruntime compatibility issues...$(NC)"
	@echo "$(YELLOW)Removing lock file and trying clean install...$(NC)"
	@rm -f poetry.lock
	@echo "$(BLUE)Installing with CPU-only dependencies...$(NC)"
	@poetry install --with=dev --extras=all --no-deps || true
	@echo "$(BLUE)Installing sentence-transformers with CPU backend...$(NC)"
	@poetry run pip install --upgrade pip
	@poetry run pip install sentence-transformers==2.5.1
	@echo "$(BLUE)Installing remaining dependencies...$(NC)"
	@poetry install --with=dev --extras=all || echo "$(YELLOW)⚠ Some optional dependencies may have failed$(NC)"
	@echo "$(GREEN)✓ Dependencies installation completed with workarounds$(NC)"

setup: install-dev setup-env setup-git ## Complete project setup (install deps, setup env, git hooks)
	@echo "$(GREEN)✓ Project setup complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env file and add your API keys"
	@echo "  2. Run 'make run-demo' to test the system"
	@echo "  3. Run 'make run-api' to start the FastAPI server"
	@echo "  4. Run 'make run-frontend' to launch the modern UI"

setup-env: ## Setup environment file
	@echo "$(BLUE)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp $(INFRA_DIR)/.env.development .env; \
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
	poetry run flake8 backend --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 backend --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	poetry run mypy backend --ignore-missing-imports
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black backend
	poetry run isort backend
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	poetry run black --check backend
	poetry run isort --check-only backend
	@echo "$(GREEN)✓ Code formatting check complete$(NC)"

# Testing
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	poetry run pytest tests -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	poetry run pytest tests --cov=backend --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Tests with coverage complete$(NC)"


run-web: run-api ## Legacy alias for FastAPI server (deprecated - use run-api)

run-api: ## Run FastAPI server (default mode)
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	poetry run python backend/main.py

run-frontend: ## Run Next.js frontend
	@echo "$(BLUE)Starting Next.js frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run dev

run-fullstack: ## Run both backend and frontend
	@echo "$(BLUE)Starting full stack application...$(NC)"
	@echo "$(YELLOW)Starting backend...$(NC)"
	@make run-api &
	@sleep 5
	@echo "$(YELLOW)Starting frontend...$(NC)"
	@make run-frontend

run-cli: ## Run command line interface
	@echo "$(BLUE)Starting CLI...$(NC)"
	poetry run python backend/main.py

# Building and Deployment
build: ## Build all components
	@echo "$(BLUE)Building all components...$(NC)"
	@make build-backend
	@make build-frontend
	@echo "$(GREEN)✓ All components built$(NC)"

build-backend: ## Build backend
	@echo "$(BLUE)Building backend...$(NC)"
	poetry build
	@echo "$(GREEN)✓ Backend built$(NC)"

build-frontend: ## Build frontend
	@echo "$(BLUE)Building frontend...$(NC)"
	cd $(FRONTEND_DIR) && npm run build
	@echo "$(GREEN)✓ Frontend built$(NC)"

# Docker Commands
docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker build -f $(INFRA_DIR)/docker/Dockerfile -t research-agent-rag:latest .
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-run-middleware: ## Start middleware services (PostgreSQL, Redis, Weaviate)
	@echo "$(BLUE)Starting middleware services...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml up -d
	@echo "$(GREEN)✓ Middleware services started$(NC)"

docker-run-apps: ## Start application services (requires middleware to be running)
	@echo "$(BLUE)Starting application services...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env up -d
	@echo "$(GREEN)✓ Application services started$(NC)"

docker-run: docker-run-middleware docker-run-apps ## Run with Docker Compose (all services)
	@echo "$(GREEN)✓ All services started with Docker$(NC)"

docker-run-dev: docker-run-middleware ## Run with Docker Compose (development mode)
	@echo "$(BLUE)Starting development application services...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env --profile dev up -d
	@echo "$(GREEN)✓ Development environment started with Docker$(NC)"

docker-run-frontend: ## Run frontend only with Docker
	@echo "$(BLUE)Starting frontend with Docker...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env up -d research-agent-frontend
	@echo "$(GREEN)✓ Frontend started with Docker$(NC)"

docker-run-backend: ## Run backend only with Docker
	@echo "$(BLUE)Starting backend with Docker...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env up -d research-agent-backend
	@echo "$(GREEN)✓ Backend started with Docker$(NC)"

docker-run-admin: docker-run-middleware ## Run with Docker Compose (with admin tools)
	@echo "$(BLUE)Starting admin tools...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml --profile admin up -d
	@echo "$(GREEN)✓ Admin tools started$(NC)"

docker-run-monitoring: docker-run-middleware ## Run with Docker Compose (with monitoring)
	@echo "$(BLUE)Starting monitoring services...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml --profile monitoring up -d
	@echo "$(GREEN)✓ Monitoring services started$(NC)"

docker-stop-apps: ## Stop application containers only
	@echo "$(BLUE)Stopping application containers...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env down
	@echo "$(GREEN)✓ Application containers stopped$(NC)"

docker-stop-middleware: ## Stop middleware containers only
	@echo "$(BLUE)Stopping middleware containers...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml down
	@echo "$(GREEN)✓ Middleware containers stopped$(NC)"

docker-stop: docker-stop-apps docker-stop-middleware ## Stop all Docker containers
	@echo "$(GREEN)✓ All Docker containers stopped$(NC)"

docker-logs: ## Show all Docker logs
	@echo "$(BLUE)Showing all Docker logs...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env logs -f & docker-compose --env-file ../../.env -f docker-compose.middleware.yml logs -f

docker-logs-apps: ## Show application service logs
	@echo "$(BLUE)Showing application logs...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env logs -f

docker-logs-middleware: ## Show middleware service logs
	@echo "$(BLUE)Showing middleware logs...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml logs -f

docker-logs-api: ## Show API service logs
	@echo "$(BLUE)Showing API logs...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env logs -f research-agent-backend

docker-logs-db: ## Show database logs
	@echo "$(BLUE)Showing database logs...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml logs -f postgres weaviate redis

docker-shell: ## Access API container shell
	@echo "$(BLUE)Accessing API container shell...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env exec research-agent-backend bash

docker-db-shell: ## Access PostgreSQL shell
	@echo "$(BLUE)Accessing PostgreSQL shell...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml exec postgres psql -U research_user -d research_agent

docker-redis-shell: ## Access Redis shell
	@echo "$(BLUE)Accessing Redis shell...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml exec redis redis-cli -a redis_password

docker-health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(CYAN)Backend API Health:$(NC)"
	@curl -s http://localhost:8000/health || echo "$(RED)Backend API not responding$(NC)"
	@echo "$(CYAN)Frontend Health:$(NC)"
	@curl -s http://localhost:3000/api/health || echo "$(RED)Frontend not responding$(NC)"
	@echo "$(CYAN)PostgreSQL Health:$(NC)"
	@cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml exec -T postgres pg_isready -U research_user || echo "$(RED)PostgreSQL not ready$(NC)"
	@echo "$(CYAN)Weaviate Health:$(NC)"
	@curl -s http://localhost:8080/v1/.well-known/ready || echo "$(RED)Weaviate not responding$(NC)"
	@echo "$(CYAN)Redis Health:$(NC)"
	@cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml exec -T redis redis-cli -a redis_password ping || echo "$(RED)Redis not responding$(NC)"

docker-test: ## Run comprehensive docker tests
	@echo "$(BLUE)Running Docker setup tests...$(NC)"
	@cd $(INFRA_DIR)/docker && python test-docker-setup.py

docker-deploy: ## Deploy with Docker (development mode)
	@echo "$(BLUE)Deploying with Docker...$(NC)"
	@cd $(INFRA_DIR)/docker && ./deploy.sh

docker-deploy-prod: ## Deploy with Docker (production mode)
	@echo "$(BLUE)Deploying with Docker (production)...$(NC)"
	@cd $(INFRA_DIR)/docker && ./deploy.sh production

docker-deploy-admin: ## Deploy with Docker (admin tools)
	@echo "$(BLUE)Deploying with Docker (admin tools)...$(NC)"
	@cd $(INFRA_DIR)/docker && ./deploy.sh admin

docker-deploy-monitoring: ## Deploy with Docker (monitoring)
	@echo "$(BLUE)Deploying with Docker (monitoring)...$(NC)"
	@cd $(INFRA_DIR)/docker && ./deploy.sh monitoring

docker-backup: ## Backup PostgreSQL database
	@echo "$(BLUE)Backing up PostgreSQL database...$(NC)"
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml exec -T postgres pg_dump -U research_user research_agent > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backup created$(NC)"

docker-restore: ## Restore PostgreSQL database (requires backup file)
	@echo "$(BLUE)Restoring PostgreSQL database...$(NC)"
	@read -p "Enter backup file name: " backup_file; \
	cd $(INFRA_DIR)/docker && docker-compose --env-file ../../.env -f docker-compose.middleware.yml exec -T postgres psql -U research_user research_agent < $$backup_file
	@echo "$(GREEN)✓ Database restored$(NC)"

# Infrastructure
deploy-k8s: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(NC)"
	kubectl apply -f $(INFRA_DIR)/k8s/
	@echo "$(GREEN)✓ Deployed to Kubernetes$(NC)"

deploy-docker: ## Deploy with Docker
	@echo "$(BLUE)Deploying with Docker...$(NC)"
	@make docker-build
	@make docker-run
	@echo "$(GREEN)✓ Deployed with Docker$(NC)"

# Maintenance
clean: ## Clean build artifacts and temporary files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	poetry update
	cd $(FRONTEND_DIR) && npm update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

check-deps: ## Check for outdated dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	poetry show --outdated
	cd $(FRONTEND_DIR) && npm outdated
	@echo "$(GREEN)✓ Dependency check complete$(NC)"

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	poetry run safety check
	cd $(FRONTEND_DIR) && npm audit
	@echo "$(GREEN)✓ Security checks complete$(NC)"

# Documentation
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	cd docs && make html
	@echo "$(GREEN)✓ Documentation built$(NC)"

# Development helpers
logs: ## Show application logs
	@echo "$(BLUE)Showing logs...$(NC)"
	tail -f logs/*.log

status: ## Show application status
	@echo "$(BLUE)Application Status:$(NC)"
	@echo "$(CYAN)Backend:$(NC)"
	@curl -s http://localhost:8000/health || echo "$(RED)Backend not running$(NC)"
	@echo "$(CYAN)Frontend:$(NC)"
	@curl -s http://localhost:3000 > /dev/null && echo "$(GREEN)Frontend running$(NC)" || echo "$(RED)Frontend not running$(NC)"

# Configuration
config: ## Run configuration manager
	@echo "$(BLUE)Running configuration manager...$(NC)"
	poetry run python backend/config_manager.py

# Quick development
dev: run-fullstack ## Quick development setup (alias for run-fullstack)
	@echo "$(GREEN)✓ Development environment ready$(NC)"

# Production
prod: build deploy-docker ## Production deployment
	@echo "$(GREEN)✓ Production deployment complete$(NC)"

# ===== Zeabur Deployment =====
zeabur-deploy-backend: ## Deploy backend to Zeabur
	@echo "$(BLUE)🚀 Deploying backend to Zeabur...$(NC)"
	@echo "$(YELLOW)Make sure you have configured environment variables in Zeabur console$(NC)"
	@echo "$(CYAN)Dockerfile: backend/Dockerfile$(NC)"
	@echo "$(CYAN)Service name: backend$(NC)"
	@echo "$(GREEN)✓ Backend deployment instructions ready$(NC)"

zeabur-deploy-frontend: ## Deploy frontend to Zeabur
	@echo "$(BLUE)🚀 Deploying frontend to Zeabur...$(NC)"
	@echo "$(YELLOW)Make sure you have configured environment variables in Zeabur console$(NC)"
	@echo "$(CYAN)Dockerfile: frontend/Dockerfile$(NC)"
	@echo "$(CYAN)Service name: frontend$(NC)"
	@echo "$(GREEN)✓ Frontend deployment instructions ready$(NC)"

zeabur-deploy-all: zeabur-deploy-backend zeabur-deploy-frontend ## Deploy both services to Zeabur
	@echo "$(GREEN)✅ Both services ready for Zeabur deployment$(NC)"
	@echo "$(YELLOW)📋 Next steps:$(NC)"
	@echo "1. Configure environment variables in Zeabur console"
	@echo "2. Set API_BASE_URL to point to your backend service"
	@echo "3. Check service health in Zeabur dashboard"
	@echo "4. See ZEABUR_DEPLOYMENT.md for detailed instructions"

zeabur-status: ## Show Zeabur deployment status
	@echo "$(BLUE)📊 Zeabur Deployment Status$(NC)"
	@echo "$(CYAN)Backend:$(NC) backend/Dockerfile"
	@echo "$(CYAN)Frontend:$(NC) frontend/Dockerfile"
	@echo "$(CYAN)Config:$(NC) zbpack.json"
	@echo "$(CYAN)Guide:$(NC) ZEABUR_DEPLOYMENT.md"

zeabur-clean: ## Clean up Zeabur deployment files
	@echo "$(BLUE)🧹 Cleaning up Zeabur deployment files...$(NC)"
	@rm -f zbpack.json
	@echo "$(GREEN)✅ Cleaned up Zeabur configuration$(NC)"