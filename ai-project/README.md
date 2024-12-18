# Docker for AI
## Cài đặt Docker trên Windows 
Tham khảo cài đặt tại đường dẫn: https://docs.docker.com/desktop/install/windows-install/
## Cài đặt Docker trên Ubuntu
### 1. Chuẩn bị hệ thống
Đầu tiên, cài đặt các package cần thiết để chuẩn bị cho việc cài đặt Docker:

```
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release
```

Thêm Docker GPG key vào hệ thống:
```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

Thiết lập Docker repository:
```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
### 2. Cài đặt Docker Engine
Sử dụng apt-get (hoặc apt) để cài đặt Docker vào máy:
```
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

Để xác nhận Docker đã được cài đặt và hoạt động ổn định, kiểm tra bằng cách sau:
```
sudo docker run hello-world
```

Nếu nhận được thông báo **Hello from Docker!** như hình dưới đây thì Docker đã sẵn sàng hoạt động:

```
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 <https://hub.docker.com/>

For more examples and ideas, visit:
 <https://docs.docker.com/get-started/>
```

### 3. Thêm user vào group Docker
Để quản lý Docker dưới tài khoản non-root (không cần phải chèn **sudo** khi gõ lệnh), ta cần gán tài khoản hiện tại vào user group Docker như sau:

```
sudo groupadd docker
sudo usermod -aG docker $USER
```

### 4. Cài đặt Docker Compose
Tiếp theo, cài đặt thêm Docker Compose để sau này có thể khởi tạo các ứng dụng sử dụng nhiều container một cách nhanh chóng. Với Docker Compose, chúng ta sử dụng một file YAML để thiết lập các service cần thiết cho chương trình. 
#### Cài đặt trên máy tính Intel / AMD
Tải Docker Compose phiên bản mới nhất về máy: 

```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

Thiết lập quyền thực thi cho **docker-compose** và tạo **symlink**:

```
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

Kiểm tra lại docker-compose đã cài đặt chưa bằng lệnh: `docker-compose --version`