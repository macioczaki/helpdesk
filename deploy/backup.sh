#!/usr/bin/env bash
set -e

BACKUP_DIR="${BACKUP_DIR:-/var/backups/helpdesk}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="$BACKUP_DIR/helpdesk-$STAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "==> Backup do $FILE"
docker compose -f "$(dirname "$0")/../docker-compose.prod.yml" exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"

echo "==> Usuwanie starszych niż $KEEP_DAYS dni"
find "$BACKUP_DIR" -name "helpdesk-*.sql.gz" -mtime +$KEEP_DAYS -delete

echo "==> Gotowe. Plik: $FILE"