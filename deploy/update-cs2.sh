#!/usr/bin/env bash
set -euo pipefail

echo "==> Stopping CS2 server"
systemctl stop cs2

echo "==> Updating CS2"
sudo -u steam /usr/games/steamcmd \
  +force_install_dir /home/steam/cs2 \
  +login anonymous \
  +app_update 730 validate \
  +quit

echo "==> Copying plugin binaries"
# Assumes plugin is built to plugin/bin/Release/net8.0/
PLUGIN_SRC="$(dirname "$0")/../plugin/bin/Release/net8.0"
PLUGIN_DST="/home/steam/cs2/game/csgo/addons/counterstrikesharp/plugins/Clutchboard"
mkdir -p "$PLUGIN_DST"
cp "$PLUGIN_SRC/Clutchboard.dll" "$PLUGIN_DST/"
cp "$(dirname "$0")/../plugin/config.json" "$PLUGIN_DST/"

echo "==> Starting CS2 server"
systemctl start cs2
echo "==> Done"
