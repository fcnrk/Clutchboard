from pydantic import BaseModel


class PlayerResponse(BaseModel):
    steam_id: int
    display_name: str
    real_name: str | None
    avatar_url: str | None


class PlayerStatsResponse(BaseModel):
    steam_id: int
    display_name: str
    real_name: str | None
    avatar_url: str | None
    total_matches: int
    total_kills: int
    total_deaths: int
    total_assists: int
    total_damage: int
    total_rounds: int
    total_wins: int
    kd_ratio: float
    adr: float
    hs_pct: float
    win_rate: float
    first_kills_total: int
    utility_damage_total: int
