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
	@echo "  3. make run-web      - Launch web interface"
	@echo "  4. make run-frontend - Launch modern UI"
	@echo "  5. make run-fullstack- Launch both backend + frontend"
	@echo ""

# Installation and Setup
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	cd $(BACKEND_DIR) && poetry install --only=main
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: ## Install all dependencies including development tools
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	cd $(BACKEND_DIR) && poetry install --with=dev --extras=all
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

setup: install-dev setup-env setup-git ## Complete project setup (install deps, setup env, git hooks)
	@echo "$(GREEN)✓ Project setup complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env file and add your API keys"
	@echo "  2. Run 'make run-demo' to test the system"
	@echo "  3. Run 'make run-web' to start the web interface"
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
			cd $(BACKEND_DIR) && poetry run pre-commit install; \
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
	cd $(BACKEND_DIR) && poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	cd $(BACKEND_DIR) && poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	cd $(BACKEND_DIR) && poetry run mypy . --ignore-missing-imports
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	cd $(BACKEND_DIR) && poetry run black .
	cd $(BACKEND_DIR) && poetry run isort .
	@echo "$(GREEN)✓ Code formatting complete$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	cd $(BACKEND_DIR) && poetry run black --check .
	cd $(BACKEND_DIR) && poetry run isort --check-only .
	@echo "$(GREEN)✓ Code formatting check complete$(NC)"

# Testing
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	cd $(BACKEND_DIR) && poetry run pytest -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	cd $(BACKEND_DIR) && poetry run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Tests with coverage complete$(NC)"

# Running Applications
run-demo: ## Run demonstration script
	@echo "$(BLUE)Running demonstration...$(NC)"
	cd $(BACKEND_DIR) && poetry run python examples/demo.py

run-web: ## Run Streamlit web interface
	@echo "$(BLUE)Starting Streamlit web interface...$(NC)"
	cd $(BACKEND_DIR) && poetry run streamlit run chat/chat_interface.py --server.port 8501 --server.address 0.0.0.0

run-api: ## Run FastAPI server
	@echo "$(BLUE)Starting FastAPI server...$(NC)"
	cd $(BACKEND_DIR) && poetry run python api/simple_server.py

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
	cd $(BACKEND_DIR) && poetry run python main.py

# Building and Deployment
build: ## Build all components
	@echo "$(BLUE)Building all components...$(NC)"
	@make build-backend
	@make build-frontend
	@echo "$(GREEN)✓ All components built$(NC)"

build-backend: ## Build backend
	@echo "$(BLUE)Building backend...$(NC)"
	cd $(BACKEND_DIR) && poetry build
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

docker-run: ## Run with Docker Compose
	@echo "$(BLUE)Starting with Docker Compose...$(NC)"
	docker-compose -f $(INFRA_DIR)/docker/docker-compose.yml up -d
	@echo "$(GREEN)✓ Application started with Docker$(NC)"

docker-stop: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose -f $(INFRA_DIR)/docker/docker-compose.yml down
	@echo "$(GREEN)✓ Docker containers stopped$(NC)"

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
	cd $(BACKEND_DIR) && poetry update
	cd $(FRONTEND_DIR) && npm update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

check-deps: ## Check for outdated dependencies
	@echo "$(BLUE)Checking dependencies...$(NC)"
	cd $(BACKEND_DIR) && poetry show --outdated
	cd $(FRONTEND_DIR) && npm outdated
	@echo "$(GREEN)✓ Dependency check complete$(NC)"

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	cd $(BACKEND_DIR) && poetry run safety check
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
	cd $(BACKEND_DIR) && poetry run python config_manager.py

# Quick development
dev: run-fullstack ## Quick development setup (alias for run-fullstack)
	@echo "$(GREEN)✓ Development environment ready$(NC)"

# Production
prod: build deploy-docker ## Production deployment
	@echo "$(GREEN)✓ Production deployment complete$(NC)"