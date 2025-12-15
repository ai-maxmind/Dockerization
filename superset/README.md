## 1. Mục đích
Triển khai Superset, Keycloak (SSO), PostgreSQL, Redis bằng Docker. Hỗ trợ phân quyền dữ liệu theo phòng ban, cột, dòng. 

## 2. Cần chuẩn bị gì?
- Máy đã cài Docker và Docker Compose
- (Nếu muốn phát triển thêm) Cài Python 3.10+ và pip

---

## 3. Cài đặt nhanh (3 bước)
**Bước 1:** Copy file `.env.example` thành `.env` rồi sửa lại mật khẩu, thông tin cho phù hợp.

**Bước 2:** Mở terminal, chạy:
```powershell
docker-compose up -d
```
Lệnh này sẽ tự động dựng Superset, Keycloak, PostgreSQL, Redis.

**Bước 3:** Truy cập:
- Superset: http://localhost:8088/
- Keycloak: http://localhost:8080/ (user: admin, pass: admin)

---


## 4. Cấu hình môi trường 
### File `.env` (biến môi trường)
Tất cả biến cấu hình chính nằm trong file `.env`. Xem mẫu trong `.env.example`. Ví dụ:
```env
POSTGRES_DB=superset         # Tên database Superset sẽ dùng
POSTGRES_USER=superset       # User để kết nối database
POSTGRES_PASSWORD=your_password  # Mật khẩu database
SUPERSET_SECRET_KEY=your_secret  # Chuỗi bí mật bảo mật cho Superset
ADMIN_USERNAME=admin         # Tài khoản admin Superset (tạo tự động)
ADMIN_PASSWORD=admin         # Mật khẩu admin
... (xem thêm trong file)
```

### File `superset/scripts/seed_company.py` 
**Mục đích:**
- Tự động tạo sẵn các quyền (role) phòng ban như `Dept_Finance`, `Dept_Sales`, `Dept_HR`, `Dept_Engineering` và các role phụ như `Viewer`, `Analyst` trong Superset.
- Giúp phân quyền dữ liệu/dashboards nhanh, không cần tạo role thủ công từng cái.

**Cách dùng:**
1. Mở terminal, chạy lệnh này để thực thi script bên trong container Superset:
	```powershell
	docker-compose exec superset python /app/pythonpath/scripts/seed_company.py
	```
2. Script sẽ tự kiểm tra, tạo role nếu chưa có, không xóa role cũ.
3. Sau khi chạy xong, script sẽ in ra:
	- Danh sách role đã tạo.
	- Hướng dẫn tạo phân quyền dòng (RLS) và cột (CLS) qua giao diện hoặc API.

### File `superset/superset_config.py` 
File này giúp Superset biết cách kết nối tới database, Redis, cache, và Celery. Giải thích:

- `SECRET_KEY`: Lấy từ biến môi trường, dùng để bảo mật session Superset.
- `SQLALCHEMY_DATABASE_URI`: Đường dẫn kết nối tới PostgreSQL, lấy thông tin từ `.env`.
- `REDIS_HOST`, `REDIS_PORT`: Địa chỉ và port của Redis (dùng cho cache và Celery).
- `CACHE_CONFIG`:
	- `CACHE_TYPE`: Loại cache, ở đây là Redis.
	- `CACHE_DEFAULT_TIMEOUT`: Thời gian cache mặc định (giây).
	- `CACHE_KEY_PREFIX`: Tiền tố cho mọi key cache (giúp phân biệt cache của Superset với app khác, ví dụ: `superset_`).
	- `CACHE_REDIS_HOST`, `CACHE_REDIS_PORT`: Kết nối tới Redis.
- `CELERY_CONFIG`:
	- `broker_url`: Địa chỉ Redis dùng để truyền task cho worker (Celery).
	- `result_backend`: Địa chỉ Redis lưu kết quả task.

- Nếu bạn đổi tên project, có thể đổi `CACHE_KEY_PREFIX` để tránh trùng cache với app khác.
- Nếu đổi port/host Redis hay DB, chỉ cần sửa `.env`, không cần sửa code.


---

## 5. Đăng nhập và quản trị Superset
- Đăng nhập Superset bằng tài khoản admin (tạo tự động từ biến môi trường).
- Muốn đổi cấu hình? Sửa file `superset/superset_config.py` rồi chạy:
```powershell
docker-compose restart superset
```
- Nếu Superset báo lỗi DB, chạy:
```powershell
docker-compose exec superset superset db upgrade
docker-compose exec superset superset init
```

---

## 6. Đăng nhập SSO với Keycloak (đăng nhập 1 lần cho tất cả)
1. Vào http://localhost:8080/ (user: admin, pass: admin)
2. Tạo Realm (ví dụ: `company8-realm`), Client (`superset-client`, OIDC), lấy `client_secret`.
3. Sửa file `superset/superset_config.py` (phần OIDC) cho đúng URL Keycloak: dùng `http://localhost:8080/realms/company8-realm/protocol/openid-connect/...`
4. Tạo user, gán role/groups/department nếu muốn phân quyền tự động.
5. Đăng nhập Superset bằng nút SSO.

---

## 7. Phân quyền dữ liệu (Data Security) siêu dễ
- **Theo phòng ban:** Tạo role kiểu `Dept_Sales`, `Dept_Finance`... rồi gán quyền cho từng role.
- **Theo dòng (RLS):** Vào menu Security → Row Level Security → Add. Filter ví dụ: `department = '{{ current_user.department }}'`
- **Theo cột (CLS):** Vào Security → List Column Level Security → Add. Chọn cột muốn ẩn/hiện theo role.
- **Tự động gán role:**
	- Chỉ cần dùng file mẫu `superset/superset_config.company.py` (đã có sẵn trong repo).
	- Khi user đăng nhập qua SSO, Superset sẽ tự động gán role dựa vào thông tin phòng ban, nhóm, mã nhân viên... lấy từ Keycloak/LDAP.
	- Ví dụ đoạn code trong file mẫu:
		```python
		class Company8SecurityManager(SupersetSecurityManager):
				def oauth_user_info(self, user_info):
						department = user_info.get('department')
						if department:
								role_name = f"Dept_{department}"
								# ...tự động gán role này cho user...
		CUSTOM_SECURITY_MANAGER = Company8SecurityManager
		```
	- Nghĩa là: bạn chỉ cần tạo đúng role (ví dụ Dept_Sales), user đăng nhập sẽ tự được gán quyền đúng phòng ban, không cần thao tác tay.
