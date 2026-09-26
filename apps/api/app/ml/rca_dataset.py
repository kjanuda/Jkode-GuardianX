from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.features import (
    build_features_from_evidence_map,
)

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)


STRUCTURED_ENGINE = (
    "STRUCTURED_RCA_V1"
)

CONSENSUS_ENGINE = (
    "RCA_CONSENSUS_V1"
)


def latest_prediction(
    *,
    db: Session,
    case_id: int,
    engine_type: str,
) -> RCAPrediction | None:
    return db.scalar(
        select(
            RCAPrediction
        )
        .where(
            RCAPrediction.case_id
            == case_id,

            RCAPrediction.engine_type
            == engine_type,
        )
        .order_by(
            RCAPrediction.created_at.desc(),
            RCAPrediction.id.desc(),
        )
        .limit(1)
    )


def build_case_training_row(
    *,
    db: Session,
    case: RCACase,
) -> dict[str, Any] | None:
    structured = latest_prediction(
        db=db,
        case_id=case.id,
        engine_type=STRUCTURED_ENGINE,
    )

    # -----------------------------------------
    # Only deterministic verified RCA cases
    # may become labelled ML examples.
    # -----------------------------------------

    if structured is None:
        return None

    structured_output = (
        structured.output_json
        or {}
    )

    if (
        structured.verifier_status
        != "VERIFIED"
        or structured_output.get(
            "verified"
        )
        is not True
    ):
        return None

    evidence_items = list(
        db.scalars(
            select(
                RCAEvidence
            )
            .where(
                RCAEvidence.case_id
                == case.id
            )
            .order_by(
                RCAEvidence.id.asc()
            )
        ).all()
    )

    evidence_map = {
        item.evidence_key: item
        for item in evidence_items
    }

    # -----------------------------------------
    # Shared feature extraction
    #
    # Dataset export and live inference both
    # use build_features_from_evidence_map().
    # -----------------------------------------

    features = (
        build_features_from_evidence_map(
            evidence_map
        )
    )

    consensus = latest_prediction(
        db=db,
        case_id=case.id,
        engine_type=CONSENSUS_ENGINE,
    )

    consensus_output = (
        consensus.output_json
        if consensus is not None
        else {}
    ) or {}

    consensus_status = (
        consensus_output.get(
            "consensus_status"
        )
        if consensus is not None
        else None
    )

    human_review_required = (
        consensus_output.get(
            "human_review_required"
        )
        if consensus is not None
        else None
    )

    root_cause = (
        structured_output.get(
            "primary_root_cause"
        )
        or structured.primary_cause
    )

    domain = structured_output.get(
        "domain"
    )

    confidence = (
        structured_output.get(
            "confidence"
        )
    )

    # -----------------------------------------
    # Training eligibility
    #
    # Only consensus-agreement rows with no
    # human review requirement are considered
    # high-quality ML training examples.
    #
    # Other verified rows remain in the
    # exported dataset but are marked
    # training_eligible=False.
    # -----------------------------------------

    training_eligible = (
        consensus_status
        == "AGREEMENT"
        and human_review_required
        is False
    )

    return {
        "case_id":
            case.id,

        "case_uuid":
            case.case_uuid,

        "scope_type":
            case.scope_type,

        "scope_ref":
            case.scope_ref,

        "trigger_type":
            case.trigger_type,

        "risk_score":
            case.risk_score,

        "risk_level":
            case.risk_level,

        # -------------------------------------
        # Shared ML features
        # -------------------------------------

        **features,

        # -------------------------------------
        # Labels
        # -------------------------------------

        "label_domain":
            domain,

        "label_primary_cause":
            root_cause,

        # -------------------------------------
        # Metadata — not model features
        # -------------------------------------

        "label_confidence":
            confidence,

        "structured_verified":
            True,

        "consensus_status":
            consensus_status,

        "human_review_required":
            human_review_required,

        "training_eligible":
            training_eligible,

        "created_at":
            (
                case.created_at.isoformat()
                if case.created_at
                else None
            ),
    }


def build_rca_dataset(
    *,
    db: Session,
) -> list[dict[str, Any]]:
    cases = list(
        db.scalars(
            select(
                RCACase
            )
            .order_by(
                RCACase.id.asc()
            )
        ).all()
    )

    rows = []

    for case in cases:
        row = (
            build_case_training_row(
                db=db,
                case=case,
            )
        )

        if row is not None:
            rows.append(
                row
            )

    return rows