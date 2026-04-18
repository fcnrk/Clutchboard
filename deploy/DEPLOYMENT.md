# Clutchboard — Deployment Guide

Step-by-step instructions for deploying Clutchboard to a Hetzner VPS from scratch.

**Target:** Ubuntu 24.04 on Hetzner CX32 (~€10/mo)

---

## Prerequisites (local machine)

- SSH key pair (`ssh-keygen -t ed25519` if you don't have one)
- A registered domain with access to DNS settings
- A CS2 GSLT token from [steamcommunity.com/dev/managegameservers](https://steamcommunity.com/dev/managegameservers) (App ID: `730`)
- .NET 8 SDK installed (to build the plugin)

---

## Part 1: Hetzner Server

### 1.1 Create the server

1. Log in to [console.hetzner.cloud](https://console.hetzner.cloud)
2. Create a new project, then click **Add Server**
3. Choose settings:
   - **Location:** Falkenstein or Helsinki (EU)
   - **Image:** Ubuntu 24.04
   - **Type:** CX32 (4 vCPU, 8 GB RAM)
   - **SSH keys:** paste the contents of `~/.ssh/id_ed25519.pub`
   - **Firewall:** leave default for now
4. Click **Create & Buy** and note the server's public IP address

### 1.2 Open required ports (Hetzner Firewall)

In the Hetzner console, create a firewall with these inbound rules and attach it to your server:

| Protocol | Port | Purpose |
|----------|------|---------|
| TCP | 22 | SSH |
| TCP | 80 | HTTP (Caddy redirect) |
| TCP | 443 | HTTPS |
| UDP | 27015 | CS2 game traffic |
| TCP | 27015 | CS2 RCON |

---

## Part 2: DNS

In your DNS provider, add two **A records** pointing at the server IP:

```
yourdomain.com      →  <server-ip>
api.yourdomain.com  →  <server-ip>
```

DNS propagation takes a few minutes to a few hours. Caddy will not obtain TLS certificates until DNS resolves correctly.

---

## Part 3: Bootstrap the VPS

### 3.1 Upload bootstrap files

From your local machine:

```bash
scp -r deploy/ root@<server-ip>:~/
```

### 3.2 Run the setup script

```bash
ssh root@<server-ip>
bash ~/deploy/setup.sh
```

This script:
- Creates a `steam` user
- Installs SteamCMD and Docker
- Downloads CS2 (~30 GB — takes 10–20 min depending on connection)
- Registers and enables the `cs2` systemd service

---

## Part 4: Deploy the Docker Stack

### 4.1 Clone the repository

```bash
git clone https://github.com/youruser/clutchboard.git /home/steam/clutchboard
cd /home/steam/clutchboard
```

### 4.2 Create the environment file

```bash
cp .env.example .env
nano .env
```

Fill in every value:

```env
DB_PASSWORD=<strong-random-password>
DB_NAME=clutchboard
DB_USER=postgres
API_SECRET=<strong-random-secret>
DOMAIN=yourdomain.com
CS2_RCON_PASSWORD=<rcon-password>
```

Tips:
- Generate secrets with `openssl rand -hex 32`
- `API_SECRET` must match what you put in `plugin/config.json`
- `DOMAIN` should be your bare domain — Caddy handles both `yourdomain.com` and `api.yourdomain.com`

### 4.3 Build and start the stack

```bash
docker compose up -d --build
```

On first start:
- PostgreSQL initialises the schema from `db/init.sql`
- Caddy fetches TLS certificates from Let's Encrypt (requires DNS to be propagated)
- The API runs Alembic migrations automatically on container start

### 4.4 Verify the stack is healthy

```bash
docker compose ps
```

All services should show `healthy` or `running`. Then:

```bash
curl https://api.yourdomain.com/health
# Expected: {"status":"ok"}
```

Open `https://yourdomain.com` in a browser — you should see the leaderboard (empty for now).

---

## Part 5: CS2 Server

### 5.1 Configure the GSLT token

Edit the systemd service to inject your GSLT token:

```bash
nano /etc/systemd/system/cs2.service
```

Find `+sv_setsteamaccount ${GSLT_TOKEN}` and replace `${GSLT_TOKEN}` with your actual token.

```bash
systemctl daemon-reload
```

### 5.2 Create the steamclient symlink

CS2 looks for `steamclient.so` at `/home/steam/.steam/sdk64/`. SteamCMD installs it elsewhere, so create the symlink once:

```bash
mkdir -p /home/steam/.steam/sdk64
ln -sf /home/steam/steamcmd/linux64/steamclient.so /home/steam/.steam/sdk64/steamclient.so
chown -h steam:steam /home/steam/.steam/sdk64/steamclient.so
```

### 5.3 Start CS2

```bash
systemctl start cs2
systemctl status cs2   # should show "active (running)"
```

To view live server output:

```bash
journalctl -u cs2 -f
```

---

## Part 6: Plugin

### 6.1 Install CounterStrikeSharp

CounterStrikeSharp must be installed on the CS2 server before the plugin will load. Follow the official installation guide at [docs.cssharp.dev](https://docs.cssharp.dev) for the server-side runtime.

### 6.2 Build the plugin

On your local machine:

```bash
cd plugin
dotnet build -c Release
```

Output: `bin/Release/net8.0/Clutchboard.dll`

### 6.3 Configure the plugin

Edit `plugin/config.json`:

```json
{
  "ApiUrl": "http://localhost:8000",
  "ApiSecret": "<same-value-as-API_SECRET-in-.env>"
}
```

The plugin talks to the API over localhost (they're on the same machine), so no HTTPS needed here.

### 6.4 Copy plugin files to the server

```bash
PLUGIN_DST="/home/steam/cs2/game/csgo/addons/counterstrikesharp/plugins/Clutchboard"

ssh root@<server-ip> "mkdir -p $PLUGIN_DST"

scp plugin/bin/Release/net8.0/Clutchboard.dll root@<server-ip>:$PLUGIN_DST/
scp plugin/config.json                         root@<server-ip>:$PLUGIN_DST/
```

### 6.5 Restart CS2 to load the plugin

```bash
ssh root@<server-ip> 'systemctl restart cs2'
```

Check the CS2 logs to confirm the plugin loaded without errors:

```bash
ssh root@<server-ip> 'journalctl -u cs2 -n 50'
```

---

## Verification

Run through this checklist after deployment:

- [ ] `docker compose ps` — all services healthy
- [ ] `curl https://api.yourdomain.com/health` returns `{"status":"ok"}`
- [ ] `https://yourdomain.com` loads the dashboard
- [ ] CS2 server is reachable at `<server-ip>:27015`
- [ ] Plugin logs show no errors in `journalctl -u cs2`
- [ ] Join the CS2 server, play a round — stats appear in the dashboard after the match ends

---

## Ongoing Operations

### Update the dashboard and API

```bash
ssh root@<server-ip>
cd /home/steam/clutchboard
git pull
docker compose up -d --build
```

### Update CS2 and the plugin

Build the plugin locally first, then on the server:

```bash
bash ~/deploy/update-cs2.sh
```

This stops CS2, updates the game files via SteamCMD, copies the new plugin binaries, and restarts CS2.

### Run database migrations

After pulling changes that include new Alembic migrations:

```bash
docker compose exec api alembic upgrade head
```

### View logs

```bash
docker compose logs -f api        # API logs
docker compose logs -f dashboard  # Next.js logs
docker compose logs -f caddy      # Caddy / TLS logs
journalctl -u cs2 -f              # CS2 server logs
```

### Back up the database

```bash
docker compose exec postgres pg_dump -U postgres clutchboard > backup-$(date +%Y%m%d).sql
```

### Restart individual services

```bash
docker compose restart api
docker compose restart dashboard
systemctl restart cs2
```

---

## Troubleshooting

**Caddy shows certificate errors**
DNS hasn't propagated yet, or your A records are wrong. Check with `dig yourdomain.com` and wait for propagation.

**API container keeps restarting**
Check logs: `docker compose logs api`. Most likely the database isn't ready yet (wait for postgres to be healthy) or there's a missing env var.

**Plugin not loading**
Confirm CounterStrikeSharp is installed correctly. Check CS2 logs for `[Clutchboard]` entries. Verify `config.json` is in the same directory as `Clutchboard.dll`.

**Stats not appearing after a match**
The materialized view refreshes only at match end (when the plugin sends `match_end`). Check API logs during the match to confirm events are being received: `docker compose logs -f api`.

**`X-Api-Secret` errors in API logs**
The `ApiSecret` in `plugin/config.json` doesn't match `API_SECRET` in `.env`. They must be identical.

**CS2 crashes with `libv8.so: cannot open shared object file`**
The service file sets `LD_LIBRARY_PATH` for this. If you copied the service file before this fix, re-copy it and `systemctl daemon-reload && systemctl restart cs2`.

**CS2 warns `steamclient.so: No such file or directory`**
Run the symlink step in 5.2 above. The SteamCMD linux64 directory is where `steamclient.so` lives after a `steamcmd +quit` run.
