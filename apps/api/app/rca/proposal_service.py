from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)

from app.rca.proposal_verifier import (
    verify_rca_proposal,
)

from app.rca.rag_context import (
    build_rag_evidence_packet,
)


AUDIT_ENGINE_TYPE = (
    "RCA_PROPOSAL_AUDIT_V1"
)


def load_case_evidence(
    *,
    db: Session,
    case_id: int,
) -> tuple[
    RCACase,
    list[RCAEvidence],
]:
    case = db.get(
        RCACase,
        case_id,
    )

    if case is None:
        raise ValueError(
            "RCA case not found"
        )

    evidence_items = list(
        db.scalars(
            select(
                RCAEvidence
            )
            .where(
                RCAEvidence.case_id
                == case_id
            )
            .order_by(
                RCAEvidence.id.asc()
            )
        ).all()
    )

    if not evidence_items:
        raise ValueError(
            "RCA case has no evidence"
        )

    return (
        case,
        evidence_items,
    )


def get_case_evidence_packet(
    *,
    db: Session,
    case_id: int,
) -> dict:
    _, evidence_items = (
        load_case_evidence(
            db=db,
            case_id=case_id,
        )
    )

    return build_rag_evidence_packet(
        case_id=case_id,
        evidence_items=evidence_items,
    )


def verify_case_proposal(
    *,
    db: Session,
    case_id: int,
    proposal: dict,
) -> dict:
    _, evidence_items = (
        load_case_evidence(
            db=db,
            case_id=case_id,
        )
    )

    result = verify_rca_proposal(
        proposal=proposal,
        evidence_items=evidence_items,
    )

    reasons = list(
        result.get(
            "verification_reasons"
        )
        or []
    )

    # -----------------------------------------
    # Path case must match proposal case.
    # -----------------------------------------

    if (
        proposal.get(
            "case_id"
        )
        != case_id
    ):
        reasons.append(
            "PROPOSAL_CASE_MISMATCH"
        )

    reasons = list(
        dict.fromkeys(
            reasons
        )
    )

    verified = (
        len(reasons) == 0
    )

    result[
        "verification_reasons"
    ] = reasons

    result[
        "verified"
    ] = verified

    result[
        "proposal_status"
    ] = (
        "ACCEPTED"
        if verified
        else "REJECTED"
    )

    proposal_id = str(
        uuid4()
    )

    result[
        "proposal_id"
    ] = proposal_id

    audit_output = {
        "schema_version":
            "RCA_PROPOSAL_AUDIT_V1",

        "proposal_id":
            proposal_id,

        "case_id":
            case_id,

        "proposal":
            proposal,

        "verification":
            result,
    }

    verifier_reason = (
        "; ".join(
            reasons
        )
        if reasons
        else None
    )

    prediction = (
        RCAPrediction(
            case_id=case_id,

            engine_type=(
                AUDIT_ENGINE_TYPE
            ),

            primary_cause=(
                proposal.get(
                    "primary_cause"
                )
            ),

            confidence=(
                proposal.get(
                    "confidence"
                )
            ),

            rank=1,

            output_json=(
                audit_output
            ),

            verifier_status=(
                result[
                    "proposal_status"
                ]
            ),

            verifier_reason=(
                verifier_reason
            ),
        )
    )

    try:
        db.add(
            prediction
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return result