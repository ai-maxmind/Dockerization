#!/bin/bash
echo "Stop all containers..."
sudo docker stop $(sudo docker ps -aq)
echo "Delete all containers..."
sudo docker rm $(sudo docker ps -aq)
echo "Delete all networks..."
sudo docker network rm $(docker network ls -q)
echo "Delete all volumes..."
sudo docker volume rm $(sudo docker volume ls -q)
echo "Delete all images..."
sudo docker rmi $(sudo docker images -q)
echo "System updating..."
sudo apt-get update
echo "Uninstall Docker and related packages..."
sudo apt-get remove --purge -y docker-ce docker-ce-cli containerd.io
echo "Delete Docker data directory..."
sudo rm -rf /var/lib/docker
echo "Delete Docker configuration files..."
sudo rm -rf /etc/apt/keyrings/docker.asc
sudo rm -rf /etc/apt/sources.list.d/docker.list

echo "Clean up unused packages..."
sudo apt-get autoremove -y
sudo apt-get autoclean -y
echo "Check if Docker is uninstalled..."
docker --version
