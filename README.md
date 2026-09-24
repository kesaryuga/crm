# CRM — испытательная / сервисная организация

Модульный монолит: FastAPI + Next.js + PostgreSQL + файловое хранилище (Local/S3).

## Быстрый старт

```bash
cp .env.example .env
docker compose up
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Health: http://localhost:8000/health/live, `/health/ready`

## Структура

- `backend/` — FastAPI, SQLAlchemy 2, Alembic
- `frontend/` — Next.js, TypeScript, Tailwind, shadcn/ui
- `scripts/` — backup / restore / verify_restore
- `docs/` — архитектура и runbook переноса на VPS

## Нумерация документов (решение владельца)

- Номера договоров и протоколов вводятся **вручную** сотрудником.
- Нумерация **со сбросом года** (в новом году — снова №1, №2, …).
- Уникальность: `(document_type, year, number)` — на уровне БД.
- Автоматический counter не используется; UI может подсказать следующий свободный номер.

## Переносимость

PostgreSQL dump + файлы storage + `.env` (без секретов в git) → любой VPS с Docker Compose. Бесплатный хостинг — временный слой.

## Проверки

```bash
make lint
make test
make build
```
