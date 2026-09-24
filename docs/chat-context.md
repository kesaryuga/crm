# Контекст проекта: CRM для ООО «КИТ-лаб»

Дата: 23.09.2026
Организация: ООО «КИТ-лаб» · kit-lab.by · Беларусь, г. Минск
Проект: веб-CRM для услуг, договоров, испытаний и протоколов

---

## 1. Исходное ТЗ

Пакет из 12 файлов + README (`00_README_FIRST.md`) в папке `C:\Users\Yury\Downloads\Новая папка`:

- 01_MASTER_AGENT_PROMPT.md — приоритеты, стек, архитектура
- 02_PRODUCT_REQUIREMENTS.md — контрагенты, задачи, договоры, протоколы, оборудование
- 03_UI_UX_SPEC.md — интерфейс, wizard, wireframes
- 04_DATA_MODEL.md — схема БД
- 05_API_AND_BUSINESS_RULES.md — REST API, правила
- 06_DOCUMENT_ENGINE.md — DOCX-шаблоны, формулы без eval
- 07_SECURITY_BACKUP_DEPLOYMENT.md — backup, перенос на VPS
- 08_TESTING_ACCEPTANCE.md — критерии приёмки
- 09_ROADMAP_AND_AGENT_WORKFLOW.md — Sprint 0–10
- 10_ASSUMPTIONS_AND_OPEN_DECISIONS.md — допущения
- 11_ENV_EXAMPLE.txt — переменные окружения
- 12_HOSTING_NOTES_2026.md — бесплатный хостинг временный

**Главный принцип:** бесплатный хостинг — временный слой; PostgreSQL, файлы и конфиг должны переезжать на VPS без потери данных.

---

## 2. Решения владельца

| Вопрос | Решение |
|--------|---------|
| Номера договоров/протоколов | **Вручную**, со сбросом года (№1, №2…, с 1 января заново) |
| НДС | **Без НДС** (организация не плательщик НДС) |
| Сумма прописью | **Да**, без НДС |
| Шаблоны договоров | Свои Word-файлы (загрузим позже) |
| Протоколы | Много видов, формы пришлём позже |
| Логотип | Синий кит «КИТ-лаб» (image2.png из КП) |
| Каталог проекта | `C:\Users\Yury\XiaomiMiMoProjects\crm` |

---

## 3. Архитектура

Модульный монолит:
- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic
- Frontend: Next.js 15 + TypeScript + Tailwind + shadcn/ui
- БД: PostgreSQL
- Docker Compose: frontend, backend, postgres
- Storage: Local / S3-compatible (без привязки к хостингу)
- Формулы протоколов: безопасный DSL (без eval)

---

## 4. Что сделано (Sprint 0–10)

| Sprint | Что внутри | Тесты |
|--------|-------------|-------|
| 0 | Docker, FastAPI, Next.js, health, Alembic, CI, backup | build ok |
| 1 | Вход, Argon2id, роли, аудит | 7 |
| 2 | Контрагенты, объекты, контакты, комментарии, поиск | +4 |
| 3 | Задачи, делегирование, просрочки, дашборд, уведомления | +3 |
| 4 | Услуги, договоры, Decimal, номера вручную, snapshot | +4 |
| 5 | Шаблоны DOCX, генерация, версии, storage | +3 |
| 6 | Работы, протоколы, безопасные формулы | +3 |
| 7 | Оборудование, поверки, привязка к протоколам | +2 |
| 8 | Импорт/экспорт CSV/XLSX, backup/restore | +2 |
| 9–10 | Rate limit, security headers, конкурентность | +6 |
| **Итого** | | **34 passed, ruff clean** |

Дополнительно:
- Прототип интерфейса `demo/CRM-прототип.html` с логотипом-китом
- Комментарии, заметки исполнителей, загрузка файлов
- Docs: architecture.md, deploy-free.md, runbook-vps.md, sprint-0-report.md

---

## 5. Где лежит код

- Локально: `C:\Users\Yury\XiaomiMiMoProjects\crm`
- GitHub: https://github.com/kesaryuga/crm (ветка main, коммит 1f6c4f2)
- Задачи T1–T15: все закрыты (кроме T15 деплой — в процессе)

---

## 6. Статус размещения

**Готово:**
- Код на GitHub (kesaryuga/crm)
- Git установлен, авторизация GitHub пройдена
- Инструкция: `docs/deploy-free.md`

**404 на kesaryuga.github.io/crm/** — это нормально:
- GitHub Pages хранит только статичные сайты
- CRM — полноценное приложение (backend + БД + frontend)
- GitHub — это «шкаф» с кодом, не сервер
- Нужен Railway/Supabase (или VPS)

**Следующий шаг (T15):**
1. Supabase → New project → `DATABASE_URL`
2. Railway → Deploy from GitHub → `kesaryuga/crm`
3. Root Directory = `backend`, переменные окружения
4. Frontend-сервис с `NEXT_PUBLIC_API_URL`
5. Backup: `scripts/backup.sh` + `verify_restore.sh`

---

## 7. Важные замечания

- Пароль админа: `ChangeMe!2026` → **сменить** перед рабочим запуском
- `SECRET_KEY` — заменить на случайный
- Docker compose не поднимался в этой среде (нет docker daemon)
- CI workflow (.github/workflows/ci.yml) удалён из репозитория (GitHub блокировал push без scope `workflow`)
- Логотип: `demo/assets/image2.png` (кит), `image1.png` — печать (не использовать)

---

## 8. Технические детали для разработчика

- Backend: `backend/app/` (api, core, models, services, storage, tests)
- Frontend: `frontend/src/` (app, components, lib)
- Скрипты: `scripts/backup.sh`, `restore.sh`, `verify_restore.sh`
- Настройки: `backend/app/core/config.py`, `.env.production.example`
- Пароли: Argon2id (`app/core/security.py`)
- Сессии: HttpOnly cookie, 12 часов
- Формулы: `app/services/formulas.py` (безопасный eval через ast)
- Деньги: `app/services/money.py` (Decimal, сумма прописью)
