# 🚀 Chromium Docker Ultimate

**Môi trường phát triển Chromium toàn diện trong Docker**  
Dành cho lập trình viên muốn build, debug, test, hoặc mở rộng mã nguồn trình duyệt Chromium mà **không làm bẩn máy host**.

---

## 📦 Thành phần trong gói

| File/Thư mục | Mô tả |
|---------------|-------|
| `Dockerfile` | Image Ubuntu 24.04 + `depot_tools`, `ccache`, `xvfb`, `x11vnc`, `noVNC`, hỗ trợ GPU |
| `docker-compose.yml` | Định nghĩa các profile: `dev`, `gpu`, `vnc` |
| `scripts/` | Bộ lệnh tiện ích (`bootstrap-chromium`, `gn-gen-dev`, `build-chromium`, `run-chromium`, …) |
| `.devcontainer/devcontainer.json` | Cấu hình cho VS Code Remote Containers |
| `ccache/`, `artifacts/`, `recordings/` | Thư mục mount sẵn: cache, bản build, video test |

---

## ⚙️ Yêu cầu hệ thống

- **OS:** Ubuntu 22.04/24.04 hoặc Windows 11 (WSL2 + Docker Desktop + WSLg)  
- **Công cụ:**  
  ```bash
  sudo apt install docker.io docker-compose-plugin -y
  sudo usermod -aG docker $USER   # rồi logout/login lại
  docker version && docker compose version
  ```
- Dung lượng trống ≥ 150 GB (Chromium repo + out + ccache)
- RAM ≥ 16 GB (khuyến nghị 32 GB để build nhanh hơn)

---

## 🚀 Bắt đầu sử dụng

### 1️⃣ Build image
```bash
docker compose build
```

### 2️⃣ Chạy container dev chính
```bash
docker compose run --rm chromium-dev bash
```
Bạn đang ở `/work` (user `builder`, không root, UID/GID trùng host).

---

## 🧱 Fetch mã nguồn Chromium & cài dependencies

Trong container:
```bash
bootstrap-chromium
```
Lệnh này sẽ:
1. `fetch chromium`  
2. `gclient sync`  
3. `./build/install-build-deps.sh`  
4. `gclient runhooks`

Sau khi xong, mã nguồn có tại `/work/src`.

---

## ⚙️ Cấu hình GN (build config)

### Dev nhanh (Debug + ccache)
```bash
gn-gen-dev
```

### Release build
```bash
gn-gen-rel
```

Tất cả cấu hình build được lưu trong `src/out/<dir>`.

---

## 🧩 Build Chromium

```bash
build-chromium chrome
# hoặc:
autoninja -C src/out/Default chrome
```

Theo dõi cache:
```bash
ccache -s
```

---

## 🧪 Chạy Chromium trong container

```bash
run-chromium --remote-debugging-port=9222 https://example.com
```
- Nếu có `DISPLAY`: chạy GUI thật (X11/WSLg).  
- Nếu không: tự động chạy headless qua `xvfb`.  
- Nếu gặp lỗi sandbox, thêm `--no-sandbox`.

---

## 🧠 Quy trình phát triển chuẩn

| Bước | Lệnh | Mô tả |
|------|------|-------|
| 1 | `docker compose run --rm chromium-dev bash` | Vào môi trường dev |
| 2 | `bootstrap-chromium` | Lấy và đồng bộ mã |
| 3 | `gn-gen-dev` | Tạo config debug |
| 4 | `build-chromium chrome` | Build trình duyệt |
| 5 | `run-chromium` | Chạy & test |
| 6 | Sửa mã trong `src/` | Dev |
| 7 | Build lại & chạy lại | Lặp vòng |

---

## 🧰 Các tính năng nâng cao

### 🖥️ 1. Bật GPU tăng tốc (VA-API)

Sửa `docker-compose.yml`:
```yaml
devices:
  - /dev/dri:/dev/dri
```

Rồi:
```bash
docker compose --profile gpu run --rm chromium-gpu bash
run-chromium --use-gl=desktop --enable-features=VaapiVideoDecoder
```

> Yêu cầu host có driver VAAPI phù hợp (Intel/AMD/NVIDIA).

---

### 🌐 2. Chạy VNC / noVNC (nếu không có GUI)

```bash
docker compose --profile vnc up chromium-vnc -d
```
- Mở trình duyệt host → `http://localhost:6080`
- Đăng nhập không cần mật khẩu, xem desktop Fluxbox trong container.

---

### 🧪 3. Test tự động (headless)

```bash
test-chromium
```

Hoặc:
```bash
build-chromium base_unittests
xvfb-run -a ./src/out/Default/base_unittests --gtest_filter=SomeSuite.*
```

---

### 🎥 4. Ghi lại video test (xvfb + ffmpeg)
```bash
record-run /work/recordings https://example.com
```
Video sẽ lưu tại `recordings/run-<timestamp>.mp4`.

---

### 📦 5. Đóng gói bản Release
```bash
package-rel
```
Kết quả `.tar.gz` lưu trong `artifacts/`.

---

### 🧹 6. Dọn dẹp / cập nhật
```bash
docker compose down
docker image prune
cd src && gclient sync -D --force && gclient runhooks
```

---

## 🧑‍💻 Tích hợp VS Code DevContainer

### Bật extension
- **Remote – Containers**
- **C/C++ Tools**
- **Clangd**
- **GitLens**

### Mở project
> `Ctrl + Shift + P` → **Dev Containers: Open Folder in Container**  
Chọn thư mục `chromium_docker_ultimate`.

Bạn sẽ có:
- Terminal dev trực tiếp trong container  
- Tự động map `ccache` & `src`  
- IntelliSense, clangd, symbol lookup đầy đủ  

---

## ⚡ Tối ưu hiệu năng

| Thành phần | Gợi ý |
|-------------|-------|
| **ccache** | `ccache -M 50G` để cache build |
| **SHM** | `shm_size: "4gb"` trong compose để tránh crash |
| **Disk** | Giữ `out/`, `ccache/`, `src/` trên SSD NVMe |
| **RAM** | ≥ 16GB, build song song tốt hơn (tự động theo `autoninja`) |
| **Threads** | Mặc định `autoninja` dùng toàn bộ CPU, có thể giới hạn `-j <n>` |

---

## 🩻 Debug build / symbols

Tạo cấu hình với symbol cao:
```bash
gn gen out/Sym --args='is_debug=false is_component_build=false symbol_level=2 use_thin_lto=false cc_wrapper="ccache"'
autoninja -C out/Sym chrome
```

Dùng với ASan/UBSan:
```bash
gn-gen-asan
gn-gen-ubsan
```

---

## 🪄 Troubleshooting nhanh

| Vấn đề | Cách xử lý |
|--------|-------------|
| Không hiện GUI | `xhost +si:localuser:$(id -un)` trên Linux, hoặc dùng profile `vnc` |
| Permission lỗi khi bind mount | Sửa UID/GID trong `docker-compose.yml` |
| Thiếu gói khi build | `gclient runhooks` lại, script của Chromium tự cài đúng version |
| Lỗi sandbox | Dùng `--no-sandbox` khi chạy `run-chromium` |
| Đầy ổ đĩa | Xoá cache cũ: `ccache -C`, hoặc `docker system prune` |

---

