.PHONY: help install install-backend install-frontend install-system-deps run-backend run-frontend run dev clean venv

# Variables
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(PYTHON) -m pip
UVICORN = $(PYTHON) -m uvicorn

# Default target
help:
	@echo "🔧 Weaver - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install           - Install all dependencies (backend + frontend)"
	@echo "  make install-backend   - Install backend dependencies only"
	@echo "  make install-frontend  - Install frontend dependencies only"
	@echo "  make install-system-deps - Install system dependencies (poppler for PDF)"
	@echo "  make venv              - Create Python virtual environment"
	@echo ""
	@echo "Running:"
	@echo "  make run-backend       - Start backend API server (port 8000)"
	@echo "  make run-frontend      - Start frontend dev server (port 3000)"
	@echo "  make dev               - Start both backend and frontend (parallel)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate           - Run database migrations"
	@echo "  make migration         - Create new migration (auto-generate)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean             - Clean build artifacts and caches"
	@echo "  make lint              - Run linters for backend and frontend"
	@echo "  make test              - Run tests"
	@echo ""

# Create virtual environment
venv:
	@echo "🐍 Checking Python version..."
	@PYTHON_CMD=$$(command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3 2>/dev/null); \
	if [ -z "$$PYTHON_CMD" ]; then \
		echo "❌ Error: Python 3 not found. Please install Python 3.11 or higher."; \
		exit 1; \
	fi; \
	PYTHON_VER=$$($$PYTHON_CMD --version 2>&1 | awk '{print $$2}'); \
	PYTHON_MAJOR=$$(echo $$PYTHON_VER | cut -d. -f1); \
	PYTHON_MINOR=$$(echo $$PYTHON_VER | cut -d. -f2); \
	if [ "$$PYTHON_MAJOR" -lt 3 ] || ([ "$$PYTHON_MAJOR" -eq 3 ] && [ "$$PYTHON_MINOR" -lt 11 ]); then \
		echo "❌ Error: Python 3.11+ required (pyproject.toml), but found Python $$PYTHON_VER"; \
		echo "   Please install Python 3.11 or higher: brew install python@3.11"; \
		exit 1; \
	fi; \
	echo "✅ Found Python $$PYTHON_VER at $$PYTHON_CMD"; \
	if [ -d "$(VENV_DIR)" ]; then \
		echo "⚠️  Virtual environment already exists. Removing old venv..."; \
		rm -rf $(VENV_DIR); \
	fi; \
	echo "🐍 Creating Python virtual environment with $$PYTHON_CMD..."; \
	$$PYTHON_CMD -m venv $(VENV_DIR); \
	echo "✅ Virtual environment created at ./$(VENV_DIR)"

# Install system dependencies (poppler for pdf2image, ffmpeg for audio transcription)
install-system-deps:
	@echo "📦 Installing system dependencies..."
	@if command -v brew >/dev/null 2>&1; then \
		echo "🍺 Detected Homebrew (macOS)"; \
		brew install poppler ffmpeg || echo "⚠️  poppler/ffmpeg may already be installed"; \
	elif command -v apt-get >/dev/null 2>&1; then \
		echo "🐧 Detected apt-get (Debian/Ubuntu)"; \
		sudo apt-get update && sudo apt-get install -y poppler-utils ffmpeg; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "🎩 Detected dnf (Fedora/RHEL)"; \
		sudo dnf install -y poppler-utils ffmpeg; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "🏴 Detected pacman (Arch)"; \
		sudo pacman -S --noconfirm poppler ffmpeg; \
	else \
		echo "⚠️  Could not detect package manager. Please install poppler-utils and ffmpeg manually."; \
		echo "   - macOS: brew install poppler ffmpeg"; \
		echo "   - Debian/Ubuntu: apt-get install poppler-utils ffmpeg"; \
		echo "   - Fedora/RHEL: dnf install poppler-utils ffmpeg"; \
	fi
	@echo "✅ System dependencies installed!"

# Install all dependencies
install: venv install-system-deps install-backend install-frontend
	@echo "✅ All dependencies installed successfully!"
	@echo ""
	@echo "💡 To activate the virtual environment manually:"
	@echo "   source $(VENV_DIR)/bin/activate"

# Install backend dependencies
install-backend: venv
	@echo "📦 Installing backend dependencies..."
	@$(PIP) install --upgrade pip setuptools wheel
	@cd app/backend && ../../$(PIP) install -e .
	@echo "✅ Backend dependencies installed!"

# Install frontend dependencies
install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd app/frontend && npm install
	@echo "✅ Frontend dependencies installed!"

# Run backend API server
run-backend: venv
	@echo "🚀 Starting backend API server on http://localhost:8000"
	@echo "📚 API docs: http://localhost:8000/docs"
	@if [ ! -f .env ]; then \
		echo "⚠️  Warning: .env file not found. Copy from env.example and configure."; \
	fi
	cd app/backend && ../../$(UVICORN) research_agent.main:app --reload --host 0.0.0.0 --port 8000

# Alias for run-backend
run-api: run-backend

# Run frontend dev server
run-frontend:
	@echo "🚀 Starting frontend dev server on http://localhost:3000"
	cd app/frontend && npm run dev

# Run both backend and frontend in parallel (requires GNU parallel or use separate terminals)
dev:
	@echo "🚀 Starting both backend and frontend..."
	@echo "⚠️  Note: This requires two terminal windows. Use 'make run-backend' and 'make run-frontend' in separate terminals."
	@echo ""
	@echo "Terminal 1: make run-backend"
	@echo "Terminal 2: make run-frontend"

# Clean build artifacts and caches
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	cd app/frontend && rm -rf .next node_modules/.cache 2>/dev/null || true
	@echo "✅ Cleaned!"

# Clean everything including virtual environment
clean-all: clean
	@echo "🧹 Removing virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "✅ Everything cleaned!"

# Run linters
lint: venv
	@echo "🔍 Running linters..."
	cd app/backend && ../../$(PYTHON) -m ruff check .
	cd app/frontend && npm run lint
	@echo "✅ Linting complete!"

# Run tests
test: venv
	@echo "🧪 Running tests..."
	cd app/backend && ../../$(PYTHON) -m pytest
	@echo "✅ Tests complete!"

# Database migrations
migrate: venv
	@echo "🗄️  Running database migrations..."
	cd app/backend && ../../$(PYTHON) -m alembic upgrade head
	@echo "✅ Migrations complete!"

# Create new migration
migration: venv
	@echo "🗄️  Creating new migration..."
	@read -p "Migration message: " msg; \
	cd app/backend && ../../$(PYTHON) -m alembic revision --autogenerate -m "$$msg"

# Check environment setup
check-env:
	@echo "🔍 Checking environment setup..."
	@echo ""
	@echo "Python version:"
	@python3 --version || echo "❌ Python 3 not found"
	@echo ""
	@echo "Node version:"
	@node --version || echo "❌ Node.js not found"
	@echo ""
	@echo "npm version:"
	@npm --version || echo "❌ npm not found"
	@echo ""
	@echo "Poppler (for Gemini PDF OCR):"
	@if command -v pdftoppm >/dev/null 2>&1; then \
		echo "✅ poppler-utils installed (pdftoppm found)"; \
	else \
		echo "⚠️  poppler-utils not found (required for Gemini OCR, run 'make install-system-deps')"; \
	fi
	@echo ""
	@echo "Environment file:"
	@if [ -f .env ]; then echo "✅ .env file exists"; else echo "⚠️  .env file not found (copy from env.example)"; fi
	@echo ""

# Setup development environment (first time setup)
setup: check-env
	@echo "🎯 Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from env.example..."; \
		cp env.example .env; \
		echo "⚠️  Please edit .env and add your API keys!"; \
	fi
	@$(MAKE) install
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "  1. Edit .env file with your API keys"
	@echo "  2. Run 'make migrate' to setup database"
	@echo "  3. Run 'make run-backend' in one terminal"
	@echo "  4. Run 'make run-frontend' in another terminal"
	@echo ""

