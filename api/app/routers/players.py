import uuid

from fastapi import APIRouter, HTTPException, Query

from app.database import get_connection
from app.schemas.player import PlayerStatsResponse
from app.schemas.match import MatchListItem
from app.schemas.stats import WeaponStats, HeadToHeadResponse, TrendPoint

router = APIRouter()

_SORT_COLUMNS = {
    "kd_ratio": "kd_ratio",
    "adr": "adr",
    "hs_pct": "hs_pct",
    "total_wins": "total_wins",
    "total_kills": "total_kills",
}


@router.get("/players", response_model=list[PlayerStatsResponse])
async def get_leaderboard(
    sort_by: str = Query(
        "kd_ratio",
        enum=list(_SORT_COLUMNS.keys()),
    ),
):
    col = _SORT_COLUMNS[sort_by]
    async with get_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT steam_id, display_name, real_name, avatar_url, total_matches,
                   total_kills, total_deaths, total_assists, total_damage, total_rounds,
                   total_wins, kd_ratio, adr, hs_pct, win_rate,
                   first_kills_total, utility_damage_total
            FROM player_stats
            ORDER BY {col} DESC NULLS LAST
            """
        )
        return [PlayerStatsResponse(**dict(r)) for r in rows]


@router.get("/players/{steam_id}", response_model=PlayerStatsResponse)
async def get_player(steam_id: int):
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT steam_id, display_name, real_name, avatar_url, total_matches,
                   total_kills, total_deaths, total_assists, total_damage, total_rounds,
                   total_wins, kd_ratio, adr, hs_pct, win_rate,
                   first_kills_total, utility_damage_total
            FROM player_stats WHERE steam_id = $1
            """,
            steam_id,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Player not found")
        return PlayerStatsResponse(**dict(row))


@router.get("/players/{steam_id}/matches", response_model=list[MatchListItem])
async def get_player_matches(steam_id: int, limit: int = Query(20, le=100)):
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT m.id, m.map_name, m.started_at, m.ended_at, m.t_score, m.ct_score, m.status
            FROM matches m
            JOIN match_players mp ON mp.match_id = m.id
            WHERE mp.steam_id = $1
            ORDER BY m.started_at DESC
            LIMIT $2
            """,
            steam_id, limit,
        )
        return [MatchListItem(**dict(r)) for r in rows]


@router.get("/players/{steam_id}/weapons", response_model=list[WeaponStats])
async def get_player_weapons(steam_id: int):
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                k.weapon,
                COUNT(*)                   AS kills,
                SUM(k.headshot::int)       AS headshot_kills,
                COALESCE(wf.shots, 0)      AS shots_fired
            FROM kills k
            LEFT JOIN (
                SELECT weapon, COUNT(*) AS shots
                FROM weapon_fires
                WHERE steam_id = $1
                GROUP BY weapon
            ) wf ON wf.weapon = k.weapon
            WHERE k.killer_steam_id = $1
            GROUP BY k.weapon, wf.shots
            ORDER BY kills DESC
            """,
            steam_id,
        )
        result = []
        for r in rows:
            kills = r["kills"]
            hs = r["headshot_kills"] or 0
            shots = r["shots_fired"] or 0
            result.append(WeaponStats(
                weapon=r["weapon"],
                kills=kills,
                headshot_kills=hs,
                shots_fired=shots,
                hs_pct=round(hs / kills * 100, 1) if kills else 0.0,
                accuracy=round(kills / shots * 100, 1) if shots else 0.0,
            ))
        return result


@router.get("/players/{steam_id}/trends", response_model=list[TrendPoint])
async def get_player_trends(steam_id: int, n: int = Query(10, ge=1, le=20)):
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                m.id::text                                                              AS match_id,
                m.map_name,
                m.started_at,
                mp.kills,
                mp.deaths,
                CASE WHEN mp.deaths = 0 THEN mp.kills::float
                     ELSE ROUND(mp.kills::numeric / mp.deaths, 2)::float
                END                                                                    AS kd_ratio,
                CASE WHEN mp.rounds_played = 0 THEN 0.0
                     ELSE ROUND(mp.damage_dealt::numeric / mp.rounds_played, 1)::float
                END                                                                    AS adr,
                CASE WHEN mp.kills = 0 THEN 0.0
                     ELSE ROUND(mp.headshot_kills::numeric / mp.kills * 100, 1)::float
                END                                                                    AS hs_pct
            FROM match_players mp
            JOIN matches m ON m.id = mp.match_id
            WHERE mp.steam_id = $1
            ORDER BY m.started_at DESC
            LIMIT $2
            """,
            steam_id, n,
        )
        return [TrendPoint(**dict(r)) for r in rows]


@router.get("/head-to-head", response_model=HeadToHeadResponse)
async def get_head_to_head(
    p1: int = Query(..., description="Steam ID of player 1"),
    p2: int = Query(..., description="Steam ID of player 2"),
):
    async with get_connection() as conn:
        p1_row = await conn.fetchrow("SELECT * FROM player_stats WHERE steam_id = $1", p1)
        p2_row = await conn.fetchrow("SELECT * FROM player_stats WHERE steam_id = $1", p2)
        if p1_row is None or p2_row is None:
            raise HTTPException(status_code=404, detail="One or both players not found")

        p1_kills = await conn.fetchval(
            "SELECT COUNT(*) FROM kills WHERE killer_steam_id = $1 AND victim_steam_id = $2", p1, p2
        )
        p2_kills = await conn.fetchval(
            "SELECT COUNT(*) FROM kills WHERE killer_steam_id = $1 AND victim_steam_id = $2", p2, p1
        )

        return HeadToHeadResponse(
            player1_steam_id=p1,
            player2_steam_id=p2,
            player1_kills_on_player2=p1_kills or 0,
            player2_kills_on_player1=p2_kills or 0,
            player1_stats=PlayerStatsResponse(**dict(p1_row)),
            player2_stats=PlayerStatsResponse(**dict(p2_row)),
        )
