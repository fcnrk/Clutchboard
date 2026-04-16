# Clutchboard — Full Project Scaffold Design

**Date:** 2026-04-16
**Scope:** Full project scaffold — all four components — with complete database layer (SQLAlchemy models + `db/init.sql` + Alembic migration), fully-wired infrastructure configs and API event ingestion, real dashboard page layouts, and C# plugin skeleton. Stats aggregation services and chart components are stubbed with `// TODO` markers.

---

## 1. Directory Structure & Infrastructure

Root layout matches `CLAUDE.md` exactly.

### Root-level files

| File | Status | Notes |
|---|---|---|
| `docker-compose.yml` | Fully wired | Services: `postgres`, `api`, `dashboard`, `caddy`; `api` depends on `postgres` with healthcheck |
| `.env.example` | Fully wired | `DB_PASSWORD`, `DB_NAME`, `API_SECRET`, `DOMAIN`, `CS2_RCON_PASSWORD` |
| `Caddyfile` | Fully wired | `api.{$DOMAIN}` → `api:8000`; `{$DOMAIN}` → `dashboard:3000`; auto-HTTPS via Let's Encrypt |

### `api/`

| File | Status | Notes |
|---|---|---|
| `Dockerfile` | Fully wired | Python 3.12 slim, `pip install -e .`, uvicorn |
| `pyproject.toml` | Fully wired | fastapi, uvicorn, asyncpg, sqlalchemy[asyncio], alembic, pydantic-settings; ruff for dev |
| `alembic.ini` | Fully wired | Async engine, imports all models for autogenerate |
| `alembic/env.py` | Fully wired | Configured for async engine |

### `dashboard/`

| File | Status | Notes |
|---|---|---|
| `Dockerfile` | Fully wired | Node 20 alpine, `npm ci`, `npm run build`, `next start` |
| `package.json` | Fully wired | next 14, react 18, typescript, tailwind, recharts, @types/* |
| `next.config.js`, `tailwind.config.js`, `tsconfig.json` | Fully wired | Standard Next.js 14 App Router config |

### `deploy/`

| File | Status | Notes |
|---|---|---|
| `cs2.service` | Fully wired | `ExecStart`, `Restart=on-failure`, `User=steam` |
| `setup.sh` | Fully wired | Installs SteamCMD, Docker, clones repo, copies `.env` |
| `update-cs2.sh` | Fully wired | `steamcmd +app_update 730 validate +quit`, restarts service |

---

## 2. Database Layer

### Approach: Hybrid autogenerate + manual SQL (Approach C)

SQLAlchemy models are the single source of truth for table structure. Alembic autogenerates table creation. A manual `op.execute()` block in the same migration adds materialized views and complex indexes. `db/init.sql` is a derived artifact — a manual transcription for bootstrapping without Alembic, with a warning comment to keep it in sync.

### Tables

#### `players`
| Column | Type | Notes |
|---|---|---|
| `steam_id` | `BIGINT` | PK |
| `display_name` | `TEXT NOT NULL` | Synced from Steam, updated on each event — can change |
| `real_name` | `TEXT` | Manually set, never overwritten by the plugin |
| `avatar_url` | `TEXT` | |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT now() |

#### `matches`
| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | PK, gen_random_uuid() |
| `map_name` | `TEXT NOT NULL` | |
| `started_at` | `TIMESTAMPTZ NOT NULL` | |
| `ended_at` | `TIMESTAMPTZ` | NULL until match ends |
| `t_score` | `INT` | DEFAULT 0 |
| `ct_score` | `INT` | DEFAULT 0 |
| `duration_seconds` | `INT` | |
| `status` | `TEXT NOT NULL` | `live` / `completed` / `abandoned` |
| `demo_path` | `TEXT` | Path to GOTV `.dem` file |

#### `match_players`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches |
| `steam_id` | `BIGINT` | FK → players |
| `team` | `TEXT NOT NULL` | `T` or `CT` |
| `kills` | `INT` | DEFAULT 0 |
| `deaths` | `INT` | DEFAULT 0 |
| `assists` | `INT` | DEFAULT 0 |
| `damage_dealt` | `INT` | DEFAULT 0 |
| `headshot_kills` | `INT` | DEFAULT 0 |
| `rounds_played` | `INT` | DEFAULT 0 |
| `first_kills` | `INT` | DEFAULT 0 |
| `first_deaths` | `INT` | DEFAULT 0 |
| `utility_damage` | `INT` | DEFAULT 0 |
| `enemies_flashed` | `INT` | DEFAULT 0 |
| `team_flashes` | `INT` | DEFAULT 0 |
| `clutch_attempts` | `INT` | DEFAULT 0 |
| `clutch_wins` | `INT` | DEFAULT 0 |
| `mvp_count` | `INT` | DEFAULT 0 |
| | | UNIQUE(match_id, steam_id) |

#### `rounds`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches |
| `round_number` | `INT NOT NULL` | |
| `winner` | `TEXT NOT NULL` | `T` or `CT` |
| `win_reason` | `TEXT NOT NULL` | `elimination` / `bomb_defused` / `bomb_exploded` / `time_expired` |
| `duration_seconds` | `INT` | |
| | | UNIQUE(match_id, round_number) |

#### `kills`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches ON DELETE CASCADE |
| `round_id` | `INT` | FK → rounds ON DELETE CASCADE |
| `killer_steam_id` | `BIGINT` | FK → players; NULL for world kills |
| `victim_steam_id` | `BIGINT NOT NULL` | FK → players |
| `assister_steam_id` | `BIGINT` | FK → players; nullable |
| `weapon` | `TEXT NOT NULL` | |
| `headshot` | `BOOLEAN` | DEFAULT false |
| `penetrated` | `BOOLEAN` | DEFAULT false |
| `noscope` | `BOOLEAN` | DEFAULT false |
| `thrusmoke` | `BOOLEAN` | DEFAULT false |
| `attacker_blind` | `BOOLEAN` | DEFAULT false |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() |

#### `damage`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches ON DELETE CASCADE |
| `round_id` | `INT` | FK → rounds ON DELETE CASCADE |
| `attacker_steam_id` | `BIGINT` | FK → players; nullable (world damage) |
| `victim_steam_id` | `BIGINT NOT NULL` | FK → players |
| `weapon` | `TEXT NOT NULL` | |
| `damage` | `INT NOT NULL` | |
| `damage_armor` | `INT` | DEFAULT 0 |
| `hitgroup` | `TEXT NOT NULL` | head / chest / stomach / left_arm / right_arm / left_leg / right_leg / generic |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() |

#### `utility_events`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches ON DELETE CASCADE |
| `round_id` | `INT` | FK → rounds ON DELETE CASCADE |
| `steam_id` | `BIGINT` | FK → players |
| `event_type` | `TEXT NOT NULL` | `smoke_start` / `molotov_detonate` / `he_detonate` / `decoy_detonate` |
| `damage` | `INT` | DEFAULT 0 |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() |

#### `flash_events`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches ON DELETE CASCADE |
| `round_id` | `INT` | FK → rounds ON DELETE CASCADE |
| `thrower_steam_id` | `BIGINT` | FK → players |
| `blinded_steam_id` | `BIGINT` | FK → players |
| `blind_duration` | `FLOAT NOT NULL` | Seconds |
| `is_teammate` | `BOOLEAN` | DEFAULT false |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() |

#### `weapon_fires`
| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL` | PK |
| `match_id` | `UUID` | FK → matches ON DELETE CASCADE |
| `round_id` | `INT` | FK → rounds ON DELETE CASCADE |
| `steam_id` | `BIGINT` | FK → players |
| `weapon` | `TEXT NOT NULL` | |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() |

### Materialized View: `player_stats`

Aggregates lifetime stats per player for leaderboard queries. Columns: `steam_id`, `display_name`, `real_name`, `avatar_url`, `total_matches`, `total_kills`, `total_deaths`, `total_assists`, `total_damage`, `total_rounds`, `total_wins`, `kd_ratio`, `adr`, `hs_pct`, `win_rate`, `first_kills_total`, `utility_damage_total`.

Refreshed `CONCURRENTLY` from `match_tracker.end_match()` after each match completes.

### Alembic Migration `0001_initial`

1. Autogenerated section: creates all 9 tables with FK constraints
2. Manual `op.execute()` block:
   - Creates `player_stats` materialized view
   - Adds indexes:
     - `(match_id)` on all event tables
     - `(match_id, round_id)` on kills, damage
     - `(match_id, steam_id, weapon)` on weapon_fires
     - `(killer_steam_id)`, `(victim_steam_id)` on kills
     - `(match_id, steam_id)` on flash_events, utility_events

### `db/init.sql`

Derived artifact. Header comment: `-- WARNING: Derived from Alembic migration 0001_initial. Do not edit directly — update the migration and regenerate.`

---

## 3. FastAPI Layer

### `app/main.py`
FastAPI app with lifespan managing asyncpg pool creation/teardown. CORS via `CORSMiddleware` (all origins in dev, locked via env in prod). Routers mounted: `/events`, `/api`.

### `app/schemas/events.py`
Pydantic v2 discriminated union:
```python
EventPayload = Annotated[Union[KillEvent, DamageEvent, FlashEvent, UtilityEvent,
    WeaponFireEvent, RoundEndEvent, MatchStartEvent, MatchEndEvent, PlayerConnectEvent],
    Field(discriminator="type")]
```
This is the canonical plugin-to-API contract.

### `app/routers/events.py` — fully wired
`POST /events` accepts `list[EventPayload]`. Routes each event type to a batch insert function. `match_end` events additionally call `match_tracker.end_match()`.

### `app/routers/players.py`, `matches.py`, `weapons.py`, `utility.py` — real route handlers
All endpoints use raw asyncpg queries for reads, typed Pydantic response models. Complex aggregations delegated to `services/stats.py` stubs.

### `app/services/stats.py` and `match_tracker.py` — stubbed
Full function signatures with docstrings, `# TODO` bodies. `match_tracker.end_match()` includes a `REFRESH MATERIALIZED VIEW CONCURRENTLY player_stats` call (this part is wired — it's one line of SQL).

### Supporting files
- `app/config.py` — `Settings` (pydantic-settings): `DATABASE_URL`, `API_SECRET`, `DEBUG`
- `app/database.py` — asyncpg pool, `get_connection()` async context manager

---

## 4. Dashboard (Next.js 14 App Router)

### `src/lib/api.ts`
Typed fetch helpers for every endpoint. All return types mirror FastAPI Pydantic schemas. Native `fetch`, no axios.

### Pages

| Route | Implementation |
|---|---|
| `/` | Leaderboard table, sortable by KD/ADR/HS%/wins — real, renders live data |
| `/players/[steamid]` | Stats grid real; Recharts trend charts `// TODO` |
| `/matches` | Paginated match list with map + score — real |
| `/matches/[id]` | Scoreboard real; `RoundTimeline` component `// TODO` |
| `/head-to-head` | Two-player layout real; comparison bars `// TODO` |
| `/weapons` | Server-wide weapon meta table — real |

### Components

| Component | Status |
|---|---|
| `Leaderboard.tsx` | Real implementation |
| `PlayerCard.tsx` | Real implementation |
| `MatchScoreboard.tsx` | Real implementation |
| `RoundTimeline.tsx` | Stub — `// TODO: implement with Recharts` |
| `StatChart.tsx` | Stub — `// TODO: implement with Recharts` |
| `WeaponBreakdown.tsx` | Stub — `// TODO: implement with Recharts` |

---

## 5. C# Plugin

### `plugin/Clutchboard.csproj`
Targets .NET 8. References `CounterStrikeSharp.API` NuGet package.

### `plugin/Clutchboard.cs`
Extends `BasePlugin`. `OnLoad` registers handlers and initializes `ApiClient`.

Registered event handlers:
- `EventPlayerDeath` → `KillEventDto` + `DamageEventDto`
- `EventPlayerHurt` → `DamageEventDto`
- `EventFlashbangDetonate` → `FlashEventDto`
- `EventSmokegrenadeDetonate`, `EventMolotovDetonate`, `EventHegrenadeDetonate`, `EventDecoyDetonate` → `UtilityEventDto`
- `EventWeaponFire` → `WeaponFireEventDto`
- `EventRoundEnd` → `RoundEndEventDto`
- `EventRoundStart` → start-of-round bookkeeping
- `EventGameEnd` → `MatchEndEventDto`
- `EventPlayerConnectFull` → `PlayerConnectEventDto`

All handlers: fire-and-forget (`_ = _apiClient.PostEventAsync(dto)`). No game thread blocking.

### `plugin/Models/`
One DTO per event type, matching Pydantic schemas exactly. Serialized via `System.Text.Json`.

### `plugin/Services/ApiClient.cs`
`HttpClient` with `BaseAddress` from config. Events queued in a `ConcurrentQueue<object>`, flushed to `POST /events` as a batch every 500ms on a background timer. All exceptions caught and logged — never throws.

### `plugin/config.json`
```json
{ "ApiUrl": "http://localhost:8000", "ApiSecret": "" }
```

---

## Out of Scope (Phase 2)

- KAST%, clutch detection, Elo/Glicko-2 rating
- Demo parsing pipeline
- Economy tracking
- Heatmaps and spray analysis
- Recharts visualizations (RoundTimeline, StatChart, WeaponBreakdown)
