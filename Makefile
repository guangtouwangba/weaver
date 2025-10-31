VENV ?= .venv
UV ?= uv
APP_MODULE ?= app:app
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
	$(UV) run uvicorn $(APP_MODULE) --reload --host $(HOST) --port $(PORT)

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .

format:
	$(UV) run ruff format .

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .ruff_cache $(VENV)
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
