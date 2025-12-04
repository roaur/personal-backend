.PHONY: help build up down restart logs test test-fastapi test-celery clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Follow logs for all services
	docker compose logs -f

test: build up test-fastapi test-celery down ## Run all tests

test-fastapi: ## Run FastAPI tests
	@echo "Running FastAPI tests..."
	docker compose run --rm --no-deps fastapi sh -c "cd /app && PYTHONPATH=/app:/app/common pytest tests/ -v"

test-celery: ## Run Celery tests
	@echo "Running Celery tests..."
	docker compose exec celery_producer pytest tests/ -v

test-local-fastapi: ## Run FastAPI tests locally (requires running services)
	docker compose exec fastapi sh -c "cd /app && PYTHONPATH=/app:/app/common pytest tests/ -v"

test-local-celery: ## Run Celery tests locally (requires running services)
	docker compose exec celery_producer pytest tests/ -v

clean: ## Remove all containers, volumes, and images
	docker compose down -v
	docker system prune -f

status: ## Show status of all services
	docker compose ps

rebuild: down build up ## Rebuild and restart all services

rebuild-fastapi: ## Rebuild just the FastAPI service
	docker compose build fastapi
	docker compose up -d fastapi

rebuild-celery: ## Rebuild all Celery services
	docker compose build celery_producer celery_consumer analysis_producer analysis_consumer celery_beat
	docker compose up -d celery_producer celery_consumer analysis_producer analysis_consumer celery_beat
