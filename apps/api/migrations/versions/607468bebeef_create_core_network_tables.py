"""create core network tables

Revision ID: 607468bebeef
Revises:
Create Date: 2026-09-22 19:18:28.634414

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "607468bebeef"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core network tables."""

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_customers_customer_code"),
        "customers",
        ["customer_code"],
        unique=True,
    )

    op.create_table(
        "towers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tower_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("elevation_m", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_towers_tower_code"),
        "towers",
        ["tower_code"],
        unique=True,
    )

    op.create_table(
        "sectors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sector_code", sa.String(length=50), nullable=False),
        sa.Column("tower_id", sa.Integer(), nullable=False),
        sa.Column("azimuth_deg", sa.Float(), nullable=True),
        sa.Column("electrical_tilt_deg", sa.Float(), nullable=True),
        sa.Column("mechanical_tilt_deg", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tower_id"],
            ["towers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_sectors_sector_code"),
        "sectors",
        ["sector_code"],
        unique=True,
    )

    op.create_index(
        op.f("ix_sectors_tower_id"),
        "sectors",
        ["tower_id"],
        unique=False,
    )

    op.create_table(
        "cells",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cell_id", sa.String(length=80), nullable=False),
        sa.Column("sector_id", sa.Integer(), nullable=False),
        sa.Column("technology", sa.String(length=20), nullable=False),
        sa.Column("pci", sa.Integer(), nullable=True),
        sa.Column("earfcn", sa.Integer(), nullable=True),
        sa.Column("band", sa.String(length=20), nullable=True),
        sa.Column("bandwidth_mhz", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["sector_id"],
            ["sectors.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_cells_cell_id"),
        "cells",
        ["cell_id"],
        unique=True,
    )

    op.create_index(
        op.f("ix_cells_sector_id"),
        "cells",
        ["sector_id"],
        unique=False,
    )

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("current_cell_id", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("manufacturer", sa.String(length=100), nullable=True),
        sa.Column("software_version", sa.String(length=100), nullable=True),
        sa.Column("antenna_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["current_cell_id"],
            ["cells.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_devices_current_cell_id"),
        "devices",
        ["current_cell_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_devices_customer_id"),
        "devices",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_devices_device_id"),
        "devices",
        ["device_id"],
        unique=True,
    )

    op.create_table(
        "sims",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sim_id", sa.String(length=100), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("operator", sa.String(length=100), nullable=True),
        sa.Column("plan_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id"),
    )

    op.create_index(
        op.f("ix_sims_sim_id"),
        "sims",
        ["sim_id"],
        unique=True,
    )


def downgrade() -> None:
    """Drop core network tables."""

    op.drop_index(
        op.f("ix_sims_sim_id"),
        table_name="sims",
    )
    op.drop_table("sims")

    op.drop_index(
        op.f("ix_devices_device_id"),
        table_name="devices",
    )
    op.drop_index(
        op.f("ix_devices_customer_id"),
        table_name="devices",
    )
    op.drop_index(
        op.f("ix_devices_current_cell_id"),
        table_name="devices",
    )
    op.drop_table("devices")

    op.drop_index(
        op.f("ix_cells_sector_id"),
        table_name="cells",
    )
    op.drop_index(
        op.f("ix_cells_cell_id"),
        table_name="cells",
    )
    op.drop_table("cells")

    op.drop_index(
        op.f("ix_sectors_tower_id"),
        table_name="sectors",
    )
    op.drop_index(
        op.f("ix_sectors_sector_code"),
        table_name="sectors",
    )
    op.drop_table("sectors")

    op.drop_index(
        op.f("ix_towers_tower_code"),
        table_name="towers",
    )
    op.drop_table("towers")

    op.drop_index(
        op.f("ix_customers_customer_code"),
        table_name="customers",
    )
    op.drop_table("customers")