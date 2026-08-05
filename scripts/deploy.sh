#!/bin/bash
# Script deploy pe Hetzner VPS

echo "=== DEPLOY AI PLATFORM ==="

# Update
sudo apt update && sudo apt upgrade -y

# Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Docker Compose
sudo apt install -y docker-compose-plugin

# Clone repo (modifica cu repo-ul tau)
# git clone https://github.com/user/ai-platform.git
# cd ai-platform

# Configurare .env pentru productie
cp backend/.env.example backend/.env
echo "Editeaza backend/.env cu valorile de productie!"

# Pornire
docker compose up -d --build

echo "=== Deploy finalizat ==="
echo "Backend: http://IP_SERVER:8000"
echo "Frontend: http://IP_SERVER:5500"