"""add alert lifecycle fields

Revision ID: 57b82e89c122
Revises: 8e76c2fd3407
Create Date: 2026-09-25 16:07:00.231092
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "57b82e89c122"
down_revision: Union[str, Sequence[str], None] = "8e76c2fd3407"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "mitigation_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "reopened_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "alerts",
        sa.Column(
            "reopened_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.alter_column(
        "alerts",
        "reopened_count",
        existing_type=sa.Integer(),
        server_default=None,
    )

    op.add_column(
        "alerts",
        sa.Column(
            "status_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE alerts
            SET status_updated_at =
                COALESCE(
                    last_seen_at,
                    first_seen_at,
                    CURRENT_TIMESTAMP
                )
            WHERE status_updated_at IS NULL
            """
        )
    )

    op.alter_column(
        "alerts",
        "status_updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column(
        "alerts",
        "status_updated_at",
    )

    op.drop_column(
        "alerts",
        "reopened_count",
    )

    op.drop_column(
        "alerts",
        "reopened_at",
    )

    op.drop_column(
        "alerts",
        "mitigation_started_at",
    )

    op.drop_column(
        "alerts",
        "acknowledged_at",
    )
