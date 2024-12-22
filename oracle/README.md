# Oracle Master-Slave
Truy cập trang [Oracle Container Registry](https://container-registry.oracle.com) và tạo tài khoản. Để tải xuống image, sẽ cần đăng nhập Docker vào Oracle Container Registry: `docker login container-registry.oracle.com`

![docker login container-registry.oracle.com](./images/docker%20login.png)

Sau đó, Chấp nhận các điều khoản của Oracle: 
![Oracle Standard Terms and Restrictions](./images/Oracle%20Standard%20Terms%20and%20Restrictions.png)
## Cấu hình Oracle Master-Slave Replication
+ Khởi động Docker Compose: `docker-compose up -d`

![Docker Compose](./images/docker%20compose.png)

+ Cấu hình Oracle Data Guard và SQL*Plus với quyền SYSDBA:
    + Kết nối vào container Oracle Master:
        
        ```sh
        docker exec -it oracle-master bash
        sqlplus sys/yourpassword@localhost:1521/ORCL as sysdba
        ```
    + Chạy lệnh sau trong SQL*Plus để bật tính năng Data Guard:
    ```
    ALTER SYSTEM SET DG_BROKER_START=TRUE SCOPE=BOTH;
    SHOW PARAMETER DG_BROKER_START;
    ```
    + Tạo dịch vụ cho Data Guard Broker: 
    ```
    ALTER SYSTEM SET DB_CREATE_FILE_DEST='/OPT/ORACLE/ORADATA' SCOPE=BOTH;
    ```

    + Cấu hình cho Database ảo (Logical Standby):
    ```
    ALTER SYSTEM SET LOG_ARCHIVE_CONFIG='DG_CONFIG=(ORCL,ORCLSTANDBY)' SCOPE=BOTH;
    ALTER SYSTEM SET LOG_ARCHIVE_DEST_1='LOCATION=/OPT/ORACLE/ORADATA' SCOPE=BOTH;
    ALTER SYSTEM SET LOG_ARCHIVE_DEST_2='SERVICE=ORCLSTANDBY' SCOPE=BOTH;
    ```
    + Bật chế độ Archive:
    ```
    ALTER SYSTEM SET LOG_ARCHIVE_FORMAT='LOG%T_%S.ARC' SCOPE=BOTH;
    ```
    + Bật tính năng Data Guard Broker:
    ```
    ALTER SYSTEM SET LOG_ARCHIVE_DEST_STATE_1=ENABLE;
    ALTER SYSTEM SET LOG_ARCHIVE_DEST_STATE_2=ENABLE;
    ```

    + Cấu hình Slave (Standby) với Oracle Data Guard:
        + Kết nối vào container của một slave:
            ```sh
            docker exec -it oracle-slave-1 bash
            sqlplus sys/yourpassword@localhost:1521/ORCL as sysdba
            ```
        + Đặt chế độ Standby cho Slave:
        ```
        ALTER SYSTEM SET DB_CREATE_FILE_DEST='/OPT/ORACLE/ORADATA' SCOPE=BOTH;
        ALTER SYSTEM SET DB_NAME='ORCL' SCOPE=BOTH;
        ALTER SYSTEM SET LOG_ARCHIVE_DEST_1='LOCATION=/OPT/ORACLE/ORADATA' SCOPE=BOTH;
        ALTER SYSTEM SET LOG_ARCHIVE_DEST_2='SERVICE=ORCL' SCOPE=BOTH;
        ALTER SYSTEM SET LOG_ARCHIVE_FORMAT='LOG%T_%S.ARC' SCOPE=BOTH;
        ```
        + Thiết lập chế độ Standby cho Slave:
        ```
        ALTER DATABASE RECOVER MANAGED STANDBY DATABASE USING CURRENT LOGFILE DISCONNECT FROM SESSION;
        ```
    + Kiểm tra và đồng bộ dữ liệu:
        + Kiểm tra trạng thái của Data Guard: `SHOW PARAMETER DG_BROKER_START;`
        + Kiểm tra trạng thái của các slave: `SELECT * FROM V$DATAGUARD_STATUS;`








