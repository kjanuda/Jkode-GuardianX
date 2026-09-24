"""add telemetry scenario label

Revision ID: c8dcec1d3662
Revises: febd43e70f23
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8dcec1d3662"
down_revision: Union[str, Sequence[str], None] = "febd43e70f23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "telemetry",
        sa.Column(
            "scenario",
            sa.String(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_telemetry_scenario",
        "telemetry",
        ["scenario"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_telemetry_scenario",
        table_name="telemetry",
    )

    op.drop_column(
        "telemetry",
        "scenario",
    )