PYTHON ?= python
COMPOSE ?= docker compose
ALEMBIC ?= $(PYTHON) -m alembic
LOAD_SCRIPT = scripts/load_data.py

.PHONY: install db-up db-down db-restart db-ps db-logs migrate load reload reset-db adminer verify

install:
	$(PYTHON) -m pip install -r requirements.txt

db-up:
	$(COMPOSE) up -d

db-down:
	$(COMPOSE) down

db-restart:
	$(COMPOSE) restart

db-ps:
	$(COMPOSE) ps

db-logs:
	$(COMPOSE) logs --tail=100

migrate:
	$(ALEMBIC) upgrade head

load:
	$(PYTHON) $(LOAD_SCRIPT)

reload: migrate load

reset-db:
	$(COMPOSE) down -v
	$(COMPOSE) up -d
	$(ALEMBIC) upgrade head
	$(PYTHON) $(LOAD_SCRIPT)

adminer:
	@echo "Adminer: http://localhost:8080"
	@echo "Server: postgres"
	@echo "Username: $${POSTGRES_USER:-claude}"
	@echo "Password: $${POSTGRES_PASSWORD:-pass}"
	@echo "Database: $${POSTGRES_DB:-claude_code_analytics}"

verify:
	$(PYTHON) -m compileall src scripts alembic
