from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActionSimulation(Base):
    __tablename__ = "action_simulations"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    simulation_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
    )

    action_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "action_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    attempt: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        index=True,
    )

    simulation_mode: Mapped[str] = mapped_column(
        String(30),
        default="DRY_RUN",
        index=True,
    )

    simulator_version: Mapped[str] = mapped_column(
        String(50),
        default="ACTION_SIMULATOR_V1",
    )

    schema_version: Mapped[str] = mapped_column(
        String(50),
        default="ACTION_SIMULATION_V1",
    )

    # Snapshot of the action that was simulated.
    input_snapshot_json: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    # Deterministic checks performed by simulator.
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

    verification_ready: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    rollback_ready: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    execution_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
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
