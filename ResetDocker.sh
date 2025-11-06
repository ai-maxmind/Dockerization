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
    echo -e "\n📦 Installing Docker..."
    if command -v docker >/dev/null 2>&1; then
        echo "Docker is already installed."
        return
    fi

    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "$USER"
    rm -f get-docker.sh

    echo -e "\n✅ Docker installation completed!"
    echo "⚠️  Please log out and log in again for group changes to take effect."
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
