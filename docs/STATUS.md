# CRM запущена — статус на утро

**Готово:** CRM работает, вход есть, keep-alive крутится.

## Ссылки

| Что | URL |
|-----|-----|
| **CRM (открывать это)** | https://crm-frontend-h3zf.onrender.com/login |
| API / Swagger | https://crm-backend-myq6.onrender.com/docs |
| Health | https://crm-frontend-h3zf.onrender.com/health/ready |

## Вход

- Email: `admin@kit-lab.by`
- Пароль: `2W1X7eAWOQovF0U7D_U-q3Cg`

(смените, когда будете работать с реальными данными)

## Что крутится (бесплатно)

| Сервис | Где | Заметки |
|--------|-----|---------|
| Frontend + API | Render Free | засыпает без запросов, keep-alive будит |
| PostgreSQL | Supabase Free | проект `crm` / org `kit-lab` |
| Keep-alive | GitHub Actions | каждые 10 мин `/health/ready` |

**Ссылка на GitHub:** https://github.com/kesaryuga/crm

## Если «вдруг тухнет»

1. Откройте https://crm-frontend-h3zf.onrender.com/login и обновите — Render поднимется ~1 мин.
2. Проверьте Actions: https://github.com/kesaryuga/crm/actions/workflows/keep-alive.yml
3. Supabase — раз в 2–3 недели заходите в дашборд (иначе free project может «уснуть»).

## Следующий шаг (не срочно)

- Подключить шаблоны договоров/протоколов (Word)
- Сменить пароль админа
- Бэкапы: `scripts/backup.sh` (см. `docs/deploy-free.md`)
- Когда надоест free-лимиты — VPS по `docs/runbook-vps.md`
