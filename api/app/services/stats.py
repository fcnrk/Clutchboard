import uuid

import asyncpg


async def get_player_kast(
    conn: asyncpg.Connection, steam_id: int, match_id: uuid.UUID
) -> float:
    """
    KAST% — rounds where the player had a Kill, Assist, Survived, or was Traded.
    TODO: Implement. Requires per-round kill/death/survive tracking.
    """
    raise NotImplementedError


async def get_clutch_stats(conn: asyncpg.Connection, steam_id: int) -> dict:
    """
    Clutch win rates (1v1, 1v2, 1v3, 1v4).
    TODO: Implement. Requires tracking alive-player count per round at time of death.
    """
    raise NotImplementedError


async def get_opening_duel_rate(conn: asyncpg.Connection, steam_id: int) -> dict:
    """
    First-kill / first-death rate per round.
    TODO: Implement. Requires tick ordering within a round or first-event tracking.
    """
    raise NotImplementedError
