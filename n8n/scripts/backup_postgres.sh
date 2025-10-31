#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/n8n_postgres_backup_$TIMESTAMP.sql.gz"
LOG_FILE="$BACKUP_DIR/backup.log"


POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-n8n}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-n8n_password}"
POSTGRES_DB="${POSTGRES_DB:-n8n_db}"

mkdir -p "$BACKUP_DIR"
touch "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Starting PostgreSQL backup..." | tee -a "$LOG_FILE"

export PGPASSWORD="$POSTGRES_PASSWORD"

if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Backup created successfully: $BACKUP_FILE" | tee -a "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Backup failed!" | tee -a "$LOG_FILE"
    exit 1
fi

find "$BACKUP_DIR" -name "n8n_postgres_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -exec rm -f {} \;
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧹 Old backups older than $RETENTION_DAYS days removed." | tee -a "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎉 Backup process completed successfully!" | tee -a "$LOG_FILE"
