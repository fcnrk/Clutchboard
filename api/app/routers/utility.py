from fastapi import APIRouter

from app.database import get_connection
from app.schemas.stats import UtilityStats

router = APIRouter()


@router.get("/players/{steam_id}/utility", response_model=UtilityStats)
async def get_player_utility(steam_id: int):
    async with get_connection() as conn:
        ue_row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'smoke_start')       AS smokes_thrown,
                COUNT(*) FILTER (WHERE event_type = 'molotov_detonate')  AS molotovs_thrown,
                COUNT(*) FILTER (WHERE event_type = 'he_detonate')       AS he_grenades_thrown,
                COALESCE(SUM(damage), 0)                                  AS utility_damage
            FROM utility_events WHERE steam_id = $1
            """,
            steam_id,
        )
        fe_row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE NOT is_teammate)                        AS enemies_flashed,
                COUNT(*) FILTER (WHERE is_teammate)                            AS team_flashes,
                COALESCE(AVG(blind_duration) FILTER (WHERE NOT is_teammate), 0.0) AS avg_flash_duration
            FROM flash_events WHERE thrower_steam_id = $1
            """,
            steam_id,
        )
        return UtilityStats(
            smokes_thrown=ue_row["smokes_thrown"] or 0,
            molotovs_thrown=ue_row["molotovs_thrown"] or 0,
            he_grenades_thrown=ue_row["he_grenades_thrown"] or 0,
            utility_damage=ue_row["utility_damage"] or 0,
            enemies_flashed=fe_row["enemies_flashed"] or 0,
            team_flashes=fe_row["team_flashes"] or 0,
            avg_flash_duration=float(fe_row["avg_flash_duration"] or 0.0),
        )
