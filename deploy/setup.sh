#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for Ubuntu 24.04 on Hetzner CX32
# Run once as root: bash setup.sh

echo "==> Creating steam user"
id steam &>/dev/null || useradd -m -s /bin/bash steam

echo "==> Installing SteamCMD dependencies"
dpkg --add-architecture i386
apt-get update -q
apt-get install -y lib32gcc-s1 steamcmd

echo "==> Installing Docker"
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -q
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
usermod -aG docker steam

echo "==> Downloading CS2"
sudo -u steam /usr/games/steamcmd \
  +force_install_dir /home/steam/cs2 \
  +login anonymous \
  +app_update 730 validate \
  +quit

echo "==> Installing server.cfg"
mkdir -p /home/steam/cs2/game/csgo/cfg
cp /root/deploy/server.cfg /home/steam/cs2/game/csgo/cfg/server.cfg
chown steam:steam /home/steam/cs2/game/csgo/cfg/server.cfg

echo "==> Installing systemd service"
cp /root/deploy/cs2.service /etc/systemd/system/cs2.service
systemctl daemon-reload
systemctl enable cs2

echo "==> Installing CS2 auto-update timer (daily at 05:00 UTC)"
cp /root/deploy/cs2-update.service /etc/systemd/system/cs2-update.service
cp /root/deploy/cs2-update.timer /etc/systemd/system/cs2-update.timer
systemctl daemon-reload
systemctl enable --now cs2-update.timer

echo "==> Setup complete. Copy your .env file and run: docker compose up -d --build"
