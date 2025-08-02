# Research Agent RAG System Makefile

# Directory variables
FRONTEND_DIR = frontend

# Color variables for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[0;33m
NC = \033[0m

.PHONY: help setup start start-dev stop status test-celery

help:
	@echo "🚀 Research Agent RAG System - 可用命令:"
	@echo ""
	@echo "  setup           - 初始化环境配置"
	@echo "  start           - 启动完整系统 (包括Celery)"
	@echo "  start-dev       - 启动开发环境"
	@echo "  stop            - 停止所有服务"
	@echo "  status          - 查看服务状态"
	@echo "  test-celery     - 测试Celery配置"

setup:
	@echo "📋 初始化环境配置..."
	@if [ ! -f .env ]; then \
		cp infra/docker/env.template .env; \
		echo "✅ 创建了 .env 文件"; \
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

start: setup
	@echo "🚀 启动完整系统..."
	@docker-compose -f infra/docker/docker-compose.middleware.yml up -d
	@sleep 20
	@docker-compose -f infra/docker/docker-compose.yml up -d

start-dev: setup
	@echo "🔧 启动开发环境..."
	@docker-compose -f infra/docker/docker-compose.middleware.yml up -d postgres redis

stop:
	@docker-compose -f infra/docker/docker-compose.yml down
	@docker-compose -f infra/docker/docker-compose.middleware.yml down

status:
	@docker-compose -f infra/docker/docker-compose.middleware.yml ps
	@docker-compose -f infra/docker/docker-compose.yml ps

test-celery:
	@python test-celery.py