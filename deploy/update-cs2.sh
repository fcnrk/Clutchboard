#!/usr/bin/env bash
set -euo pipefail

LOG=/var/log/cs2-update.log
exec >> "$LOG" 2>&1
echo ""
echo "==> CS2 update started at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

PLUGIN_SRC="$(dirname "$0")/../plugin/bin/Release/net8.0"
PLUGIN_DST="/home/steam/cs2/game/csgo/addons/counterstrikesharp/plugins/Clutchboard"
GAMEINFO="/home/steam/cs2/game/csgo/gameinfo.gi"
METAMOD_DIR="/home/steam/cs2/game/csgo"
ADDONS_DIR="/home/steam/cs2/game/csgo/addons"

echo "==> Stopping CS2 server"
systemctl stop cs2

echo "==> Updating CS2 via SteamCMD"
sudo -u steam /usr/games/steamcmd \
  +force_install_dir /home/steam/cs2 \
  +login anonymous \
  +app_update 730 validate \
  +quit

echo "==> Updating Metamod"
METAMOD_URL=$(curl -sA "Mozilla/5.0" https://mms.alliedmods.net/mmsdrop/2.0/ \
  | grep -oP 'mmsource-[0-9.]+-git\d+-linux\.tar\.gz' \
  | tail -1)

if [[ -n "$METAMOD_URL" ]]; then
  if curl -fLA "Mozilla/5.0" -e "https://mms.alliedmods.net/mmsdrop/2.0/" \
       "https://mms.alliedmods.net/mmsdrop/2.0/${METAMOD_URL}" \
       | tar -xz -C "$METAMOD_DIR"; then
    echo "    Installed ${METAMOD_URL}"
  else
    echo "    WARNING: Metamod download failed — keeping existing install"
  fi
else
  echo "    WARNING: Could not fetch Metamod URL — skipping download, keeping existing install"
fi

echo "==> Verifying gameinfo.gi Metamod entry"
if ! grep -q "addons/metamod" "$GAMEINFO"; then
  sed -i 's|\t\t\tGame_LowViolence|\t\t\tGame\t\tcsgo/addons/metamod\n\t\t\tGame_LowViolence|' "$GAMEINFO"
  echo "    Entry added"
else
  echo "    Entry already present"
fi

echo "==> Verifying Metamod vdf files"
if [[ ! -f "$ADDONS_DIR/metamod.vdf" ]] || [[ ! -f "$ADDONS_DIR/metamod_x64.vdf" ]]; then
  echo "    ERROR: Metamod vdf files missing — Metamod may not have installed correctly"
  exit 1
fi
echo "    OK"

echo "==> Updating CounterStrikeSharp"
CSS_ASSET=$(curl -s "https://api.github.com/repos/roflmuffin/CounterStrikeSharp/releases/latest" \
  | grep -oP '"browser_download_url": "\K[^"]+counterstrikesharp-with-runtime-build-[^"]+linux-x64[^"]*\.tar\.gz')

if [[ -n "$CSS_ASSET" ]]; then
  if curl -fL "$CSS_ASSET" | tar -xz -C "$METAMOD_DIR"; then
    echo "    Installed $(basename "$CSS_ASSET")"
  else
    echo "    WARNING: CounterStrikeSharp download failed — keeping existing install"
  fi
else
  echo "    WARNING: Could not fetch CounterStrikeSharp release — skipping, keeping existing install"
fi

echo "==> Copying plugin binaries"
if [[ ! -f "$PLUGIN_SRC/Clutchboard.dll" ]]; then
  echo "    WARNING: Plugin DLL not found at $PLUGIN_SRC — skipping plugin copy (build and deploy manually)"
else
  mkdir -p "$PLUGIN_DST"
  cp "$PLUGIN_SRC/Clutchboard.dll" "$PLUGIN_DST/"
  cp "$(dirname "$0")/../plugin/config.json" "$PLUGIN_DST/"
  echo "    Copied $(ls -lh "$PLUGIN_DST/Clutchboard.dll" | awk '{print $5}') Clutchboard.dll"
fi

echo "==> Starting CS2 server"
systemctl start cs2
echo "==> Done at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
