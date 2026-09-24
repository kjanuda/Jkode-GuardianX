from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(128),
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20)
    )

    risk_score: Mapped[float] = mapped_column(
        Float
    )

    primary_cause: Mapped[str] = mapped_column(
        String(100)
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    summary: Mapped[str] = mapped_column(
        Text
    )

    occurrence_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=lambda:
            datetime.now(
                timezone.utc
            ),
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=lambda:
            datetime.now(
                timezone.utc
            ),
    )

    resolved_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )