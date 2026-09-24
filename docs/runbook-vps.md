# Перенос на VPS

1. Linux VPS + Docker + Docker Compose.
2. Скопировать репозиторий / release.
3. `cp .env.example .env` и заполнить секреты (не в git).
4. `docker compose up -d --build`.
5. `alembic upgrade head` (в backend-контейнере).
6. Восстановить backup: `bash scripts/restore.sh <backup_dir>`.
7. `bash scripts/verify_restore.sh <backup_dir>`.
8. `/health/live`, `/health/ready`.
9. Сверить количество контрагентов/договоров/протоколов/файлов.
10. Переключить DNS, HTTPS (reverse proxy).

Retention backup: 7 daily · 4 weekly · 3 monthly. Backup без restore-теста не считается надёжным.
