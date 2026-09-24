"""add rca evidence system

Revision ID: 5805a3ea240f
Revises: 252d8ee6a5f9
Create Date: 2026-09-24 00:58:09.218010

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =====================================================
# Revision identifiers
# =====================================================

revision: str = "5805a3ea240f"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "252d8ee6a5f9"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


# =====================================================
# Upgrade
# =====================================================

def upgrade() -> None:
    """Upgrade schema."""

    # =================================================
    # RCA CASES
    # =================================================

    op.create_table(
        "rca_cases",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "case_uuid",
            sa.String(length=36),
            nullable=False,
        ),

        sa.Column(
            "device_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "alert_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "scope_type",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "scope_ref",
            sa.String(length=120),
            nullable=False,
        ),

        sa.Column(
            "trigger_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "risk_score",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "risk_level",
            sa.String(length=30),
            nullable=True,
        ),

        sa.Column(
            "baseline_primary_cause",
            sa.String(length=120),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            ondelete="SET NULL",
        ),

        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    # RCA CASES indexes

    op.create_index(
        op.f("ix_rca_cases_alert_id"),
        "rca_cases",
        ["alert_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_cases_case_uuid"),
        "rca_cases",
        ["case_uuid"],
        unique=True,
    )

    op.create_index(
        op.f("ix_rca_cases_created_at"),
        "rca_cases",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_cases_device_id"),
        "rca_cases",
        ["device_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_cases_scope_ref"),
        "rca_cases",
        ["scope_ref"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_cases_scope_type"),
        "rca_cases",
        ["scope_type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_cases_status"),
        "rca_cases",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_cases_trigger_type"),
        "rca_cases",
        ["trigger_type"],
        unique=False,
    )


    # =================================================
    # RCA EVIDENCE
    # =================================================

    op.create_table(
        "rca_evidence",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "case_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "evidence_key",
            sa.String(length=120),
            nullable=False,
        ),

        sa.Column(
            "source",
            sa.String(length=80),
            nullable=False,
        ),

        sa.Column(
            "category",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "metric",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "value_json",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),

        sa.Column(
            "unit",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "supports_causes",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),

        sa.Column(
            "contradicts_causes",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),

        sa.Column(
            "support_score",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "reliability_score",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "freshness_score",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "specificity_score",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "gate_passed",
            sa.Boolean(),
            nullable=True,
        ),

        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "context_json",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["case_id"],
            ["rca_cases.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    # RCA EVIDENCE indexes

    op.create_index(
        op.f("ix_rca_evidence_case_id"),
        "rca_evidence",
        ["case_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_evidence_category"),
        "rca_evidence",
        ["category"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_evidence_evidence_key"),
        "rca_evidence",
        ["evidence_key"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_evidence_metric"),
        "rca_evidence",
        ["metric"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_evidence_source"),
        "rca_evidence",
        ["source"],
        unique=False,
    )


    # =================================================
    # RCA PREDICTIONS
    # =================================================

    op.create_table(
        "rca_predictions",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "case_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "engine_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "primary_cause",
            sa.String(length=120),
            nullable=True,
        ),

        sa.Column(
            "confidence",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "rank",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "output_json",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),

        sa.Column(
            "verifier_status",
            sa.String(length=40),
            nullable=True,
        ),

        sa.Column(
            "verifier_reason",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["case_id"],
            ["rca_cases.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    # RCA PREDICTIONS indexes

    op.create_index(
        op.f("ix_rca_predictions_case_id"),
        "rca_predictions",
        ["case_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_rca_predictions_engine_type"),
        "rca_predictions",
        ["engine_type"],
        unique=False,
    )

    # =================================================
    # IMPORTANT
    # =================================================
    #
    # DO NOT drop spatial_ref_sys here.
    #
    # spatial_ref_sys is managed by the PostGIS
    # extension, not by the Guardian X application
    # migration.
    #
    # =================================================


# =====================================================
# Downgrade
# =====================================================

def downgrade() -> None:
    """Downgrade schema."""

    # =================================================
    # RCA PREDICTIONS
    # =================================================

    op.drop_index(
        op.f("ix_rca_predictions_engine_type"),
        table_name="rca_predictions",
    )

    op.drop_index(
        op.f("ix_rca_predictions_case_id"),
        table_name="rca_predictions",
    )

    op.drop_table(
        "rca_predictions",
    )


    # =================================================
    # RCA EVIDENCE
    # =================================================

    op.drop_index(
        op.f("ix_rca_evidence_source"),
        table_name="rca_evidence",
    )

    op.drop_index(
        op.f("ix_rca_evidence_metric"),
        table_name="rca_evidence",
    )

    op.drop_index(
        op.f("ix_rca_evidence_evidence_key"),
        table_name="rca_evidence",
    )

    op.drop_index(
        op.f("ix_rca_evidence_category"),
        table_name="rca_evidence",
    )

    op.drop_index(
        op.f("ix_rca_evidence_case_id"),
        table_name="rca_evidence",
    )

    op.drop_table(
        "rca_evidence",
    )


    # =================================================
    # RCA CASES
    # =================================================

    op.drop_index(
        op.f("ix_rca_cases_trigger_type"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_status"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_scope_type"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_scope_ref"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_device_id"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_created_at"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_case_uuid"),
        table_name="rca_cases",
    )

    op.drop_index(
        op.f("ix_rca_cases_alert_id"),
        table_name="rca_cases",
    )

    op.drop_table(
        "rca_cases",
    )

    # =================================================
    # IMPORTANT
    # =================================================
    #
    # DO NOT recreate spatial_ref_sys here.
    #
    # It belongs to the PostGIS extension and should
    # remain managed by PostGIS.
    #
    # =================================================