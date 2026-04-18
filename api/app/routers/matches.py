import uuid

from fastapi import APIRouter, HTTPException, Query

from app.database import get_connection
from app.schemas.match import MatchListItem, MatchDetailResponse, MatchScoreboardEntry, RoundSummary

router = APIRouter()


@router.get("/matches", response_model=list[MatchListItem])
async def get_matches(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
):
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT id, map_name, started_at, ended_at, t_score, ct_score, status
            FROM matches
            ORDER BY started_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )
        return [MatchListItem(**dict(r)) for r in rows]


@router.get("/matches/{match_id}", response_model=MatchDetailResponse)
async def get_match(match_id: uuid.UUID):
    async with get_connection() as conn:
        match_row = await conn.fetchrow(
            """
            SELECT id, map_name, started_at, ended_at, t_score, ct_score,
                   status, duration_seconds
            FROM matches WHERE id = $1
            """,
            match_id,
        )
        if match_row is None:
            raise HTTPException(status_code=404, detail="Match not found")

        scoreboard_rows = await conn.fetch(
            """
            SELECT
                mp.steam_id,
                p.display_name,
                p.real_name,
                mp.team,
                mp.kills,
                mp.deaths,
                mp.assists,
                mp.damage_dealt,
                mp.headshot_kills,
                mp.mvp_count,
                CASE WHEN mp.rounds_played = 0 THEN 0.0
                     ELSE ROUND(mp.damage_dealt::numeric / mp.rounds_played, 1)::float
                END AS adr
            FROM match_players mp
            JOIN players p ON p.steam_id = mp.steam_id
            WHERE mp.match_id = $1
            ORDER BY mp.kills DESC
            """,
            match_id,
        )

        round_rows = await conn.fetch(
            """
            SELECT round_number, winner, win_reason, duration_seconds
            FROM rounds WHERE match_id = $1 ORDER BY round_number
            """,
            match_id,
        )

        return MatchDetailResponse(
            **dict(match_row),
            scoreboard=[MatchScoreboardEntry(**dict(r)) for r in scoreboard_rows],
            rounds=[RoundSummary(**dict(r)) for r in round_rows],
        )
