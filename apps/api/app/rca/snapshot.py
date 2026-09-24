from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)

from app.rca.evidence import (
    build_context_evidence,
    build_telemetry_evidence,
)


def create_rca_snapshot(
    *,
    db: Session,
    device_id: int,
    device_external_id: str,
    telemetry,
    risk: dict,
    alert_id: int | None = None,
    trigger_type: str = (
        "MANUAL_SNAPSHOT"
    ),
) -> RCACase:
    causes = risk.get(
        "likely_causes",
        [],
    )

    baseline_primary_cause = (
        causes[0]
        if causes
        else None
    )

    case = RCACase(
        device_id=device_id,

        alert_id=alert_id,

        scope_type="DEVICE",

        scope_ref=(
            device_external_id
        ),

        trigger_type=trigger_type,

        status="OPEN",

        risk_score=risk[
            "risk_score"
        ],

        risk_level=risk[
            "risk_level"
        ],

        baseline_primary_cause=(
            baseline_primary_cause
        ),
    )

    db.add(
        case
    )

    db.flush()

    evidence_items = (
        build_telemetry_evidence(
            telemetry
        )
        +
        build_context_evidence(
            risk=risk,
            observed_at=(
                telemetry.timestamp
            ),
        )
    )

    for item in evidence_items:
        db.add(
            RCAEvidence(
                case_id=case.id,
                **item,
            )
        )

    # ----------------------------------
    # Current rule engine prediction.
    #
    # No artificial confidence yet.
    # STEP 31 will calculate confidence.
    # ----------------------------------

    prediction = RCAPrediction(
        case_id=case.id,

        engine_type=(
            "RULE_BASELINE"
        ),

        primary_cause=(
            baseline_primary_cause
        ),

        confidence=None,

        rank=1,

        output_json={
            "likely_causes":
                causes,

            "reasons":
                risk.get(
                    "reasons",
                    [],
                ),

            "risk_score":
                risk[
                    "risk_score"
                ],

            "risk_level":
                risk[
                    "risk_level"
                ],
        },

        verifier_status=(
            "NOT_VERIFIED"
        ),
    )

    db.add(
        prediction
    )

    db.commit()

    db.refresh(
        case
    )

    return case