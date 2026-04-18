import uuid
from datetime import datetime

from sqlalchemy import UUID, BigInteger, Integer, Text, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Kill(Base):
    __tablename__ = "kills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    round_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False
    )
    killer_steam_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("players.steam_id"), nullable=True
    )
    victim_steam_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.steam_id"), nullable=False
    )
    assister_steam_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("players.steam_id"), nullable=True
    )
    weapon: Mapped[str] = mapped_column(Text, nullable=False)
    headshot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    penetrated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    noscope: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    thrusmoke: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attacker_blind: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
