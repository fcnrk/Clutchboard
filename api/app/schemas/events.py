from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class KillEvent(BaseModel):
    type: Literal["kill"]
    match_id: str
    round_number: int
    killer_steam_id: int | None = None
    victim_steam_id: int
    assister_steam_id: int | None = None
    weapon: str
    headshot: bool = False
    penetrated: bool = False
    noscope: bool = False
    thrusmoke: bool = False
    attacker_blind: bool = False


class DamageEvent(BaseModel):
    type: Literal["damage"]
    match_id: str
    round_number: int
    attacker_steam_id: int | None = None
    victim_steam_id: int
    weapon: str
    damage: int
    damage_armor: int = 0
    hitgroup: str


class FlashEvent(BaseModel):
    type: Literal["flash"]
    match_id: str
    round_number: int
    thrower_steam_id: int | None = None
    blinded_steam_id: int | None = None
    blind_duration: float
    is_teammate: bool = False


class UtilityEvent(BaseModel):
    type: Literal["utility"]
    match_id: str
    round_number: int
    steam_id: int | None = None
    event_type: str  # smoke_start | molotov_detonate | he_detonate | decoy_detonate
    damage: int = 0


class WeaponFireEvent(BaseModel):
    type: Literal["weapon_fire"]
    match_id: str
    round_number: int
    steam_id: int | None = None
    weapon: str


class RoundEndEvent(BaseModel):
    type: Literal["round_end"]
    match_id: str
    round_number: int
    winner: str  # T | CT
    win_reason: str  # elimination | bomb_defused | bomb_exploded | time_expired
    duration_seconds: int | None = None


class MatchStartEvent(BaseModel):
    type: Literal["match_start"]
    match_id: str
    map_name: str
    started_at: str  # ISO 8601 UTC


class MatchEndEvent(BaseModel):
    type: Literal["match_end"]
    match_id: str
    t_score: int
    ct_score: int
    duration_seconds: int | None = None
    player_teams: dict[str, str] = {}  # steam_id (str) → "T" | "CT"


class PlayerConnectEvent(BaseModel):
    type: Literal["player_connect"]
    steam_id: int
    display_name: str
    avatar_url: str | None = None


EventPayload = Annotated[
    Union[
        KillEvent,
        DamageEvent,
        FlashEvent,
        UtilityEvent,
        WeaponFireEvent,
        RoundEndEvent,
        MatchStartEvent,
        MatchEndEvent,
        PlayerConnectEvent,
    ],
    Field(discriminator="type"),
]
