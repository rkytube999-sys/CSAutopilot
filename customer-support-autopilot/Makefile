.PHONY: install-backend install-frontend install-dev dev-backend dev-frontend dev-all test-backend lint-backend seed-kb docker-up docker-down clean

# Install backend dependencies
install-backend:
	cd backend && pip install -r requirements.txt

# Install frontend dependencies
install-frontend:
	cd frontend && npm install

# Install all dependencies
install-all: install-backend install-frontend

# Run backend in development mode
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend in development mode
dev-frontend:
	cd frontend && npm run dev

# Run all services (without Docker)
dev-all:
	@echo "Starting backend and frontend..."
	@make dev-backend &
	@sleep 2
	@make dev-frontend

# Run backend tests
test-backend:
	cd backend && pytest tests/ -v

# Lint backend code
lint-backend:
	cd backend && ruff check app/ && mypy app/

# Seed knowledge base
seed-kb:
	python scripts/seed_kb.py --kb knowledge_base/faqs.md

# Docker commands
docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-clean:
	docker compose down -v

# Clean Python cache
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

# Help
help:
	@echo "Customer Support Autopilot - Makefile Commands"
	@echo ""
	@echo "  install-backend   - Install Python dependencies"
	@echo "  install-frontend  - Install Node.js dependencies"
	@echo "  install-all       - Install all dependencies"
	@echo "  dev-backend       - Run backend in development mode"
	@echo "  dev-frontend      - Run frontend in development mode"
	@echo "  dev-all           - Run both backend and frontend"
	@echo "  test-backend      - Run backend tests"
	@echo "  lint-backend      - Lint backend code"
	@echo "  seed-kb           - Seed knowledge base into vector DB"
	@echo "  docker-up         - Start all Docker services"
	@echo "  docker-down       - Stop all Docker services"
	@echo "  docker-clean      - Stop and remove all Docker volumes"
	@echo "  clean             - Clean Python cache and build artifacts"
	@echo "  help              - Show this help message"
