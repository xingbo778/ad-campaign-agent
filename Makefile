.PHONY: help install install-dev test lint format clean start-services stop-services start-orchestrator stop-orchestrator restart-all

# Default target
help:
	@echo "Ad Campaign Agent - Available Commands:"
	@echo ""
	@echo "  make install          - Install dependencies (from requirements.txt)"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make lint             - Run linters (flake8, mypy)"
	@echo "  make format           - Format code with black"
	@echo "  make clean            - Clean cache and temporary files"
	@echo ""
	@echo "Service Management:"
	@echo "  make start-services   - Start all microservices"
	@echo "  make stop-services    - Stop all microservices"
	@echo "  make start-orchestrator - Start orchestrator service"
	@echo "  make stop-orchestrator  - Stop orchestrator service"
	@echo "  make restart-all      - Restart all services"
	@echo ""
	@echo "Development:"
	@echo "  make venv             - Create virtual environment"
	@echo "  make setup            - Full setup (venv + install)"

# Virtual environment
venv:
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3.11 -m venv venv; \
	fi
	@echo "Virtual environment ready"

# Installation
install: venv
	@echo "Installing dependencies..."
	@./venv/bin/pip install --upgrade pip
	@./venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

install-dev: install
	@echo "Installing development dependencies..."
	./venv/bin/pip install -r requirements.txt
	./venv/bin/pip install black flake8 mypy pytest-cov

setup: venv install
	@echo "Setup complete!"

# Testing
test:
	@echo "Running tests..."
	@if [ ! -d "venv" ] || [ ! -f "venv/bin/python" ]; then \
		echo "⚠️  Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@./venv/bin/python -m pytest tests/ -v --tb=short --durations=10

test-parallel:
	@echo "Running tests in parallel (requires pytest-xdist)..."
	@if [ ! -d "venv" ] || [ ! -f "venv/bin/python" ]; then \
		echo "⚠️  Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@./venv/bin/pip install -q pytest-xdist || echo "⚠️  pytest-xdist not installed. Install with: pip install pytest-xdist"
	@./venv/bin/python -m pytest tests/ -n auto -v --tb=short --durations=10

test-fast:
	@echo "Running fast tests only..."
	@./venv/bin/python -m pytest tests/ -m "not slow" -v --tb=short

test-coverage:
	@echo "Running tests with coverage..."
	./venv/bin/pytest tests/ --cov=app --cov-report=html -v

# Linting and formatting
lint:
	@echo "Running linters..."
	./venv/bin/flake8 app/ tests/ --max-line-length=120 --exclude=venv,__pycache__
	./venv/bin/mypy app/ --ignore-missing-imports

format:
	@echo "Formatting code..."
	./venv/bin/black app/ tests/ --line-length=120

format-check:
	@echo "Checking code format..."
	./venv/bin/black app/ tests/ --line-length=120 --check

# Cleanup
clean:
	@echo "Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	@echo "Clean complete"

# Service management
start-services:
	@echo "Starting all microservices..."
	@bash scripts/start_services.sh

stop-services:
	@echo "Stopping all microservices..."
	@bash scripts/stop_services.sh

start-orchestrator:
	@echo "Starting orchestrator..."
	@bash scripts/start_orchestrator_llm.sh

stop-orchestrator:
	@echo "Stopping orchestrator..."
	@bash scripts/stop_orchestrator.sh

restart-all: stop-services stop-orchestrator
	@sleep 2
	@$(MAKE) start-services
	@sleep 2
	@$(MAKE) start-orchestrator
	@echo "All services restarted"

# Health checks
health-check:
	@echo "Checking service health..."
	@./venv/bin/python -c "import requests; \
		services = {'Product': 8001, 'Creative': 8002, 'Strategy': 8003, 'Meta': 8004, 'Logs': 8005, 'Optimizer': 8007}; \
		[print(f'{name}: {\"✓\" if requests.get(f\"http://localhost:{port}/health\", timeout=2).status_code == 200 else \"✗\"}') \
		for name, port in services.items()]"

# Development helpers
logs:
	@echo "Showing recent logs..."
	@tail -f logs/*.log

logs-creative:
	@tail -f logs/creative_service.log

logs-orchestrator:
	@tail -f logs/orchestrator_llm.log

