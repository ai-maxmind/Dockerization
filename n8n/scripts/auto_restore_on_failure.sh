#!/bin/bash
# ============================================================
# 🧠 PostgreSQL Auto Restore on Failure
# Phiên bản: 1.0 (Hau Nguyen)
# ------------------------------------------------------------
# Kiểm tra container PostgreSQL định kỳ.
# Nếu container bị lỗi hoặc database không phản hồi, tự động
# khôi phục bản backup mới nhất bằng restore_postgres.sh.
# ============================================================

CONTAINER_NAME="${CONTAINER_NAME:-n8n_postgres}"
POSTGRES_USER="${POSTGRES_USER:-n8n_user}"
POSTGRES_DB="${POSTGRES_DB:-n8n_db}"
CHECK_INTERVAL="${CHECK_INTERVAL:-300}"   
BACKUP_DIR="${BACKUP_DIR:-/backups}"
LOG_FILE="${LOG_FILE:-/var/log/auto_restore.log}"


log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Bắt đầu giám sát container PostgreSQL: $CONTAINER_NAME"
log "🕒 Tần suất kiểm tra: $CHECK_INTERVAL giây"


while true; do

  if ! docker ps --filter "name=^${CONTAINER_NAME}$" --filter "status=running" | grep -q "$CONTAINER_NAME"; then
    log "❌ Container PostgreSQL ($CONTAINER_NAME) không chạy! Bắt đầu khôi phục..."
    ./restore_postgres.sh
    log "✅ Đã chạy xong quá trình khôi phục. Sẽ kiểm tra lại sau ${CHECK_INTERVAL}s."
  else

    docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      log "⚠️ Database không phản hồi. Tiến hành khôi phục..."
      ./restore_postgres.sh
      log "✅ Khôi phục hoàn tất. Sẽ kiểm tra lại sau ${CHECK_INTERVAL}s."
    else
      log "✅ PostgreSQL hoạt động bình thường."
    fi
  fi

  sleep "$CHECK_INTERVAL"
done
