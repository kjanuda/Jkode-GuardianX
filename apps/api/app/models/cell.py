from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Cell(Base):
    __tablename__ = "cells"

    id: Mapped[int] = mapped_column(primary_key=True)

    cell_id: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False,
        index=True,
    )

    sector_id: Mapped[int] = mapped_column(
        ForeignKey(
            "sectors.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    technology: Mapped[str] = mapped_column(
        String(20),
        default="4G",
        nullable=False,
    )

    pci: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    earfcn: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    band: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    bandwidth_mhz: Mapped[float | None] = mapped_column(
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

    sector: Mapped["Sector"] = relationship(
        back_populates="cells",
    )

    devices: Mapped[list["Device"]] = relationship(
        back_populates="current_cell",
    )

    telemetry_records: Mapped[list["Telemetry"]] = relationship(
        back_populates="cell",
    )