.PHONY: up down lint test build migrate backup restore verify

up:
	docker compose up --build

down:
	docker compose down

lint:
	cd backend && python -m ruff check .
	cd frontend && npm run lint

test:
	cd backend && python -m pytest -q
	cd frontend && npm test --if-present

build:
	cd frontend && npm run build

migrate:
	cd backend && alembic upgrade head

backup:
	bash scripts/backup.sh

restore:
	bash scripts/restore.sh

verify:
	bash scripts/verify_restore.sh
