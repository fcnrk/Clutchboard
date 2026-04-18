# Clutchboard

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=next.js&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![.NET](https://img.shields.io/badge/.NET-8-512BD4?logo=dotnet&logoColor=white)

A self-hosted CS2 stats tracker for private servers. Captures granular match data via a CounterStrikeSharp plugin and presents it through a web dashboard — kills, ADR, HS%, weapon breakdowns, round timelines, and per-match performance trends.

## Architecture

```
CS2 Server (srcds)
  └─► CounterStrikeSharp Plugin (C#)
        └─► POST /events  →  FastAPI (Python 3.12)
                                └─► PostgreSQL 16
                                      └─► Next.js 14 Dashboard
                                            └─► Caddy (auto-HTTPS)
```

The CS2 server runs natively via systemd. Everything else runs in Docker Compose on a single VPS.

## Features

- **Live event ingestion** — kills, damage, utility, flashes, weapon fires, round outcomes
- **Per-match scoreboard** — kills, deaths, assists, ADR, HS%, damage dealt
- **Player profiles** — lifetime stats, match history, weapon breakdown, performance trend charts
- **Round timeline** — colour-coded round-by-round outcomes split at half-time
- **Weapon meta** — server-wide kill counts per weapon
- **Head-to-head** — side-by-side stat comparison between two players
- **API secret auth** — plugin authenticates with a shared secret on every request
- **Auto-HTTPS** — Caddy handles TLS certificates via Let's Encrypt

## Stack

| Layer | Technology |
|-------|-----------|
| Plugin | C# / .NET 8 / CounterStrikeSharp |
| API | Python 3.12, FastAPI, asyncpg, Alembic |
| Database | PostgreSQL 16 |
| Dashboard | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| Proxy | Caddy 2 |
| Infra | Docker Compose, Ubuntu 24.04, Hetzner CX32 |

## Quick Start (local dev)

**Prerequisites:** Docker Desktop, Python 3.12, Node.js 20+, .NET 8 SDK

```bash
# 1. Start PostgreSQL
docker compose up postgres -d

# 2. Run the API
cd api
python -m venv .venv && source .venv/Scripts/activate  # Windows
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Run the dashboard
cd dashboard
npm install
npm run dev
```

Dashboard at `http://localhost:3000` · API at `http://localhost:8000`

## Deployment

### 1. Provision a VPS

A Hetzner CX32 (~€10/mo) is the target. Bootstrap it:

```bash
scp -r deploy/ root@<server-ip>:~/
ssh root@<server-ip> 'bash ~/deploy/setup.sh'
```

This installs Docker, SteamCMD, downloads CS2, and registers the systemd service.

### 2. Configure and deploy

```bash
git clone <this-repo> /home/steam/clutchboard
cd /home/steam/clutchboard
cp .env.example .env
nano .env  # fill in DB_PASSWORD, API_SECRET, DOMAIN
docker compose up -d --build
```

### 3. Start CS2

Edit `/etc/systemd/system/cs2.service` to add your GSLT token, then:

```bash
systemctl start cs2
```

### 4. Install the plugin

```bash
cd plugin && dotnet build -c Release
scp bin/Release/net8.0/Clutchboard.dll root@<server-ip>:/home/steam/cs2/game/csgo/addons/counterstrikesharp/plugins/Clutchboard/
```

Update `plugin/config.json` with your API URL and secret, then copy it alongside the DLL.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_PASSWORD` | PostgreSQL password |
| `DB_NAME` | Database name (default: `clutchboard`) |
| `DB_USER` | Database user (default: `postgres`) |
| `API_SECRET` | Shared secret sent by the plugin in `X-Api-Secret` |
| `DOMAIN` | Your domain (e.g. `clutchboard.gg`) — used for CORS and Caddy |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events` | Batch event ingestion (plugin → API) |
| `GET` | `/api/players` | Leaderboard |
| `GET` | `/api/players/{steam_id}` | Player profile |
| `GET` | `/api/players/{steam_id}/matches` | Match history |
| `GET` | `/api/players/{steam_id}/weapons` | Weapon breakdown |
| `GET` | `/api/players/{steam_id}/trends` | Per-match stat trends |
| `GET` | `/api/matches` | Match list |
| `GET` | `/api/matches/{id}` | Match detail with scoreboard + round timeline |
| `GET` | `/api/weapons` | Server-wide weapon meta |
| `GET` | `/api/head-to-head?p1=&p2=` | Head-to-head comparison |
| `GET` | `/health` | Health check |

## Project Structure

```
├── plugin/          # CounterStrikeSharp C# plugin
├── api/             # FastAPI backend
│   ├── app/
│   │   ├── routers/ # HTTP endpoints
│   │   ├── schemas/ # Pydantic models
│   │   └── services/# Business logic (match aggregation)
│   └── tests/
├── dashboard/       # Next.js frontend
│   └── src/
│       ├── app/     # Pages (App Router)
│       ├── components/
│       └── lib/api.ts
├── db/init.sql      # Schema + materialized views
├── deploy/          # setup.sh, systemd service, update scripts
├── docker-compose.yml
└── Caddyfile
```

## License

MIT
