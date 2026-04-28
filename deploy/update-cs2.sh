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

echo "==> Updating Metamod"
METAMOD_URL=$(curl -s https://mms.alliedmods.net/mmsdrop/2.0/ \
  | grep -oP 'mmsource-[0-9.]+-git\d+-linux\.tar\.gz' \
  | tail -1)
curl -fL "https://mms.alliedmods.net/mmsdrop/2.0/${METAMOD_URL}" \
  | tar -xz -C /home/steam/cs2/game/csgo/
echo "    Installed ${METAMOD_URL}"

echo "==> Restoring gameinfo.gi Metamod entry"
if ! grep -q "addons/metamod" /home/steam/cs2/game/csgo/gameinfo.gi; then
  sed -i 's|\t\t\tGame_LowViolence|\t\t\tGame\t\tcsgo/addons/metamod\n\t\t\tGame_LowViolence|' \
    /home/steam/cs2/game/csgo/gameinfo.gi
  echo "    Entry added"
else
  echo "    Entry already present"
fi

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
