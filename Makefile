VENV ?= .venv
UV ?= uv
APP_MODULE ?= apps.api.app:app
HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: help venv install install-dev sync run test lint format clean

help:
	@echo "Available targets:"
	@echo "  venv         Create a virtual environment using uv"
	@echo "  install      Install application dependencies"
	@echo "  install-dev  Install app + developer dependencies"
	@echo "  sync         Sync dependencies using uv (faster)"
	@echo "  run          Launch FastAPI via uvicorn"
	@echo "  test         Run pytest suite"
	@echo "  lint         Run Ruff linting"
	@echo "  format       Format code with Ruff"
	@echo "  clean        Remove caches and compiled artifacts"

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment with uv at $(VENV)"; \
		$(UV) venv $(VENV); \
	fi

install: venv
	$(UV) pip install -e .

install-dev: venv
	$(UV) pip install -e .[dev]

sync: venv
	$(UV) pip sync pyproject.toml

run:
	@echo "================================================================"
	@echo "Starting FastAPI with Runtime Evaluation support..."
	@echo "================================================================"
	@echo "App module: $(APP_MODULE)"
	@echo "Host: $(HOST):$(PORT)"
	@echo "Loading environment from .env file in project root..."
	@echo ""
	@if [ ! -f ".env" ]; then \
		echo "⚠️  WARNING: .env file not found!"; \
		echo "Copy env.example to .env and configure it."; \
		exit 1; \
	fi
	@echo "✅ Found .env file"
	@echo "================================================================"
	@echo ""
	@export KMP_DUPLICATE_LIB_OK=TRUE && $(UV) run uvicorn $(APP_MODULE) --reload --host $(HOST) --port $(PORT)

test:
	@echo "Running tests in .venv environment..."
	$(UV) run pytest packages/rag-core/tests/ -v
	
test-all:
	@echo "Running all tests..."
	$(UV) run pytest -v

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .ruff_cache $(VENV)
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
