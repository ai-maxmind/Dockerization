# SQL Server
+ Khởi động SQL Server trong Docker: 
  + Tạo 3 thư mục **data, log, secrets** trên máy tính để ánh xạ dữ liệu của SQL Server trong Docker ra PC 
  + `docker-compose up`

  ![](./images/docker-compose-mssql.png)

+ Kết nối MSSQL trong Docker với Visual Studio Code
  + Cài đặt extension SQL Server trong VS Code

  ![](./images/ms-sql-server-extension.png)

  + Kết nối đến SQL Server container với Visual Studio Code
    + Tạo kết nối với tên server: `localhost,1433` hoặc `127.0.0.1,1433`

    ![](./images/server-name.png)

    + Nhập tên cơ sở dữ liệu hoặc nhấn **Enter** để tiếp tục

    ![](./images/database-name.png)

    + Chọn SQL Login với tên đăng nhập user sa, password
    + Nhập tên hiển thị trên kết nối Docker

    ![](./images/profile-name.png)

    + Kiểm tra phiên bản SQL Server:

    ![](./images/sql-server-version.png)
    





