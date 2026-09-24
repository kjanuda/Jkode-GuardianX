from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class RCACase(Base):
    __tablename__ = "rca_cases"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    case_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(
            uuid4()
        ),
    )

    device_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    alert_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "alerts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    scope_type: Mapped[str] = mapped_column(
        String(30),
        default="DEVICE",
        index=True,
    )

    scope_ref: Mapped[str] = mapped_column(
        String(120),
        index=True,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
        default="MANUAL_SNAPSHOT",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN",
        index=True,
    )

    risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_level: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    baseline_primary_cause: Mapped[
        str | None
    ] = mapped_column(
        String(120),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
        onupdate=utc_now,
    )


class RCAEvidence(Base):
    __tablename__ = "rca_evidence"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "rca_cases.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    evidence_key: Mapped[str] = mapped_column(
        String(120),
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(80),
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    metric: Mapped[str] = mapped_column(
        String(100),
        index=True,
    )

    value_json: Mapped[dict] = mapped_column(
        JSONB
    )

    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    supports_causes: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    contradicts_causes: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    support_score: Mapped[
        float
    ] = mapped_column(
        Float,
        default=0.0,
    )

    reliability_score: Mapped[
        float
    ] = mapped_column(
        Float,
        default=1.0,
    )

    freshness_score: Mapped[
        float
    ] = mapped_column(
        Float,
        default=1.0,
    )

    specificity_score: Mapped[
        float
    ] = mapped_column(
        Float,
        default=0.5,
    )

    gate_passed: Mapped[
        bool | None
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    observed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    context_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
    )


class RCAPrediction(Base):
    __tablename__ = "rca_predictions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "rca_cases.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    engine_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    primary_cause: Mapped[
        str | None
    ] = mapped_column(
        String(120),
        nullable=True,
    )

    confidence: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    rank: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    output_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    verifier_status: Mapped[
        str | None
    ] = mapped_column(
        String(40),
        nullable=True,
    )

    verifier_reason: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True
        ),
        default=utc_now,
    )