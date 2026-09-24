#!/usr/bin/env bash
set -euo pipefail

# Verify restore into empty environment: counts + sample file hashes.
# Backup без restore-теста не считается надёжным.
# Usage: bash scripts/verify_restore.sh [backup_dir]

SRC="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

if [[ -n "${DATABASE_URL:-}" ]]; then
  PG_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql://}"
  echo "==> DB connectivity"
  psql "$PG_URL" -v ON_ERROR_STOP=1 -c "SELECT 1" >/dev/null
  echo "==> table counts"
  for t in counterparties contracts protocols files users; do
    count=$(psql "$PG_URL" -tAc "SELECT count(*) FROM $t" 2>/dev/null || echo "n/a")
    echo "  $t: $count"
  done
else
  echo "==> DATABASE_URL не задан — только проверка файлов"
fi

UPLOADS="${STORAGE_LOCAL_PATH:-$ROOT/data/uploads}"
if [[ -d "$UPLOADS" ]]; then
  echo "==> sample file hashes"
  find "$UPLOADS" -type f | head -n 5 | while read -r f; do
    sha256sum "$f" 2>/dev/null || shasum -a 256 "$f"
  done
fi

if [[ -n "$SRC" && -f "$SRC/manifest.json" ]]; then
  echo "==> manifest"
  cat "$SRC/manifest.json"
fi

if [[ -n "$SRC" && ! -f "$SRC/db.dump" && ! -f "$SRC/uploads.tar.gz" ]]; then
  echo "ERROR: backup пустой" >&2
  FAIL=1
fi

if [[ $FAIL -ne 0 ]]; then
  echo "FAIL: verify" >&2
  exit 1
fi
echo "OK: verify finished"
