from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(primary_key=True)

    sector_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    tower_id: Mapped[int] = mapped_column(
        ForeignKey(
            "towers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    azimuth_deg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    electrical_tilt_deg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    mechanical_tilt_deg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tower: Mapped["Tower"] = relationship(
        back_populates="sectors",
    )

    cells: Mapped[list["Cell"]] = relationship(
        back_populates="sector",
        cascade="all, delete-orphan",
    )