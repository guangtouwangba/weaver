.PHONY: help install install-uv install-backend install-frontend install-system-deps run-backend run-frontend run dev clean sync

# Variables
VENV_DIR = .venv
UV = uv
PYTHON = $(UV) run python
UVICORN = $(UV) run uvicorn

# Default target
help:
	@echo "🔧 Weaver - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install           - Install all dependencies (backend + frontend)"
	@echo "  make install-backend   - Install backend dependencies only"
	@echo "  make install-frontend  - Install frontend dependencies only"
	@echo "  make install-system-deps - Install system dependencies (poppler for PDF)"
	@echo "  make sync              - Sync dependencies (fast, no reinstall)"
	@echo ""
	@echo "Running:"
	@echo "  make run-backend       - Start backend API server (port 8000)"
	@echo "  make run-frontend      - Start frontend dev server (port 3000)"
	@echo "  make dev               - Start both backend and frontend (parallel)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate           - Run database migrations"
	@echo "  make migration         - Create new migration (auto-generate)"
	@echo "  make clean-migration   - Drop all tables and re-run migrations (DESTRUCTIVE!)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean             - Clean build artifacts and caches"
	@echo "  make lint              - Run linters for backend and frontend"
	@echo "  make test              - Run tests"
	@echo ""

# Install uv if not present
install-uv:
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "📦 Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "✅ uv installed! Please restart your terminal or run: source $$HOME/.local/bin/env"; \
	else \
		echo "✅ uv is already installed"; \
	fi

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
install: install-uv install-system-deps install-backend install-frontend
	@echo ""
	@echo "✅ All dependencies installed successfully!"
	@echo ""
	@echo "💡 To run commands in the virtual environment:"
	@echo "   uv run <command>"
	@echo "   or: source $(VENV_DIR)/bin/activate"

# Install backend dependencies
install-backend: install-uv
	@echo "📦 Installing backend dependencies with uv..."
	@cd app/backend && $(UV) sync
	@echo "✅ Backend dependencies installed!"

# Sync dependencies (fast update without full reinstall)
sync:
	@echo "🔄 Syncing backend dependencies..."
	@cd app/backend && $(UV) sync
	@echo "✅ Dependencies synced!"

# Install frontend dependencies
install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd app/frontend && npm install
	@echo "✅ Frontend dependencies installed!"

# Run backend API server
run-backend:
	@echo "🚀 Starting backend API server on http://localhost:8000"
	@echo "📚 API docs: http://localhost:8000/docs"
	@if [ ! -f .env ]; then \
		echo "⚠️  Warning: .env file not found. Copy from env.example and configure."; \
	fi
	cd app/backend && $(UVICORN) research_agent.main:app --reload --host 0.0.0.0 --port 8000

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
	rm -rf $(VENV_DIR) venv
	rm -rf app/backend/$(VENV_DIR)
	@echo "✅ Everything cleaned!"

# Run linters
lint:
	@echo "🔍 Running linters..."
	cd app/backend && $(UV) run ruff check .
	cd app/frontend && npm run lint
	@echo "✅ Linting complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	cd app/backend && $(UV) run pytest
	@echo "✅ Tests complete!"

# Database migrations
migrate:
	@echo "🗄️  Running database migrations..."
	cd app/backend && $(UV) run alembic upgrade head
	@echo "✅ Migrations complete!"

# Create new migration
migration:
	@echo "🗄️  Creating new migration..."
	@read -p "Migration message: " msg; \
	cd app/backend && $(UV) run alembic revision --autogenerate -m "$$msg"

# Check environment setup
check-env:
	@echo "🔍 Checking environment setup..."
	@echo ""
	@echo "uv version:"
	@uv --version || echo "❌ uv not found (run: make install-uv)"
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

# Clean database and reset migrations (DESTRUCTIVE!)
clean-migration:
	@echo "⚠️  WARNING: This will DROP ALL TABLES in your local database!"
	@echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
	@sleep 3
	@echo "🗄️  Cleaning database..."
	@cd app/backend && $(UV) run python ../../scripts/clean_database.py
	@echo "🗄️  Running migrations..."
	cd app/backend && $(UV) run alembic upgrade head
	@echo "✅ Database clean and migrated!"
