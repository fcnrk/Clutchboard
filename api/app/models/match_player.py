import uuid

from sqlalchemy import UUID, BigInteger, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MatchPlayer(Base):
    __tablename__ = "match_players"
    __table_args__ = (UniqueConstraint("match_id", "steam_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    steam_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("players.steam_id"), nullable=False)
    team: Mapped[str] = mapped_column(Text, nullable=False)
    kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damage_dealt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    headshot_kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rounds_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    utility_damage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enemies_flashed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    team_flashes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clutch_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clutch_wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mvp_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
