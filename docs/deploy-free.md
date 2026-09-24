# Размещение CRM на бесплатном сервере (тест)

Главный принцип из ТЗ: **бесплатный хостинг — временный слой**.  
PostgreSQL, файлы и конфиг должны переезжать на обычный VPS без потери данных.

## Схема (рекомендуется)

| Часть | Где | Зачем |
|-------|-----|-------|
| **БД** | [Supabase](https://supabase.com) — Free PostgreSQL | надёжная БД, есть export |
| **Backend** | [Railway](https://railway.app) или [Render](https://render.com) | Docker, есть free/trial |
| **Frontend** | тот же Railway/Render | один сервис или отдельно |
| **Файлы** | volume на том же сервисе **или** S3 (Cloudflare R2 / Backblaze B2) | не ephemeral disk |
| **Backup** | cron на сервере → ваш диск / облако | 7 daily / 4 weekly / 3 monthly |

> Не храните рабочие файлы только на ephemeral-диске бесплатного сервиса.

---

## Шаг 1. БД — Supabase (5 минут)

1. Зарегистрируйтесь на https://supabase.com → **New project**
2. Запомните регион (лучше EU)
3. **Project Settings → Database → Connection string → URI**
4. Замените `postgres://` на `postgresql+psycopg://`  
   Пример:
   ```
   postgresql+psycopg://postgres:ПАРОЛЬ@db.xxxxx.supabase.co:5432/postgres
   ```
5. Это значение — `DATABASE_URL`

Бэкап: Supabase → Database → Backups, плюс наш `scripts/backup.sh`.

---

## Шаг 2. Backend — Railway (самый простой путь)

1. https://railway.app → **New Project → Deploy from GitHub repo**
2. Выложите папку `crm` на GitHub (без `.env`)
3. **Root Directory** = `backend` (или весь репозиторий + Dockerfile)
4. **Variables** (Settings → Variables):

| Переменная | Пример |
|------------|--------|
| `DATABASE_URL` | `postgresql+psycopg://...` из Supabase |
| `SECRET_KEY` | длинная случайная строка (сгенерируйте) |
| `ADMIN_EMAIL` | `admin@kit-lab.by` |
| `ADMIN_PASSWORD` | **смените** с `ChangeMe!2026` |
| `APP_ENV` | `production` |
| `STORAGE_BACKEND` | `local` |
| `STORAGE_LOCAL_PATH` | `/data/uploads` |
| `LOGIN_RATE_LIMIT_ENABLED` | `true` |
| `PORT` | `8000` |

5. **Start Command** (если спросит):
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
6. **Volume** (если есть): смонтируйте `/data/uploads` — иначе файлы пропадут при redeploy

После старта:
- `https://ваш-проект.up.railway.app/health/live` → `{"status":"ok"}`
- `https://ваш-проект.up.railway.app/docs` → Swagger (в production закроется)

---

## Шаг 3. Frontend (можно на том же Railway)

**Вариант А — быстро для теста:** отдавайте статику Next.js:

1. Отдельный сервис с Root Directory = `frontend`
2. Build: `npm run build` · Start: `npm run start`
3. Переменная `NEXT_PUBLIC_API_URL` = URL backend из шага 2

**Вариант Б — бесплатно дольше:** Vercel / Netlify (Static Next.js) + тот же API URL.

---

## Шаг 4. Backup (обязательно)

На сервере / в cron:

```bash
# каждый день в 02:00
0 2 * * * cd /opt/crm && bash scripts/backup.sh /backups/$(date +\%Y\%m\%d) >> /var/log/crm-backup.log 2>&1
```

Проверка восстановления (раз в месяц):

```bash
bash scripts/restore.sh /backups/последний
bash scripts/verify_restore.sh /backups/последний
```

**Backup без проверки restore — не backup.**

---

## Шаг 5. Когда захотите «настоящий» сервер (VPS)

1. VPS с Ubuntu + Docker
2. `git clone` репозитория
3. `cp .env.example .env` → заполнить
4. `docker compose up -d`
5. `alembic upgrade head` / первый старт создаст таблицы
6. `bash scripts/restore.sh <backup>` если переносите данные
7. `bash scripts/verify_restore.sh`
8. HTTPS: Caddy / Traefik / nginx
9. Сверка: количество контрагентов, договоров, протоколов, файлов

Подробности — `docs/runbook-vps.md`.

---

## Чек-лист перед «боевым» использованием

- [ ] `ADMIN_PASSWORD` сменён
- [ ] `SECRET_KEY` — длинный случайный, не `CHANGE_ME`
- [ ] HTTPS включён
- [ ] Backup настроен и **restore проверен**
- [ ] Файлы не только на ephemeral disk
- [ ] Supabase / платформа: включён внешний экспорт БД

---

## Ограничения free-тарифов (2026 — проверьте перед стартом)

| Платформа | Риск |
|-----------|------|
| Render free | сервис засыпает, диск не persistent |
| Railway | лимиты CPU/RAM/volume после trial |
| Supabase free | может приостановить неактивный проект; auto-backup платный |

Поэтому: **данные = Supabase + ежедневный внешний backup**, а хостинг — временный.

---

## Быстрый старт «на столе» (без сервера)

```bash
cd crm
cp .env.example .env
docker compose up
```

Frontend: http://localhost:3000 · API: http://localhost:8000/docs
