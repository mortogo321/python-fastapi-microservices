.PHONY: lint test typecheck check build up down

lint:
	ruff check .
	ruff format --check .

test:
	pytest -q

typecheck:
	mypy app

check: lint typecheck test

build:
	docker build -t python-fastapi-microservices -f docker/Dockerfile .

up:
	set -a; . ./.env.development; set +a; \
	docker compose -f docker/docker-compose.development.yaml up --build

down:
	docker compose -f docker/docker-compose.development.yaml down
