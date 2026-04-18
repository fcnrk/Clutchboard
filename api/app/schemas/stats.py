from datetime import datetime

from pydantic import BaseModel

from app.schemas.player import PlayerStatsResponse


class TrendPoint(BaseModel):
    match_id: str
    map_name: str
    started_at: datetime
    kills: int
    deaths: int
    kd_ratio: float
    adr: float
    hs_pct: float


class WeaponStats(BaseModel):
    weapon: str
    kills: int
    headshot_kills: int
    shots_fired: int
    hs_pct: float
    accuracy: float


class UtilityStats(BaseModel):
    smokes_thrown: int
    molotovs_thrown: int
    he_grenades_thrown: int
    utility_damage: int
    enemies_flashed: int
    team_flashes: int
    avg_flash_duration: float


class HeadToHeadResponse(BaseModel):
    player1_steam_id: int
    player2_steam_id: int
    player1_kills_on_player2: int
    player2_kills_on_player1: int
    player1_stats: PlayerStatsResponse
    player2_stats: PlayerStatsResponse
