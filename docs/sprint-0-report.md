# Sprint 0 — отчёт

Проект: `C:\Users\Yury\XiaomiMiMoProjects\crm`

## Что сделано

- Monorepo: backend (FastAPI), frontend (Next.js), Docker Compose (frontend, backend, postgres).
- Health: `/health/live`, `/health/ready` (lazy engine, без psycopg на импорте).
- Config из env, `.env.example`, без секретов в git.
- Alembic: `0001_baseline` (пустая baseline, схема — Sprint 1+).
- Frontend: `/`, `/login` (заглушка до Auth).
- CI, Makefile, `scripts/backup.sh`, `restore.sh`, `verify_restore.sh`.
- README + docs (architecture, runbook-vps).

## Решения владельца

- Номера договоров/протоколов — **вручную**, со сбросом года.
- Без НДС; сумма прописью — да; шаблоны договоров — ваши DOCX.
- Каталог проекта: `XiaomiMiMoProjects\crm`.

## Migrations

- `0001_baseline` — без таблиц (schema empty on purpose).

## Tests

| Проверка | Результат |
|----------|-----------|
| pytest (`test_live`) | 1 passed |
| ruff | 0 errors |
| next build | success (/, /login) |

## Как проверить вручную

```bash
cd crm
cp .env.example .env
docker compose up
# UI: http://localhost:3000
# API: http://localhost:8000/health/live

cd backend
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
```

## Известные ограничения

- Docker health check не выполнялся в этой среде (docker недоступен) — compose описан, локальные проверки зелёные.
- Auth/RBAC, CRM-сущности, документы, протоколы — вне Sprint 0 (Sprint 1–6).
- PDF/LibreOffice не проверялись (Sprint 5).

## Риски

- Медленная сеть при установке pip/npm (на этой машине).
- До загрузки ваших DOCX и форм протоколов — демо-правила.

## Следующий sprint

**Sprint 1 — Auth/RBAC:** users, roles, permissions, login/logout, admin bootstrap, audit log.
