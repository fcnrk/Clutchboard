import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, Integer, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Damage(Base):
    __tablename__ = "damage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    round_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    attacker_steam_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("players.steam_id"), nullable=True
    )
    victim_steam_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.steam_id"), nullable=False
    )
    weapon: Mapped[str] = mapped_column(Text, nullable=False)
    damage: Mapped[int] = mapped_column(Integer, nullable=False)
    damage_armor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hitgroup: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
