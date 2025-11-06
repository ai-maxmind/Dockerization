#!/bin/bash
set -euo pipefail

DESTINATION=${1:-}
PORT=${2:-}
CHAT=${3:-}

if [ -z "$DESTINATION" ] || [ -z "$PORT" ] || [ -z "$CHAT" ]; then
  echo "Usage: $0 <destination_folder> <port> <chat_port>"
  exit 1
fi

if ! command -v git &> /dev/null; then
  echo "Git not found! Please install Git >= 2.25."
  exit 1
fi

GIT_VERSION=$(git --version | awk '{print $3}')
if [[ $(echo "$GIT_VERSION < 2.25" | bc) -eq 1 ]]; then
  echo "Git version must be >= 2.25 for sparse-checkout."
  exit 1
fi

git init "$DESTINATION"
cd "$DESTINATION"

git remote add -f origin https://github.com/ai-maxmind/Dockerization.git

git sparse-checkout init --cone
git sparse-checkout set odoo/odoo-18-docker-compose

git pull origin main

mv odoo/odoo-18-docker-compose/* .
rm -rf odoo

mkdir -p postgresql
sudo chown -R "$USER:$USER" "$DESTINATION"
sudo chmod -R 700 postgresql


if [ ! -f docker-compose.yml ]; then
  echo "docker-compose.yml not found!"
  exit 1
fi
cp docker-compose.yml docker-compose.yml.bak

if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s/10019/$PORT/g; s/20019/$CHAT/g" docker-compose.yml
else
  sed -i "s/10019/$PORT/g; s/20019/$CHAT/g" docker-compose.yml
fi

find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;

[ -f entrypoint.sh ] && chmod +x entrypoint.sh

if ! command -v docker &> /dev/null; then
  echo "Docker not found! Please install Docker."
  exit 1
fi

if command -v docker-compose &> /dev/null; then
  DOCKER_COMPOSE_CMD="docker-compose"
else
  DOCKER_COMPOSE_CMD="docker compose"
fi

$DOCKER_COMPOSE_CMD -f docker-compose.yml up -d

echo "Odoo started at http://localhost:$PORT | Master Password: admin | Live chat port: $CHAT"
