from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActionVerification(Base):
    __tablename__ = "action_verifications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    verification_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )

    simulation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "action_simulations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
    )

    verification_type: Mapped[str] = mapped_column(
        String(50),
        default="SIMULATION_INTEGRITY",
    )

    verifier_version: Mapped[str] = mapped_column(
        String(50),
        default="ACTION_VERIFIER_V1",
    )

    schema_version: Mapped[str] = mapped_column(
        String(50),
        default="ACTION_VERIFICATION_V1",
    )

    checks_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    result_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    failure_reasons_json: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    rollback_decision: Mapped[str] = mapped_column(
        String(50),
        default="NOT_EVALUATED",
        index=True,
    )

    execution_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
