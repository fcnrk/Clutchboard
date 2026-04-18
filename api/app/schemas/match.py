import uuid
from datetime import datetime

from pydantic import BaseModel


class MatchListItem(BaseModel):
    id: uuid.UUID
    map_name: str
    started_at: datetime
    ended_at: datetime | None
    t_score: int
    ct_score: int
    status: str


class RoundSummary(BaseModel):
    round_number: int
    winner: str
    win_reason: str
    duration_seconds: int | None


class MatchScoreboardEntry(BaseModel):
    steam_id: int
    display_name: str
    real_name: str | None
    team: str
    kills: int
    deaths: int
    assists: int
    damage_dealt: int
    headshot_kills: int
    adr: float
    mvp_count: int


class MatchDetailResponse(BaseModel):
    id: uuid.UUID
    map_name: str
    started_at: datetime
    ended_at: datetime | None
    t_score: int
    ct_score: int
    status: str
    duration_seconds: int | None
    scoreboard: list[MatchScoreboardEntry]
    rounds: list[RoundSummary]
