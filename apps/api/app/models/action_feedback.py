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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class ActionFeedback(Base):
    __tablename__ = "action_feedback"

    __table_args__ = (
        UniqueConstraint(
            "action_plan_id",
            "revision",
            name="uq_action_feedback_plan_revision",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    feedback_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(
            uuid4()
        ),
    )

    # -------------------------------------------------
    # TRACEABILITY
    # -------------------------------------------------

    action_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "action_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    rca_case_id: Mapped[int] = mapped_column(
        ForeignKey(
            "rca_cases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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

    verification_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "action_verifications.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    revision: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    # -------------------------------------------------
    # HUMAN FEEDBACK
    # -------------------------------------------------

    reviewer: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    feedback_status: Mapped[str] = mapped_column(
        String(30),
        default="DRAFT",
        index=True,
    )

    diagnosis_assessment: Mapped[str] = mapped_column(
        String(30),
        default="UNREVIEWED",
        index=True,
    )

    action_assessment: Mapped[str] = mapped_column(
        String(30),
        default="UNREVIEWED",
        index=True,
    )

    resolution_status: Mapped[str] = mapped_column(
        String(30),
        default="UNKNOWN",
        index=True,
    )

    operator_confidence: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    actual_root_cause: Mapped[
        str | None
    ] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )

    actual_resolution: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # -------------------------------------------------
    # EVIDENCE / PROVENANCE
    # -------------------------------------------------

    evidence_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    provenance_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    # -------------------------------------------------
    # LEARNING SAFETY
    # -------------------------------------------------

    quality_gate_status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
    )

    training_eligible: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    schema_version: Mapped[str] = mapped_column(
        String(50),
        default="ACTION_FEEDBACK_V1",
    )

    # -------------------------------------------------
    # AUDIT TIMES
    # -------------------------------------------------

    reviewed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    submitted_at: Mapped[
        datetime | None
    ] = mapped_column(
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
