from fastapi import APIRouter

from app.database import get_connection
from app.schemas.stats import WeaponStats

router = APIRouter()


@router.get("/weapons", response_model=list[WeaponStats])
async def get_weapon_meta():
    """Server-wide weapon kill/accuracy stats across all matches."""
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                k.weapon,
                COUNT(*)              AS kills,
                SUM(k.headshot::int)  AS headshot_kills,
                COALESCE(wf.shots, 0) AS shots_fired
            FROM kills k
            LEFT JOIN (
                SELECT weapon, COUNT(*) AS shots
                FROM weapon_fires
                GROUP BY weapon
            ) wf ON wf.weapon = k.weapon
            GROUP BY k.weapon, wf.shots
            ORDER BY kills DESC
            """
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
