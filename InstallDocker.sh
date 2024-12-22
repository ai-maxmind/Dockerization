#!/bin/bash
echo "Updating system..."
sudo apt-get update -y

echo "Install dependencies..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
echo "Add Docker GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
echo "Add Docker repository to apt..."
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
echo "Update the repository..."
sudo apt-get update -y
echo "Install Docker..."
sudo apt-get install -y docker-ce
echo "Check Docker status..."
sudo systemctl status docker
echo "Install Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
echo "Grant executable permissions to Docker Compose..."
sudo chmod +x /usr/local/bin/docker-compose
echo "Check Docker and Docker Compose versions..."
docker --version
docker-compose --version
echo "Enable Docker auto-start..."
sudo systemctl enable docker

echo "Docker installation complete!"