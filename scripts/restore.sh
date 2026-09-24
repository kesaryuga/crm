#!/usr/bin/env bash
set -euo pipefail

# Restore PostgreSQL dump and files from a backup directory.
# Usage: bash scripts/restore.sh <backup_dir>

SRC="${1:?usage: restore.sh <backup_dir>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$SRC/db.dump" ]]; then
  echo "WARN: $SRC/db.dump not found — пропускаю восстановление БД" >&2
else
  if [[ -n "${DATABASE_URL:-}" ]]; then
    PG_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql://}"
    echo "==> restore database from $SRC/db.dump"
    pg_restore --clean --if-exists --no-owner --no-privileges -d "$PG_URL" "$SRC/db.dump"
  else
    echo "ERROR: DATABASE_URL не задан" >&2
    exit 1
  fi
fi

UPLOADS="${STORAGE_LOCAL_PATH:-$ROOT/data/uploads}"
if [[ -f "$SRC/uploads.tar.gz" ]]; then
  echo "==> restore files to $UPLOADS"
  mkdir -p "$UPLOADS"
  tar -xzf "$SRC/uploads.tar.gz" -C "$UPLOADS"
fi

echo "OK: restore finished. Run scripts/verify_restore.sh $SRC"
