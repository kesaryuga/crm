#!/usr/bin/env bash
set -euo pipefail

# Backup: PostgreSQL dump + uploaded files + manifest.
# Usage: bash scripts/backup.sh [output_dir]

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${1:-$ROOT/backups/$STAMP}"
mkdir -p "$OUT"

if [[ -n "${DATABASE_URL:-}" ]]; then
  PG_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql://}"
  echo "==> pg_dump -> $OUT/db.dump"
  pg_dump --format=custom --no-owner --no-privileges -f "$OUT/db.dump" "$PG_URL"
else
  echo "==> DATABASE_URL не задан — пропускаю pg_dump"
fi

UPLOADS="${STORAGE_LOCAL_PATH:-$ROOT/data/uploads}"
if [[ -d "$UPLOADS" ]]; then
  echo "==> files -> $OUT/uploads.tar.gz"
  tar -czf "$OUT/uploads.tar.gz" -C "$UPLOADS" .
else
  echo "==> no uploads dir at $UPLOADS, skip"
fi

cat > "$OUT/manifest.json" <<EOF
{
  "created_at": "$STAMP",
  "app": "crm",
  "app_version": "0.2.0",
  "retention_hint": "7 daily / 4 weekly / 3 monthly",
  "includes": ["db.dump", "uploads.tar.gz"]
}
EOF

echo "OK: backup at $OUT"
