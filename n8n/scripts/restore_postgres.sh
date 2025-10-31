#!/bin/bash
BACKUP_DIR="${BACKUP_DIR:-/backups}"
CONTAINER_NAME="${CONTAINER_NAME:-n8n_postgres}"
POSTGRES_DB="${POSTGRES_DB:-n8n_db}"
POSTGRES_USER="${POSTGRES_USER:-n8n_user}"

echo "🔍 Đang tìm bản backup mới nhất trong: $BACKUP_DIR"
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
  echo "❌ Không tìm thấy file backup nào trong $BACKUP_DIR!"
  exit 1
fi

echo "✅ Phát hiện file backup mới nhất: $LATEST_BACKUP"
echo "⚙️  Bắt đầu khôi phục vào database: $POSTGRES_DB ..."

gunzip -c "$LATEST_BACKUP" | docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

if [ $? -eq 0 ]; then
  echo "🎉 Khôi phục thành công từ bản backup: $(basename "$LATEST_BACKUP")"
else
  echo "❌ Khôi phục thất bại. Kiểm tra lại log hoặc quyền truy cập."
  exit 1
fi

echo "🕒 Thời gian hoàn tất: $(date '+%Y-%m-%d %H:%M:%S')"
