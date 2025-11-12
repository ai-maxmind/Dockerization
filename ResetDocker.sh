#!/bin/bash

StopAllContainers() {
    echo -e "\n🛑 Stopping all containers..."
    docker ps -aq | xargs -r docker stop
    echo "✅ Done stopping!"
}

RemoveAllContainers() {
    echo -e "\n🧹 Removing all containers..."
    docker ps -aq | xargs -r docker rm -f
    echo "✅ Done removing!"
}

RemoveAllImages() {
    echo -e "\n🧼 Removing all images..."
    docker images -aq | xargs -r docker rmi -f
    echo "✅ Done removing!"
}

RemoveAllVolumes() {
    echo -e "\n🧺 Removing all volumes..."
    docker volume ls -q | xargs -r docker volume rm
    echo "✅ Done removing!"
}

RemoveNetworks() {
    echo -e "\n🌐 Removing unused networks..."
    docker network prune -f
    echo "✅ Done!"
}

PruneBuilder() {
    echo -e "\n🧱 Pruning builder cache..."
    docker builder prune -a -f
    echo "✅ Done!"
}

ResetAllDocker() {
    echo -e "\n🔥 Performing FULL Docker reset..."
    StopAllContainers
    RemoveAllContainers
    RemoveAllImages
    RemoveAllVolumes
    RemoveNetworks
    PruneBuilder
    echo -e "\n✅ All done! Docker is now clean."
}

RunAll() {
    echo -e "\n⚙️  Running ALL cleanup tasks..."
    StopAllContainers
    RemoveAllContainers
    RemoveAllImages
    RemoveAllVolumes
    RemoveNetworks
    PruneBuilder
    echo -e "\n✅ ALL cleanup tasks completed!"
}

UninstallDocker() {
    echo -e "\n🧨 Uninstalling Docker..."

    sudo systemctl stop docker || true
    sudo systemctl stop docker.socket || true

    echo "🔧 Removing Docker packages..."
    sudo apt-get remove -y docker docker-engine docker.io containerd runc
    sudo apt-get purge -y docker* containerd runc

    echo "🗑️  Removing Docker data directories..."
    sudo rm -rf /var/lib/docker /etc/docker ~/.docker

    echo "✅ Docker uninstallation completed!"
}

InstallDocker() {
    echo -e "\n📦 Installing Docker (stable, pinned versions)..."
    if command -v lsb_release >/dev/null 2>&1; then
        CODENAME="$(lsb_release -cs)"
    else
        CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
    fi
    echo "🔎 Detected Ubuntu codename: ${CODENAME:-unknown}"
    echo "🔐 Adding official Docker apt repo..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
      | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

    sudo apt-get update -y

    echo "🧹 Removing old Docker packages (if any)..."
    sudo apt-get remove -y docker docker-engine docker.io containerd runc || true

    local PINNED_ENGINE=""
    local PINNED_CLI=""
    local PINNED_CONTAINERD="1.7.17-1"

    case "${CODENAME}" in
      jammy) 
        PINNED_ENGINE="5:25.0.5-1~ubuntu.22.04~jammy"
        PINNED_CLI="5:25.0.5-1~ubuntu.22.04~jammy"
        ;;
      noble)  
        PINNED_ENGINE="5:25.0.5-1~ubuntu.24.04~noble"
        PINNED_CLI="5:25.0.5-1~ubuntu.24.04~noble"
        ;;
      *)
        echo "⚠️  Unknown codename: ${CODENAME}. Will install latest stable instead of pinned."
        ;;
    esac

    echo "⬇️  Installing Docker Engine/CLI + containerd + compose plugin..."
    if [[ -n "$PINNED_ENGINE" && -n "$PINNED_CLI" ]]; then
        if ! sudo apt-get install -y \
            docker-ce="${PINNED_ENGINE}" \
            docker-ce-cli="${PINNED_CLI}" \
            containerd.io="${PINNED_CONTAINERD}" \
            docker-buildx-plugin docker-compose-plugin; then
          echo "⚠️  Pinned versions not available for this codename. Installing latest stable..."
          sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        fi
    else
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    fi

    echo "🧾 Writing /etc/docker/daemon.json ..."
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json >/dev/null <<'JSON'
{
  "storage-driver": "overlay2",
  "max-concurrent-downloads": 6,
  "max-concurrent-uploads": 4,
  "log-driver": "local",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "features": {
    "buildkit": true
  }
}
JSON

    echo "🔁 Enabling & starting Docker service..."
    sudo systemctl enable docker || true
    sudo systemctl daemon-reload || true
    sudo systemctl restart docker
    sleep 1
    if systemctl is-active --quiet docker; then
        echo "✅ Docker service is active."
    else
        echo "❌ Docker service is not active. Check: sudo journalctl -u docker -e"
    fi

    if [[ -n "${USER:-}" ]]; then
        echo "👤 Adding current user to 'docker' group: $USER"
        sudo usermod -aG docker "$USER" || true
        echo "ℹ️  You may need to log out and log back in for group changes to take effect."
    fi

    echo -e "\n🔎 Versions:"
    docker version || true
    docker compose version || true
    command -v containerd >/dev/null 2>&1 && containerd --version || true
    command -v runc >/dev/null 2>&1 && runc --version || true

    echo -e "\n🧪 Running hello-world smoke test..."
    if docker run --rm hello-world >/dev/null 2>&1; then
        echo "✅ Docker hello-world OK."
    else
        echo "⚠️  hello-world failed (network/proxy?). Try: docker run --rm -it ubuntu:24.04 echo OK"
    fi

    echo -e "\n🎉 Docker installation completed!"
}

while true; do
    clear
    echo "=============================="
    echo "     🐳 DOCKER MANAGEMENT MENU"
    echo "=============================="
    echo "1. Stop all containers"
    echo "2. Remove all containers"
    echo "3. Remove all images"
    echo "4. Remove all volumes"
    echo "5. Remove unused networks"
    echo "6. Prune builder cache"
    echo "7. Reset all Docker (Full Reset)"
    echo "8. Run ALL cleanup tasks"
    echo "9. Uninstall Docker"
    echo "10. Install Docker"
    echo "0. Exit"
    echo "=============================="
    read -p "Enter your choice (0-10): " choice

    case $choice in
        1) StopAllContainers ;;
        2) RemoveAllContainers ;;
        3) RemoveAllImages ;;
        4) RemoveAllVolumes ;;
        5) RemoveNetworks ;;
        6) PruneBuilder ;;
        7) ResetAllDocker ;;
        8) RunAll ;;
        9) UninstallDocker ;;
        10) InstallDocker ;;
        0) echo "👋 Exiting..."; break ;;
        *) echo "❌ Invalid choice! Try again." ;;
    esac

    echo
    read -p "Press Enter to continue..."
done
