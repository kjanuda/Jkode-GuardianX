from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class DeviceProfile(Base):
    __tablename__ = "device_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
        index=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )

    os_name: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    os_version: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    firmware_version: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )

    modem_version: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
        onupdate=utc_now,
    )