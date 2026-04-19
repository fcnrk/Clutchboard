import uuid
from datetime import datetime, timezone

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.schemas.events import (
    EventPayload, KillEvent, DamageEvent, FlashEvent, UtilityEvent,
    WeaponFireEvent, RoundStartEvent, RoundEndEvent, MatchStartEvent, MatchEndEvent,
    PlayerConnectEvent,
)
from app.database import get_connection
from app.services.match_tracker import end_match
from app.config import settings

_api_key_header = APIKeyHeader(name="X-Api-Secret", auto_error=False)


async def verify_api_secret(key: str | None = Security(_api_key_header)) -> None:
    if settings.api_secret and key != settings.api_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


router = APIRouter(dependencies=[Depends(verify_api_secret)])


@router.post("/events", status_code=204)
async def ingest_events(events: list[EventPayload]) -> None:
    async with get_connection() as conn:
        for event in events:
            match event.type:
                case "player_connect":
                    await _player_connect(conn, event)
                case "match_start":
                    await _match_start(conn, event)
                case "round_start":
                    await _round_start(conn, event)
                case "round_end":
                    await _round_end(conn, event)
                case "kill":
                    await _kill(conn, event)
                case "damage":
                    await _damage(conn, event)
                case "flash":
                    await _flash(conn, event)
                case "utility":
                    await _utility(conn, event)
                case "weapon_fire":
                    await _weapon_fire(conn, event)
                case "match_end":
                    await _match_end(conn, event)


async def _player_connect(conn: asyncpg.Connection, e: PlayerConnectEvent) -> None:
    await conn.execute(
        """
        INSERT INTO players (steam_id, display_name, avatar_url)
        VALUES ($1, $2, $3)
        ON CONFLICT (steam_id) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                avatar_url   = COALESCE(EXCLUDED.avatar_url, players.avatar_url),
                updated_at   = now()
        """,
        e.steam_id, e.display_name, e.avatar_url,
    )


async def _match_start(conn: asyncpg.Connection, e: MatchStartEvent) -> None:
    started_at = datetime.fromisoformat(e.started_at.replace("Z", "+00:00"))
    await conn.execute(
        """
        INSERT INTO matches (id, map_name, started_at, status)
        VALUES ($1, $2, $3, 'live')
        ON CONFLICT (id) DO NOTHING
        """,
        uuid.UUID(e.match_id), e.map_name, started_at,
    )


async def _round_start(conn: asyncpg.Connection, e: RoundStartEvent) -> None:
    await conn.execute(
        """
        INSERT INTO rounds (match_id, round_number)
        VALUES ($1, $2)
        ON CONFLICT (match_id, round_number) DO NOTHING
        """,
        uuid.UUID(e.match_id), e.round_number,
    )


async def _round_end(conn: asyncpg.Connection, e: RoundEndEvent) -> None:
    await conn.execute(
        """
        INSERT INTO rounds (match_id, round_number, winner, win_reason, duration_seconds)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (match_id, round_number) DO NOTHING
        """,
        uuid.UUID(e.match_id), e.round_number, e.winner, e.win_reason, e.duration_seconds,
    )


async def _get_round_id(conn: asyncpg.Connection, match_id: str, round_number: int) -> int | None:
    return await conn.fetchval(
        "SELECT id FROM rounds WHERE match_id = $1 AND round_number = $2",
        uuid.UUID(match_id), round_number,
    )


async def _kill(conn: asyncpg.Connection, e: KillEvent) -> None:
    round_id = await _get_round_id(conn, e.match_id, e.round_number)
    if round_id is None:
        return
    await conn.execute(
        """
        INSERT INTO kills
            (match_id, round_id, killer_steam_id, victim_steam_id, assister_steam_id,
             weapon, headshot, penetrated, noscope, thrusmoke, attacker_blind)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
        uuid.UUID(e.match_id), round_id, e.killer_steam_id, e.victim_steam_id,
        e.assister_steam_id, e.weapon, e.headshot, e.penetrated,
        e.noscope, e.thrusmoke, e.attacker_blind,
    )


async def _damage(conn: asyncpg.Connection, e: DamageEvent) -> None:
    round_id = await _get_round_id(conn, e.match_id, e.round_number)
    if round_id is None:
        return
    await conn.execute(
        """
        INSERT INTO damage
            (match_id, round_id, attacker_steam_id, victim_steam_id,
             weapon, damage, damage_armor, hitgroup)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        uuid.UUID(e.match_id), round_id, e.attacker_steam_id, e.victim_steam_id,
        e.weapon, e.damage, e.damage_armor, e.hitgroup,
    )


async def _flash(conn: asyncpg.Connection, e: FlashEvent) -> None:
    round_id = await _get_round_id(conn, e.match_id, e.round_number)
    if round_id is None:
        return
    await conn.execute(
        """
        INSERT INTO flash_events
            (match_id, round_id, thrower_steam_id, blinded_steam_id, blind_duration, is_teammate)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        uuid.UUID(e.match_id), round_id, e.thrower_steam_id,
        e.blinded_steam_id, e.blind_duration, e.is_teammate,
    )


async def _utility(conn: asyncpg.Connection, e: UtilityEvent) -> None:
    round_id = await _get_round_id(conn, e.match_id, e.round_number)
    if round_id is None:
        return
    await conn.execute(
        """
        INSERT INTO utility_events (match_id, round_id, steam_id, event_type, damage)
        VALUES ($1, $2, $3, $4, $5)
        """,
        uuid.UUID(e.match_id), round_id, e.steam_id, e.event_type, e.damage,
    )


async def _weapon_fire(conn: asyncpg.Connection, e: WeaponFireEvent) -> None:
    round_id = await _get_round_id(conn, e.match_id, e.round_number)
    if round_id is None:
        return
    await conn.execute(
        "INSERT INTO weapon_fires (match_id, round_id, steam_id, weapon) VALUES ($1, $2, $3, $4)",
        uuid.UUID(e.match_id), round_id, e.steam_id, e.weapon,
    )


async def _match_end(conn: asyncpg.Connection, e: MatchEndEvent) -> None:
    match_id = uuid.UUID(e.match_id)
    await conn.execute(
        """
        UPDATE matches
        SET t_score = $2, ct_score = $3, duration_seconds = $4,
            status = 'completed', ended_at = now()
        WHERE id = $1
        """,
        match_id, e.t_score, e.ct_score, e.duration_seconds,
    )
    await end_match(conn, match_id, e.player_teams)
