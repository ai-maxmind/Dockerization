# Label Studio


+ Cài đặt Label Studio trong docker: 
   + Tạo 2 thư mục: data và postgresql_data
   + Chạy câu lệnh `docker-compose up`
+  Truy cập Label Studio trên localhost: 127.0.0.1: 8088
+ Truy cập cơ sở dữ liệu PostgreSQL trong Docker:
  ```
  docker exec -it <containerID> bash
  su - postgre_user_name
  psql
  ```
