#!/bin/bash
set -euo pipefail

DESTINATION=${1:-}
PORT=${2:-}
CHAT=${3:-}

if [ -z "$DESTINATION" ] || [ -z "$PORT" ] || [ -z "$CHAT" ]; then
  echo "Usage: $0 <destination_folder> <port> <chat_port>"
  exit 1
fi

REPO_URL="https://github.com/ai-maxmind/Dockerization.git"
FOLDER_PATH="odoo/odoo-13-docker-compose"

if ! command -v git &> /dev/null; then
  echo "Git not found! Please install Git >= 2.25 for sparse-checkout."
  exit 1
fi

git init "$DESTINATION"
cd "$DESTINATION"
git remote add -f origin "$REPO_URL"
git sparse-checkout init --cone
git sparse-checkout set "$FOLDER_PATH"
git pull origin main
mv "$FOLDER_PATH"/* .
rm -rf odoo


mkdir -p postgresql
sudo chown -R "$USER:$USER" "$DESTINATION"
sudo chmod -R 700 "$DESTINATION"  


if [[ "$OSTYPE" != "darwin"* ]]; then
  if ! grep -qF "fs.inotify.max_user_watches" /etc/sysctl.conf; then
    echo "fs.inotify.max_user_watches = 524288" | sudo tee -a /etc/sysctl.conf
  else
    echo $(grep -F "fs.inotify.max_user_watches" /etc/sysctl.conf)
  fi
  sudo sysctl -p
fi

if [ ! -f docker-compose.yml ]; then
  echo "docker-compose.yml not found in $DESTINATION!"
  exit 1
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s/10013/$PORT/g; s/20013/$CHAT/g" docker-compose.yml
else
  sed -i "s/10013/$PORT/g; s/20013/$CHAT/g" docker-compose.yml
fi

find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
[ -f entrypoint.sh ] && chmod +x entrypoint.sh


if command -v docker-compose &> /dev/null; then
  DOCKER_COMPOSE_CMD="docker-compose"
else
  DOCKER_COMPOSE_CMD="docker compose"
fi

$DOCKER_COMPOSE_CMD -f docker-compose.yml up -d

echo "Odoo started at http://localhost:$PORT | Master Password: admin | Live chat port: $CHAT"
