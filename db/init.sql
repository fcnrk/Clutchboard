-- WARNING: Derived from Alembic migration 0001_initial.
-- Do NOT edit directly — update the migration and regenerate this file.
-- Used by docker-compose to bootstrap postgres on first run.

CREATE TABLE IF NOT EXISTS players (
    steam_id    BIGINT PRIMARY KEY,
    display_name TEXT NOT NULL,
    real_name   TEXT,
    avatar_url  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS matches (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    map_name         TEXT NOT NULL,
    started_at       TIMESTAMPTZ NOT NULL,
    ended_at         TIMESTAMPTZ,
    t_score          INT NOT NULL DEFAULT 0,
    ct_score         INT NOT NULL DEFAULT 0,
    duration_seconds INT,
    status           TEXT NOT NULL DEFAULT 'live',
    demo_path        TEXT
);

CREATE TABLE IF NOT EXISTS match_players (
    id              SERIAL PRIMARY KEY,
    match_id        UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    steam_id        BIGINT NOT NULL REFERENCES players(steam_id),
    team            TEXT NOT NULL,
    kills           INT NOT NULL DEFAULT 0,
    deaths          INT NOT NULL DEFAULT 0,
    assists         INT NOT NULL DEFAULT 0,
    damage_dealt    INT NOT NULL DEFAULT 0,
    headshot_kills  INT NOT NULL DEFAULT 0,
    rounds_played   INT NOT NULL DEFAULT 0,
    first_kills     INT NOT NULL DEFAULT 0,
    first_deaths    INT NOT NULL DEFAULT 0,
    utility_damage  INT NOT NULL DEFAULT 0,
    enemies_flashed INT NOT NULL DEFAULT 0,
    team_flashes    INT NOT NULL DEFAULT 0,
    clutch_attempts INT NOT NULL DEFAULT 0,
    clutch_wins     INT NOT NULL DEFAULT 0,
    mvp_count       INT NOT NULL DEFAULT 0,
    UNIQUE (match_id, steam_id)
);

CREATE TABLE IF NOT EXISTS rounds (
    id               SERIAL PRIMARY KEY,
    match_id         UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    round_number     INT NOT NULL,
    winner           TEXT,
    win_reason       TEXT,
    duration_seconds INT,
    UNIQUE (match_id, round_number)
);

CREATE TABLE IF NOT EXISTS kills (
    id                SERIAL PRIMARY KEY,
    match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    round_id          INT  NOT NULL REFERENCES rounds(id)  ON DELETE CASCADE,
    killer_steam_id   BIGINT REFERENCES players(steam_id),
    victim_steam_id   BIGINT NOT NULL REFERENCES players(steam_id),
    assister_steam_id BIGINT REFERENCES players(steam_id),
    weapon            TEXT NOT NULL,
    headshot          BOOLEAN NOT NULL DEFAULT false,
    penetrated        BOOLEAN NOT NULL DEFAULT false,
    noscope           BOOLEAN NOT NULL DEFAULT false,
    thrusmoke         BOOLEAN NOT NULL DEFAULT false,
    attacker_blind    BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS damage (
    id                  SERIAL PRIMARY KEY,
    match_id            UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    round_id            INT  NOT NULL REFERENCES rounds(id)  ON DELETE CASCADE,
    attacker_steam_id   BIGINT REFERENCES players(steam_id),
    victim_steam_id     BIGINT NOT NULL REFERENCES players(steam_id),
    weapon              TEXT NOT NULL,
    damage              INT  NOT NULL,
    damage_armor        INT  NOT NULL DEFAULT 0,
    hitgroup            TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS utility_events (
    id         SERIAL PRIMARY KEY,
    match_id   UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    round_id   INT  NOT NULL REFERENCES rounds(id)  ON DELETE CASCADE,
    steam_id   BIGINT REFERENCES players(steam_id),
    event_type TEXT NOT NULL,
    damage     INT  NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS flash_events (
    id                SERIAL PRIMARY KEY,
    match_id          UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    round_id          INT  NOT NULL REFERENCES rounds(id)  ON DELETE CASCADE,
    thrower_steam_id  BIGINT REFERENCES players(steam_id),
    blinded_steam_id  BIGINT REFERENCES players(steam_id),
    blind_duration    FLOAT NOT NULL,
    is_teammate       BOOLEAN NOT NULL DEFAULT false,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS weapon_fires (
    id         SERIAL PRIMARY KEY,
    match_id   UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    round_id   INT  NOT NULL REFERENCES rounds(id)  ON DELETE CASCADE,
    steam_id   BIGINT REFERENCES players(steam_id),
    weapon     TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS ix_kills_match_id            ON kills (match_id);
CREATE INDEX IF NOT EXISTS ix_kills_match_round         ON kills (match_id, round_id);
CREATE INDEX IF NOT EXISTS ix_kills_killer              ON kills (killer_steam_id);
CREATE INDEX IF NOT EXISTS ix_kills_victim              ON kills (victim_steam_id);
CREATE INDEX IF NOT EXISTS ix_damage_match_id           ON damage (match_id);
CREATE INDEX IF NOT EXISTS ix_damage_match_round        ON damage (match_id, round_id);
CREATE INDEX IF NOT EXISTS ix_weapon_fires_match_id     ON weapon_fires (match_id);
CREATE INDEX IF NOT EXISTS ix_weapon_fires_msw          ON weapon_fires (match_id, steam_id, weapon);
CREATE INDEX IF NOT EXISTS ix_flash_events_match_id     ON flash_events (match_id);
CREATE INDEX IF NOT EXISTS ix_flash_events_match_steam  ON flash_events (match_id, thrower_steam_id);
CREATE INDEX IF NOT EXISTS ix_utility_events_match_id   ON utility_events (match_id);
CREATE INDEX IF NOT EXISTS ix_utility_events_match_steam ON utility_events (match_id, steam_id);
CREATE INDEX IF NOT EXISTS ix_rounds_match_id           ON rounds (match_id);

-- Materialized view for leaderboard (refreshed after each match via match_tracker.end_match)
CREATE MATERIALIZED VIEW IF NOT EXISTS player_stats AS
SELECT
    p.steam_id,
    p.display_name,
    p.real_name,
    p.avatar_url,
    COUNT(DISTINCT mp.match_id)                                                    AS total_matches,
    COALESCE(SUM(mp.kills), 0)                                                     AS total_kills,
    COALESCE(SUM(mp.deaths), 0)                                                    AS total_deaths,
    COALESCE(SUM(mp.assists), 0)                                                   AS total_assists,
    COALESCE(SUM(mp.damage_dealt), 0)                                              AS total_damage,
    COALESCE(SUM(mp.rounds_played), 0)                                             AS total_rounds,
    COALESCE(SUM(CASE
        WHEN m.status = 'completed'
         AND ((mp.team = 'T' AND m.t_score > m.ct_score)
          OR  (mp.team = 'CT' AND m.ct_score > m.t_score))
        THEN 1 ELSE 0 END), 0)                                                     AS total_wins,
    CASE WHEN COALESCE(SUM(mp.deaths), 0) = 0
         THEN COALESCE(SUM(mp.kills), 0)::float
         ELSE ROUND(COALESCE(SUM(mp.kills), 0)::numeric / NULLIF(SUM(mp.deaths), 0), 2)::float
    END                                                                            AS kd_ratio,
    CASE WHEN COALESCE(SUM(mp.rounds_played), 0) = 0 THEN 0.0
         ELSE ROUND(COALESCE(SUM(mp.damage_dealt), 0)::numeric / NULLIF(SUM(mp.rounds_played), 0), 1)::float
    END                                                                            AS adr,
    CASE WHEN COALESCE(SUM(mp.kills), 0) = 0 THEN 0.0
         ELSE ROUND(COALESCE(SUM(mp.headshot_kills), 0)::numeric / NULLIF(SUM(mp.kills), 0) * 100, 1)::float
    END                                                                            AS hs_pct,
    CASE WHEN COUNT(DISTINCT mp.match_id) = 0 THEN 0.0
         ELSE ROUND(
             COALESCE(SUM(CASE
                 WHEN m.status = 'completed'
                  AND ((mp.team = 'T' AND m.t_score > m.ct_score)
                   OR  (mp.team = 'CT' AND m.ct_score > m.t_score))
                 THEN 1 ELSE 0 END), 0)::numeric
             / NULLIF(COUNT(DISTINCT mp.match_id), 0) * 100, 1
         )::float
    END                                                                            AS win_rate,
    COALESCE(SUM(mp.first_kills), 0)                                               AS first_kills_total,
    COALESCE(SUM(mp.utility_damage), 0)                                            AS utility_damage_total
FROM players p
LEFT JOIN match_players mp ON mp.steam_id = p.steam_id
LEFT JOIN matches m ON m.id = mp.match_id
GROUP BY p.steam_id, p.display_name, p.real_name, p.avatar_url
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS ix_player_stats_steam_id ON player_stats (steam_id);
