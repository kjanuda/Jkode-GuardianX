from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(primary_key=True)

    device_id: Mapped[int] = mapped_column(
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    cell_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "cells.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # -------------------------
    # Scenario
    # -------------------------

    scenario: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    # -------------------------
    # Radio
    # -------------------------

    rsrp: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rsrq: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rssi: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    sinr: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    cqi: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    mcs: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # -------------------------
    # Network
    # -------------------------

    download_mbps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    upload_mbps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    jitter_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    packet_loss: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # -------------------------
    # Geo
    # -------------------------

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # -------------------------
    # Relationships
    # -------------------------

    device: Mapped["Device"] = relationship(
        back_populates="telemetry_records",
    )

    cell: Mapped["Cell | None"] = relationship(
        back_populates="telemetry_records",
    )