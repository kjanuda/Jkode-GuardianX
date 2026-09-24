from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)

    device_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    current_cell_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "cells.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    software_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    antenna_type: Mapped[str | None] = mapped_column(
        String(50),
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

    customer: Mapped["Customer"] = relationship(
        back_populates="devices",
    )

    current_cell: Mapped["Cell | None"] = relationship(
        back_populates="devices",
    )

    sim: Mapped["SIM | None"] = relationship(
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
    )

    telemetry_records: Mapped[list["Telemetry"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )