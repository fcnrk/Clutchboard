import uuid

import asyncpg


async def end_match(
    conn: asyncpg.Connection,
    match_id: uuid.UUID,
    player_teams: dict[str, str],
) -> None:
    if player_teams:
        player_teams = {sid: team for sid, team in player_teams.items() if sid != "0"}
        steam_ids = list(player_teams.keys())
        teams = [player_teams[sid] for sid in steam_ids]
        async with conn.transaction():
            rows = await conn.fetch(
                """
                WITH
                kills_agg AS (
                    SELECT killer_steam_id AS steam_id,
                           COUNT(*)                        AS kills,
                           COUNT(*) FILTER (WHERE headshot) AS headshot_kills
                    FROM kills WHERE match_id = $1 AND killer_steam_id IS NOT NULL
                    GROUP BY killer_steam_id
                ),
                deaths_agg AS (
                    SELECT victim_steam_id AS steam_id, COUNT(*) AS deaths
                    FROM kills WHERE match_id = $1
                    GROUP BY victim_steam_id
                ),
                assists_agg AS (
                    SELECT assister_steam_id AS steam_id, COUNT(*) AS assists
                    FROM kills WHERE match_id = $1 AND assister_steam_id IS NOT NULL
                    GROUP BY assister_steam_id
                ),
                damage_agg AS (
                    SELECT attacker_steam_id AS steam_id,
                           COALESCE(SUM(damage), 0) AS damage_dealt
                    FROM damage WHERE match_id = $1 AND attacker_steam_id IS NOT NULL
                    GROUP BY attacker_steam_id
                ),
                utility_agg AS (
                    SELECT steam_id, COALESCE(SUM(damage), 0) AS utility_damage
                    FROM utility_events WHERE match_id = $1 AND steam_id IS NOT NULL
                    GROUP BY steam_id
                ),
                flash_agg AS (
                    SELECT thrower_steam_id AS steam_id,
                           COUNT(*) FILTER (WHERE NOT is_teammate) AS enemies_flashed,
                           COUNT(*) FILTER (WHERE is_teammate)     AS team_flashes
                    FROM flash_events WHERE match_id = $1 AND thrower_steam_id IS NOT NULL
                    GROUP BY thrower_steam_id
                ),
                rounds_count AS (SELECT COUNT(*) AS total FROM rounds WHERE match_id = $1)
                SELECT
                    p.steam_id::bigint,
                    p.team,
                    COALESCE(ka.kills, 0)            AS kills,
                    COALESCE(da.deaths, 0)           AS deaths,
                    COALESCE(aa.assists, 0)          AS assists,
                    COALESCE(ka.headshot_kills, 0)   AS headshot_kills,
                    COALESCE(dma.damage_dealt, 0)    AS damage_dealt,
                    (SELECT total FROM rounds_count)::int AS rounds_played,
                    COALESCE(ua.utility_damage, 0)   AS utility_damage,
                    COALESCE(fa.enemies_flashed, 0)  AS enemies_flashed,
                    COALESCE(fa.team_flashes, 0)     AS team_flashes
                FROM unnest($2::text[], $3::text[]) AS p(steam_id, team)
                LEFT JOIN kills_agg   ka  ON ka.steam_id  = p.steam_id::bigint
                LEFT JOIN deaths_agg  da  ON da.steam_id  = p.steam_id::bigint
                LEFT JOIN assists_agg aa  ON aa.steam_id  = p.steam_id::bigint
                LEFT JOIN damage_agg  dma ON dma.steam_id = p.steam_id::bigint
                LEFT JOIN utility_agg ua  ON ua.steam_id  = p.steam_id::bigint
                LEFT JOIN flash_agg   fa  ON fa.steam_id  = p.steam_id::bigint
                """,
                match_id, steam_ids, teams,
            )
            await conn.executemany(
                """
                INSERT INTO match_players
                    (match_id, steam_id, team, kills, deaths, assists, headshot_kills,
                     damage_dealt, rounds_played, utility_damage, enemies_flashed, team_flashes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (match_id, steam_id) DO UPDATE SET
                    team            = EXCLUDED.team,
                    kills           = EXCLUDED.kills,
                    deaths          = EXCLUDED.deaths,
                    assists         = EXCLUDED.assists,
                    headshot_kills  = EXCLUDED.headshot_kills,
                    damage_dealt    = EXCLUDED.damage_dealt,
                    rounds_played   = EXCLUDED.rounds_played,
                    utility_damage  = EXCLUDED.utility_damage,
                    enemies_flashed = EXCLUDED.enemies_flashed,
                    team_flashes    = EXCLUDED.team_flashes
                """,
                [
                    (
                        match_id,
                        row["steam_id"],
                        row["team"],
                        row["kills"],
                        row["deaths"],
                        row["assists"],
                        row["headshot_kills"],
                        row["damage_dealt"],
                        row["rounds_played"],
                        row["utility_damage"],
                        row["enemies_flashed"],
                        row["team_flashes"],
                    )
                    for row in rows
                ],
            )

    await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY player_stats")
