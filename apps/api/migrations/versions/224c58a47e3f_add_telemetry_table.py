"""add telemetry table

Revision ID: 224c58a47e3f
Revises: 607468bebeef
Create Date: 2026-09-22 21:03:11.303299

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "224c58a47e3f"
down_revision: Union[str, Sequence[str], None] = "607468bebeef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "telemetry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("cell_id", sa.Integer(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("rsrp", sa.Float(), nullable=True),
        sa.Column("rsrq", sa.Float(), nullable=True),
        sa.Column("rssi", sa.Float(), nullable=True),
        sa.Column("sinr", sa.Float(), nullable=True),
        sa.Column("cqi", sa.Integer(), nullable=True),
        sa.Column("mcs", sa.Integer(), nullable=True),
        sa.Column("download_mbps", sa.Float(), nullable=True),
        sa.Column("upload_mbps", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("jitter_ms", sa.Float(), nullable=True),
        sa.Column("packet_loss", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cell_id"],
            ["cells.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_telemetry_cell_id"),
        "telemetry",
        ["cell_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_telemetry_device_id"),
        "telemetry",
        ["device_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_telemetry_timestamp"),
        "telemetry",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_telemetry_timestamp"),
        table_name="telemetry",
    )

    op.drop_index(
        op.f("ix_telemetry_device_id"),
        table_name="telemetry",
    )

    op.drop_index(
        op.f("ix_telemetry_cell_id"),
        table_name="telemetry",
    )

    op.drop_table("telemetry")