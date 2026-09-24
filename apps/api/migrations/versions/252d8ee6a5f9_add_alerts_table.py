"""add alerts table

Revision ID: 252d8ee6a5f9
Revises: c8dcec1d3662
Create Date: 2026-09-23 19:52:18.788851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "252d8ee6a5f9"
down_revision: Union[str, Sequence[str], None] = "c8dcec1d3662"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "alerts",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "fingerprint",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "risk_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "primary_cause",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_alerts_device_id"),
        "alerts",
        ["device_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_alerts_fingerprint"),
        "alerts",
        ["fingerprint"],
        unique=False,
    )

    op.create_index(
        op.f("ix_alerts_status"),
        "alerts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_alerts_status"),
        table_name="alerts",
    )

    op.drop_index(
        op.f("ix_alerts_fingerprint"),
        table_name="alerts",
    )

    op.drop_index(
        op.f("ix_alerts_device_id"),
        table_name="alerts",
    )

    op.drop_table("alerts")