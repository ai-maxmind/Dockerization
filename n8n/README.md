# 🚀 n8n Dockerized
## 🧩 Thành phần chính

| Service | Mô tả | Cổng | Ghi chú |
|----------|-------|------|---------|
| **Traefik v2.10** | Reverse proxy + HTTPS + Dashboard bảo mật | 80, 443 | Auto SSL (Let's Encrypt) |
| **n8n (Custom Build)** | Workflow Automation Engine | 5678 | Tối ưu build size & node_modules |
| **PostgreSQL 15** | Cơ sở dữ liệu chính | 5432 | Dữ liệu lưu ở volume `pgdata` |
| **Redis 7** | Queue/BullMQ | 6379 | Lưu queue tạm thời |
## ⚡ Cài đặt & Khởi chạy

### Clone repo
```bash
git clone https://github.com/ai-maxmind/Dockerization
cd n8n
```
### Tạo file .env
```
cp .env.example .env
```
### Tạo file ACME và cấp quyền
```
mkdir -p traefik/acme
touch traefik/acme/acme.json
chmod 600 traefik/acme/acme.json
```
### Tạo hash bảo vệ Dashboard Traefik
```
docker run --rm httpd:2.4 htpasswd -nbB admin "yourpassword"
```
Dán kết quả vào `.env`: `TRAEFIK_DASHBOARD_USER_HASH=admin:$2y$05$7pbkIbHNaS5efKJYzPmeHOGEwY4fczYk5W8Yqvh3l.J9ZoO2npD1W`
### Build và chạy toàn bộ stack
```
docker compose up -d --build
```
### Truy cập giao diện
| Service               | URL                                      | Mô tả                                 |
| --------------------- | ---------------------------------------- | ------------------------------------- |
| **n8n App**           | `https://automation.example.com`         | Giao diện chính n8n                   |
| **Traefik Dashboard** | `https://traefik.automation.example.com` | Giao diện quản trị, yêu cầu đăng nhập |
### Auto-Reload Traefik
Traefik được cấu hình theo dõi file `dynamic.yml`:
+ Khi chỉnh sửa middleware, router hoặc header → Traefik tự reload mà không cần restart container.
+ Xem log Traefik để xác minh: `docker compose logs -f traefik`
### Các biến môi trường chính (trong `.env`)
| Biến                                                | Mô tả                              |
| --------------------------------------------------- | ---------------------------------- |
| `N8N_HOST`                                          | Domain chính của n8n               |
| `WEBHOOK_URL`                                       | URL webhook gốc                    |
| `N8N_BASIC_AUTH_ACTIVE`                             | Bật/tắt bảo mật HTTP Basic cho n8n |
| `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`   | Thông tin đăng nhập n8n            |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Thông tin PostgreSQL               |
| `TRAEFIK_ACME_EMAIL`                                | Email đăng ký SSL Let's Encrypt    |
| `TRAEFIK_DASHBOARD_USER_HASH`                       | Hash user:pass cho dashboard       |
| `TZ`                                                | Múi giờ hệ thống                   |
### Câu lệnh hệ thống
| Mục tiêu                    | Lệnh                                                             |
| --------------------------- | ---------------------------------------------------------------- |
| Dừng toàn bộ stack          | `docker compose down`                                            |
| Xem log n8n                 | `docker compose logs -f n8n`                                     |
| Restart n8n                 | `docker compose restart n8n`                                     |
| Xem dashboard               | `https://traefik.${N8N_HOST}`                                    |
| Kiểm tra sức khỏe container | `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` |
