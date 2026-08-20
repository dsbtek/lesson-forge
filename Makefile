# LessonForge — developer convenience targets.
# Everything runs through Docker Compose; you do not need local Node/Python.

COMPOSE ?= docker compose

.DEFAULT_GOAL := help

.PHONY: help up down logs build ps migrate revision api-shell psql redis-cli \
        test fmt lint obs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Start the full stack (postgres, redis, minio, api, worker, web)
	$(COMPOSE) up --build

down: ## Stop and remove containers (keeps volumes)
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

build: ## Rebuild all images
	$(COMPOSE) build

ps: ## Show container status
	$(COMPOSE) ps

migrate: ## Apply database migrations
	$(COMPOSE) run --rm -e RUN_MIGRATIONS=0 api alembic upgrade head

revision: ## Autogenerate a migration:  make revision m="add table"
	$(COMPOSE) run --rm -e RUN_MIGRATIONS=0 api alembic revision --autogenerate -m "$(m)"

api-shell: ## Open a shell inside the api container
	$(COMPOSE) run --rm api bash

psql: ## Open psql against the database
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-forge} -d $${POSTGRES_DB:-lessonforge}

redis-cli: ## Open redis-cli
	$(COMPOSE) exec redis redis-cli

test: ## Run the API test suite
	$(COMPOSE) run --rm -e RUN_MIGRATIONS=0 api pytest -q

fmt: ## Format API code with ruff
	$(COMPOSE) run --rm -e RUN_MIGRATIONS=0 api ruff format .

lint: ## Lint API code with ruff
	$(COMPOSE) run --rm -e RUN_MIGRATIONS=0 api ruff check .

obs: ## Start the stack + observability profile (prometheus, grafana)
	$(COMPOSE) --profile observability up --build

clean: ## Stop and remove containers AND volumes (destroys data)
	$(COMPOSE) down -v
