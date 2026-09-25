# CRM на Railway (как gias_bot)

Бесплатный **Trial**: ~30 дней / $5. Дальше Hobby $5/мес или переезд на VPS.

Postgres пока **Supabase** (не Railway) — так надёжнее переносить данные.

## Шаг 1 — GitHub

Код уже в `kesaryuga/crm` (main).

## Шаг 2 — Railway проект

1. https://railway.app → **New Project**
2. **Deploy from GitHub repo** → `kesaryuga/crm`
3. В сервисе:
   - **Root Directory** = `backend`
   - **Dockerfile** = `backend/Dockerfile` (если спрашивает)
4. Variables (Environment → Variables):

```
APP_ENV=staging
APP_NAME=CRM
TIMEZONE=Europe/Minsk
SECRET_KEY=1KClmHzpSbjambMc_KGlYn_C1hjTt4wFwy-OvJwlc4g84PDu50iRJSOyW2MHGNh1
DATABASE_URL=postgresql+psycopg://postgres.chbmuoyuscghinfxywbs:uB1pnoArMMEea8BF1MkV-WbKXvmn5YRb@aws-1-eu-west-1.pooler.supabase.com:5432/postgres?sslmode=require
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=/data/uploads
MAX_UPLOAD_MB=25
LOG_LEVEL=INFO
ADMIN_EMAIL=admin@kit-lab.by
ADMIN_PASSWORD=kitlab2026
LOGIN_RATE_LIMIT_ENABLED=true
APP_URL=https://crm-frontend.up.railway.app
```

5. **Generate Domain** (Settings → Networking) → запомнить URL backend.

## Шаг 3 — Frontend

1. Ещё **+ New → GitHub Repo** → тот же `kesaryuga/crm`
2. **Root Directory** = `frontend`
3. Variables:

```
API_URL=https://ОТ_BACKEND.up.railway.app
NEXT_PUBLIC_API_URL=https://ОТ_BACKEND.up.railway.app
```

4. **Generate Domain** → URL frontend.

5. Вернуться в backend и обновить `APP_URL` = URL frontend.

## Шаг 4 — Проверка

- `https://backend.../health/ready` → `database: ok`
- `https://frontend.../login` → `admin@kit-lab.by` / `kitlab2026`
- boss@kit-lab.by / boss2026

## Если ошибка railway.json

Симптом: `invalid character ... failed to parse railway.json`  
Причина: сломанный/загруженный вручную файл. В репо уже лежит валидный `backend/railway.json` и `frontend/railway.json`.  
Не загружайте файлы руками — деплой только из GitHub.

## Keep-alive

После получения URL положите секреты в GitHub:
`BACKEND_URL`, `FRONTEND_URL` (workflow `keep-alive.yml`).
