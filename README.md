# Dockerization
Dockerize projects with sample structures that will be used in building the software system

# Debug
Some basic docker commands to debug program errors:
+ Kiểm tra log của container cassandra_master: `docker logs cassandra_master`
+ Kiểm tra các cổng đang lắng nghe trong container: `docker exec -it cassandra_master ss -tuln`
+ Sử dụng **lsof** để kiểm tra các cổng: `docker exec -it cassandra_master lsof -i -P -n`
+ Kiểm tra cổng bằng **docker port**: `docker port cassandra_master`
+ Kiểm tra kết nối giữa các container: `docker exec -it cassandra_slave1 ping cassandra_master`
+ Lỗi **"OCI runtime exec failed: exec failed: unable to start container process: exec: "netstat": executable file not found in $PATH: unknown"**: Xảy ra vì netstat không được cài đặt trong container Cassandra. 
    ```
    docker exec -it cassandra_master apt-get update
    docker exec -it cassandra_master apt-get install net-tools
    ```
