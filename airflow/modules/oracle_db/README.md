# OracleDB - Secure Python Oracle Database Wrapper

Module Python mạnh mẽ để tương tác với Oracle Database, tích hợp các tính năng bảo mật và hiệu suất cao.

## Tính năng chính

- 🔄 Quản lý connection pool tự động
- 🔁 Tự động kết nối lại với cơ chế exponential backoff
- ⚡ Tối ưu hóa session cho hiệu suất cao
- 🔒 Quản lý giao dịch (transaction) an toàn
- 📝 Quản lý checkpoint cho xử lý dữ liệu
- 🔍 Xử lý lỗi và ghi log chi tiết
- 🛡️ Bảo vệ khỏi SQL injection
- 📊 Hỗ trợ xử lý dữ liệu batch

## Yêu cầu cài đặt

```bash
pip install oracledb pandas
```

## Tính năng chi tiết

### Connection Pool
- Số kết nối tối thiểu: 2
- Số kết nối tối đa: 20
- Bước tăng: 2
- Timeout kết nối: 120 giây
- Chế độ pool: WAIT
- Ping interval: 60 giây

### Tối ưu hóa Session
- Parallel DML được bật
- Cursor sharing tối ưu
- Cấu hình workarea size
- Tối ưu sort và hash areas
- Cấu hình NLS parameters
- Bật result cache mode

### Xử lý lỗi
- Tự động thử lại với exponential backoff
- Ghi log chi tiết
- Kiểm tra sức khỏe kết nối
- Khả năng reset pool

## Cách sử dụng
### 1. Khởi tạo và kết nối

```python
# Cấu hình kết nối
connection_config = {
    "username": "your_username",
    "password": "your_password",
    "host": "your_host",
    "port": 1521,      # Port mặc định của Oracle
    "service_name": "your_service_name"
}

# Khởi tạo với cấu hình nâng cao
db = OracleDB(
    connectConfig=connection_config,
    maxRetries=3,      # Số lần thử kết nối lại tối đa
    retryDelay=3       # Thời gian chờ giữa các lần thử (giây)
)

# Kết nối đến database
if db.connectDB():
    print("✅ Kết nối thành công")
```

### 2. Sử dụng Context Manager (Recommended)

```python
# Context manager đảm bảo kết nối được đóng đúng cách
with OracleDB(connection_config) as db:
    if db.connectDB():
        # Thực hiện các thao tác với database
        pass
    # Kết nối sẽ tự động được đóng khi thoát khỏi block with
```

### 3. Quản lý Transaction

```python
with OracleDB(connection_config) as db:
    if db.connectDB():
        try:
            # Thực hiện các thao tác database
            db.conn.commit()  # Commit transaction
        except Exception as e:
            db.rollbackConnection()  # Rollback nếu có lỗi
            logging.error(f"Lỗi: {e}")
```

### 4. Quản lý Checkpoint

```python
# Lưu tiến trình xử lý
db.saveCheckpoint(offset=1000)

# Đọc checkpoint cuối cùng
last_offset = db.loadCheckpoint()

# Xóa checkpoint nếu cần
db.clearCheckpoint()
```

### 5. Thao tác với dữ liệu

#### a. Thêm dữ liệu (INSERT)
```python
# Thêm nhiều bản ghi cùng lúc
data = [
    {"ID": 1, "NAME": "Alice", "AGE": 25},
    {"ID": 2, "NAME": "Bob", "AGE": 30}
]

# Cách 1: Sử dụng helper method
db.insertData("USERS", ["ID", "NAME", "AGE"], data)

# Cách 2: Sử dụng SQL trực tiếp với binding parameters
sql = "INSERT INTO USERS (ID, NAME, AGE) VALUES (:1, :2, :3)"
values = [(row["ID"], row["NAME"], row["AGE"]) for row in data]
with db.conn.cursor() as cursor:
    cursor.executemany(sql, values)
db.conn.commit()
```

#### b. Cập nhật dữ liệu (UPDATE)
```python
# Cập nhật với điều kiện
updateValues = {"NAME": "Charlie", "AGE": 28}
db.updateData("USERS", updateValues, "ID = 1")

# Cập nhật với nhiều điều kiện
conditions = "AGE > 25 AND DEPARTMENT = 'IT'"
db.updateData("USERS", {"STATUS": "ACTIVE"}, conditions)
```

#### c. Xóa dữ liệu (DELETE)
```python
# Xóa với điều kiện cụ thể
db.deleteData("USERS", "AGE > 50")

# Lưu ý: Module tự động chặn DELETE không có WHERE để bảo vệ dữ liệu
```

### 6. Bảo mật và SQL Injection

Module tự động bảo vệ khỏi SQL injection bằng cách sử dụng parameter binding:

```python
# An toàn - Sử dụng parameter binding
userInput = "1 OR 1=1"  # Input độc hại
sql = "DELETE FROM USERS WHERE ID = :1"
cursor.execute(sql, [userInput])  # userInput được xử lý an toàn

# Giải thích:
# - :1 là placeholder
# - Oracle xử lý userInput như dữ liệu thuần túy
# - Ngăn chặn các tấn công như "' OR '1'='1" hoặc "'; DROP TABLE USERS; --"
```

### 7. Xử lý lỗi và logging

```python
try:
    with OracleDB(connection_config) as db:
        if db.connectDB():
            # Kiểm tra sức khỏe kết nối
            db.verifyConnection()
            
            # Reset pool nếu cần
            if connection_issues:
                db.resetPool()
                
except Exception as e:
    logging.error(f"Database error: {e}")
```
### 8. Làm việc với Stored Procedures

Module hỗ trợ đầy đủ các loại stored procedure trong Oracle:

#### a. Stored Procedure cơ bản (với tham số OUT)

```sql
-- Định nghĩa trong Oracle
CREATE OR REPLACE PROCEDURE GET_USER_INFO (
    P_USER_ID IN NUMBER,
    P_NAME OUT VARCHAR2,
    P_EMAIL OUT VARCHAR2
) AS
BEGIN
    SELECT USERNAME, EMAIL
    INTO P_NAME, P_EMAIL
    FROM USERS
    WHERE USER_ID = P_USER_ID;
END;
```

```python
# Gọi trong Python
with OracleDB(connection_config) as db:
    if db.connectDB():
        # Định nghĩa tham số với kiểu IN/OUT
        params = [
            ("P_USER_ID", "IN", 101),
            ("P_NAME", "OUT", None),
            ("P_EMAIL", "OUT", None)
        ]
        result = db.runProcedure("GET_USER_INFO", params)
        print(result)  # In kết quả trả về
```

#### b. Stored Procedure với REF CURSOR

```sql
-- Định nghĩa trong Oracle
CREATE OR REPLACE PROCEDURE GET_USERS_BY_ROLE (
    P_ROLE_ID IN NUMBER,
    P_RESULT OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN P_RESULT FOR
        SELECT USER_ID, USERNAME, EMAIL
        FROM USERS
        WHERE ROLE_ID = P_ROLE_ID;
END;
```

```python
# Gọi trong Python
with OracleDB(connection_config) as db:
    if db.connectDB():
        # Đơn giản hóa với helper method
        rows = db.runProcedureWithCursor("GET_USERS_BY_ROLE", [2])
        
        # Kết quả trả về dưới dạng list of dictionaries
        for row in rows:
            print(f"User ID: {row['USER_ID']}, Name: {row['USERNAME']}")
```

#### c. Package Procedures

```sql
-- Định nghĩa Package trong Oracle
CREATE OR REPLACE PACKAGE PKG_USER AS
    PROCEDURE GET_USER_BY_ID (P_ID IN NUMBER, P_NAME OUT VARCHAR2);
    PROCEDURE LIST_USERS (P_ROLE_ID IN NUMBER, P_RESULT OUT SYS_REFCURSOR);
END PKG_USER;
```

```python
# Gọi Procedure từ Package
with OracleDB(connection_config) as db:
    if db.connectDB():
        # Gọi procedure với tham số OUT
        user_info = db.runProcedure(
            "PKG_USER.GET_USER_BY_ID",
            [("P_ID", "IN", 101), ("P_NAME", "OUT", None)]
        )
        print(f"User name: {user_info['P_NAME']}")

        # Gọi procedure với REF CURSOR
        users = db.runProcedureWithCursor("PKG_USER.LIST_USERS", [2])
        for user in users:
            print(user)  # In thông tin từng user
```

### 9. Best Practices

1. **Sử dụng Context Manager**
   ```python
   with OracleDB(config) as db:
       if db.connectDB():
           # Code here
   ```

2. **Xử lý Transaction đúng cách**
   ```python
   try:
       # Thực hiện các thao tác
       db.conn.commit()
   except:
       db.rollbackConnection()
   ```

3. **Kiểm tra sức khỏe kết nối**
   ```python
   db.verifyConnection()
   ```

4. **Sử dụng parameter binding**
   ```python
   cursor.execute("SELECT * FROM USERS WHERE ID = :1", [user_id])
   ```

5. **Ghi log đầy đủ**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

### 10. Troubleshooting

1. **Kết nối thất bại**
   - Kiểm tra thông tin kết nối
   - Xác nhận service_name đúng
   - Kiểm tra firewall

2. **Vấn đề hiệu suất**
   - Sử dụng connection pooling
   - Kiểm tra các thiết lập session
   - Tối ưu các câu query

3. **Lỗi transaction**
   - Đảm bảo commit/rollback đúng cách
   - Kiểm tra autocommit setting
   - Xử lý deadlock