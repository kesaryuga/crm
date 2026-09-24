# Пошагово: бесплатное размещение CRM (тест)

Актуально на **сентябрь 2026**. Перед запуском сверьте тарифы — они меняются.

## Вариант A (рекомендуется без карты): Render Free + Supabase Free

Подходит, чтобы потестировать API и интерфейс 1–4 недели.

| Слуга | Платформа | Лимиты |
|-------|-----------|--------|
| PostgreSQL | Supabase Free | 500 МБ, **пауза после 1 недели бездействия**, макс. 2 проекта |
| Backend | Render Free web | 512 МБ RAM, засыпает через 15 мин простоя, 750 instance-hours/мес на workspace |
| Frontend | Render Free web | как backend |
| Файлы | local `/data/uploads` | **не переживают** redeploy/spin-down на Free |

**Не используйте Render Free Postgres** — он удаляется через 30 дней. Только внешний Supabase/Neon.

## Вариант B: Railway Free Trial + Supabase Free

Если нужны volume для файлов на 30 дней.

| Слуга | Платформа | Лимиты |
|-------|-----------|--------|
| PostgreSQL | Supabase Free | см. выше |
| Backend + Frontend | Railway Free Trial | $5 one-time credit на 30 дней, **без карты** |
| Volume `/data/uploads` | Railway | до 500 МБ |

После Trial: платный Hobby ($5/мес) или перенос на VPS (`docs/runbook-vps.md`).

**План Free Railway ($1/мес credit) не держит сервисы 24/7** — RAM ~$10/GB/мес.

---

## Шаг 1 — База данных (Supabase, 5 минут)

1. https://supabase.com → **New project** (регион ближе к вам, напр. `eu-central-1`).
2. Придумайте пароль базы (запишите).
3. **Project Settings → Database → Connection string**
4. Возьмите **Session pooler** (не Transaction pooler) — SQLAlchemy + транзакции.
5. Замените `postgres://` на `postgresql+psycopg://`
6. Добавьте `?sslmode=require`, если его нет.
7. Это значение — `DATABASE_URL`.

Пример:

```text
postgresql+psycopg://postgres:ПАРОЛЬ@aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require
```

Раз в неделю заходите в Supabase или шлите любой SQL — иначе free project **засыпает**.

---

## Шаг 2 — Секреты (один раз)

Сгенерируйте и **не коммитьте**:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(18))"
```

| Переменная | Значение |
|------------|----------|
| `APP_ENV` | `staging` (включает `/docs` для тестов) |
| `APP_NAME` | `CRM` |
| `TIMEZONE` | `Europe/Minsk` |
| `DATABASE_URL` | из шага 1 |
| `SECRET_KEY` | случайный (первый `token_urlsafe`) |
| `ADMIN_EMAIL` | `admin@kit-lab.by` |
| `ADMIN_PASSWORD` | новый пароль (не `ChangeMe!2026`) |
| `STORAGE_BACKEND` | `local` |
| `STORAGE_LOCAL_PATH` | `/data/uploads` |
| `LOGIN_RATE_LIMIT_ENABLED` | `true` |
| `LOG_LEVEL` | `INFO` |

Черновик с секретами (только локально): `.env.deploy.local` — уже в `.gitignore`.

---

## Шаг 3A — Render (вариант A)

1. https://dashboard.render.com → **New → Blueprint** → репозиторий `kesaryuga/crm`
2. Blueprint подхватит `render.yaml` (два web service: `crm-backend`, `crm-frontend`).
3. Заполните секретные env (`DATABASE_URL`, `SECRET_KEY`, `ADMIN_*`) — они помечены `sync: false`.
4. У `crm-frontend` проверьте `API_URL` / `NEXT_PUBLIC_API_URL` = публичный host backend (`crm-backend.onrender.com` или как в дашборде). Frontend проксирует `/api` и `/health` на backend (same-origin cookies).
5. Дождитесь деплоя, затем:
   - `https://crm-backend.onrender.com/health/live` → `{"status":"ok"}`
   - `https://crm-backend.onrender.com/docs` (при `APP_ENV=staging`)
   - `https://crm-frontend.onrender.com/login` — вход `ADMIN_EMAIL` / `ADMIN_PASSWORD`

## Шаг 3B — Railway (вариант B)

1. https://railway.app → **New Project → Deploy from GitHub repo** → `kesaryuga/crm`
2. **Root Directory** = `backend` (использует `backend/Dockerfile` + `backend/railway.json`)
3. Variables — таблица из шага 2 + `APP_URL` = будущий URL frontend
4. **Volume**: mount path `/data/uploads`
5. Ещё один сервис из того же repo, **Root Directory** = `frontend`
6. У frontend: `API_URL` и `NEXT_PUBLIC_API_URL` = публичный URL backend (`https://...up.railway.app`)
7. Проверки те же: `/health/live`, `/login`

---

## Шаг 4 — Резервные копии (обязательно)

На бесплатных дисках данные **могут исчезнуть**. Дамп и файлы выгружайте наружу:

```bash
# раз в день
bash scripts/backup.sh /backups/$(date +%Y%m%d)
# раз в месяц — проверка восстановления
bash scripts/restore.sh /backups/последний
bash scripts/verify_restore.sh /backups/последний
```

**Backup без проверки restore — не backup.**

Retention: 7 daily · 4 weekly · 3 monthly.

---

## Проверка после запуска

1. `/health/live` → ok  
2. `/health/ready` → ok (БД)  
3. `/docs` → OpenAPI (staging)  
4. `/login` → вход админом, `/dashboard` показывает роль `admin`  
5. Создать контрагента через API/docs  
6. `backup.sh` + `restore.sh` + `verify_restore.sh`

---

## Важно / ограничения

- Бесплатный хостинг — **временный слой**. Рабочие договоры/протоколы — только с внешним backup.
- Файлы на Render Free **не персистентны**. Для тестов с загрузкой файлов — вариант B (volume) или S3-compatible.
- Supabase Free: пауза после 1 недели без запросов, нет automatic backups.
- `APP_ENV=production` отключает `/docs` и ставит `Secure` на cookie — так и надо на бою.
- Перенос на VPS: `docs/runbook-vps.md`.
