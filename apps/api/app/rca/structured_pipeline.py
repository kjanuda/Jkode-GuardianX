from __future__ import annotations


from sqlalchemy import (
    delete,
    select,
)

from sqlalchemy.orm import Session


from app.models.rca import (
    RCAEvidence,
    RCAPrediction,
)


from app.rca.hierarchy import (
    run_hierarchical_rca,
)


from app.rca.structured import (
    build_structured_rca,
)


from app.rca.verifier import (
    verify_structured_rca_with_evidence,
)


ENGINE_TYPE = "STRUCTURED_RCA_V1"


def run_structured_rca(
    *,
    db: Session,
    case_id: int,
) -> dict:
    """
    Full deterministic Guardian X RCA chain:

    Evidence
        -> Fusion
        -> Hierarchy
        -> Structured RCA
        -> Evidence-Aware Verifier
        -> Persisted diagnosis

    The verifier is the final safety gate.
    """

    hierarchy = (
        run_hierarchical_rca(
            db=db,
            case_id=case_id,
        )
    )

    structured = (
        build_structured_rca(
            case_id=case_id,
            hierarchy=hierarchy,
        )
    )

    # -----------------------------------------
    # Load actual RCA evidence
    # -----------------------------------------

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

    # -----------------------------------------
    # Evidence-aware verification
    # -----------------------------------------

    result = (
        verify_structured_rca_with_evidence(
            diagnosis=structured,
            evidence_items=evidence_items,
        )
    )

    # -----------------------------------------
    # Idempotent persistence
    #
    # Re-running the structured RCA for the
    # same case replaces the previous final
    # structured prediction.
    # -----------------------------------------

    try:
        db.execute(
            delete(
                RCAPrediction
            ).where(
                RCAPrediction.case_id
                == case_id,

                RCAPrediction.engine_type
                == ENGINE_TYPE,
            )
        )

        reasons = (
            result.get(
                "verification_reasons"
            )
            or []
        )

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
                    ENGINE_TYPE
                ),

                primary_cause=(
                    result.get(
                        "primary_root_cause"
                    )
                ),

                confidence=(
                    result.get(
                        "confidence"
                    )
                ),

                rank=1,

                output_json=result,

                verifier_status=(
                    result.get(
                        "verification_status"
                    )
                ),

                verifier_reason=(
                    verifier_reason
                ),
            )
        )

        db.add(
            prediction
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return result