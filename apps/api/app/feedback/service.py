from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.action import ActionPlan
from app.models.action_feedback import ActionFeedback
from app.models.action_simulation import (
    ActionSimulation,
)
from app.models.action_verification import (
    ActionVerification,
)


FEEDBACK_SERVICE_VERSION = (
    "ACTION_FEEDBACK_SERVICE_V1"
)

DRAFT = "DRAFT"
SUBMITTED = "SUBMITTED"

HANDOVER_ELIGIBLE_ACTION_STATUSES = {
    "VERIFIED_SUCCESS",
    "VERIFIED_FAILED",
    "ROLLBACK_REQUIRED",
    "BLOCKED",
    "REJECTED",
}

DIAGNOSIS_ASSESSMENTS = {
    "UNREVIEWED",
    "CORRECT",
    "PARTIALLY_CORRECT",
    "INCORRECT",
    "UNKNOWN",
}

ACTION_ASSESSMENTS = {
    "UNREVIEWED",
    "USEFUL",
    "PARTIALLY_USEFUL",
    "NOT_USEFUL",
    "NOT_APPLICABLE",
}

RESOLUTION_STATUSES = {
    "UNKNOWN",
    "RESOLVED",
    "PARTIALLY_RESOLVED",
    "NOT_RESOLVED",
    "NO_CHANGE_PERFORMED",
}

EDITABLE_FIELDS = {
    "reviewer",
    "diagnosis_assessment",
    "action_assessment",
    "resolution_status",
    "operator_confidence",
    "actual_root_cause",
    "actual_resolution",
    "notes",
}


class ActionFeedbackError(
    RuntimeError
):
    pass


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def feedback_to_dict(
    feedback: ActionFeedback,
) -> dict[str, Any]:
    return {
        "id":
            feedback.id,

        "feedback_uuid":
            feedback.feedback_uuid,

        "action_plan_id":
            feedback.action_plan_id,

        "rca_case_id":
            feedback.rca_case_id,

        "alert_id":
            feedback.alert_id,

        "verification_id":
            feedback.verification_id,

        "revision":
            feedback.revision,

        "reviewer":
            feedback.reviewer,

        "feedback_status":
            feedback.feedback_status,

        "diagnosis_assessment":
            feedback.diagnosis_assessment,

        "action_assessment":
            feedback.action_assessment,

        "resolution_status":
            feedback.resolution_status,

        "operator_confidence":
            feedback.operator_confidence,

        "actual_root_cause":
            feedback.actual_root_cause,

        "actual_resolution":
            feedback.actual_resolution,

        "notes":
            feedback.notes,

        "evidence_json":
            feedback.evidence_json,

        "provenance_json":
            feedback.provenance_json,

        "quality_gate_status":
            feedback.quality_gate_status,

        "training_eligible":
            feedback.training_eligible,

        "schema_version":
            feedback.schema_version,

        "reviewed_at":
            (
                feedback.reviewed_at.isoformat()
                if feedback.reviewed_at
                else None
            ),

        "submitted_at":
            (
                feedback.submitted_at.isoformat()
                if feedback.submitted_at
                else None
            ),

        "created_at":
            (
                feedback.created_at.isoformat()
                if feedback.created_at
                else None
            ),

        "updated_at":
            (
                feedback.updated_at.isoformat()
                if feedback.updated_at
                else None
            ),
    }


def get_latest_feedback(
    db: Session,
    action_plan_id: int,
) -> ActionFeedback | None:
    return db.scalar(
        select(
            ActionFeedback
        )
        .where(
            ActionFeedback.action_plan_id
            == action_plan_id
        )
        .order_by(
            ActionFeedback.revision.desc(),
            ActionFeedback.id.desc(),
        )
        .limit(1)
    )


def get_latest_simulation(
    db: Session,
    action_plan_id: int,
) -> ActionSimulation | None:
    return db.scalar(
        select(
            ActionSimulation
        )
        .where(
            ActionSimulation.action_plan_id
            == action_plan_id
        )
        .order_by(
            ActionSimulation.attempt.desc(),
            ActionSimulation.id.desc(),
        )
        .limit(1)
    )


def get_simulation_verification(
    db: Session,
    simulation_id: int | None,
) -> ActionVerification | None:
    if simulation_id is None:
        return None

    return db.scalar(
        select(
            ActionVerification
        ).where(
            ActionVerification.simulation_id
            == simulation_id
        )
    )


def create_feedback_revision(
    db: Session,
    action_plan_id: int,
    reviewer: str | None = None,
) -> dict[str, Any]:
    plan = db.get(
        ActionPlan,
        action_plan_id,
    )

    if plan is None:
        raise ActionFeedbackError(
            "Action plan not found"
        )

    if (
        plan.status
        not in HANDOVER_ELIGIBLE_ACTION_STATUSES
    ):
        raise ActionFeedbackError(
            "Action plan is not in a "
            "handover-eligible status: "
            f"{plan.status}"
        )

    latest = get_latest_feedback(
        db=db,
        action_plan_id=action_plan_id,
    )

    if (
        latest is not None
        and latest.feedback_status == DRAFT
    ):
        return {
            "created":
                False,

            **feedback_to_dict(
                latest
            ),
        }

    simulation = get_latest_simulation(
        db=db,
        action_plan_id=action_plan_id,
    )

    verification = (
        get_simulation_verification(
            db=db,
            simulation_id=(
                simulation.id
                if simulation
                else None
            ),
        )
    )

    revision = (
        latest.revision + 1
        if latest
        else 1
    )

    evidence_snapshot = {
        "action_plan_status":
            plan.status,

        "action_code":
            plan.action_code,

        "action_type":
            plan.action_type,

        "target_type":
            plan.target_type,

        "target_ref":
            plan.target_ref,

        "source_primary_cause":
            plan.source_primary_cause,

        "source_confidence":
            plan.source_confidence,

        "source_verifier_status":
            plan.source_verifier_status,

        "execution_mode":
            plan.execution_mode,

        "auto_eligible":
            plan.auto_eligible,

        "simulation_id":
            (
                simulation.id
                if simulation
                else None
            ),

        "simulation_status":
            (
                simulation.status
                if simulation
                else None
            ),

        "simulation_execution_allowed":
            (
                simulation.execution_allowed
                if simulation
                else None
            ),

        "verification_id":
            (
                verification.id
                if verification
                else None
            ),

        "verification_status":
            (
                verification.status
                if verification
                else None
            ),

        "rollback_decision":
            (
                verification.rollback_decision
                if verification
                else None
            ),

        "verification_execution_allowed":
            (
                verification.execution_allowed
                if verification
                else None
            ),
    }

    provenance = {
        "source":
            "OPERATOR_HANDOVER",

        "service_version":
            FEEDBACK_SERVICE_VERSION,

        "action_plan_id":
            plan.id,

        "rca_case_id":
            plan.rca_case_id,

        "alert_id":
            plan.alert_id,

        "verification_id":
            (
                verification.id
                if verification
                else None
            ),

        "captured_from_action_status":
            plan.status,

        "training_eligibility_assigned":
            False,
    }

    normalized_reviewer = (
        reviewer.strip()
        if reviewer
        else None
    )

    feedback = ActionFeedback(
        action_plan_id=
            plan.id,

        rca_case_id=
            plan.rca_case_id,

        alert_id=
            plan.alert_id,

        verification_id=
            (
                verification.id
                if verification
                else None
            ),

        revision=
            revision,

        reviewer=
            normalized_reviewer,

        feedback_status=
            DRAFT,

        diagnosis_assessment=
            "UNREVIEWED",

        action_assessment=
            "UNREVIEWED",

        resolution_status=
            "UNKNOWN",

        evidence_json=
            evidence_snapshot,

        provenance_json=
            provenance,

        quality_gate_status=
            "PENDING",

        training_eligible=
            False,

        schema_version=
            "ACTION_FEEDBACK_V1",
    )

    db.add(
        feedback
    )

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        latest = get_latest_feedback(
            db=db,
            action_plan_id=action_plan_id,
        )

        if (
            latest is not None
            and latest.feedback_status
            == DRAFT
        ):
            return {
                "created":
                    False,

                **feedback_to_dict(
                    latest
                ),
            }

        raise ActionFeedbackError(
            "Feedback revision conflict"
        ) from exc

    db.refresh(
        feedback
    )

    return {
        "created":
            True,

        **feedback_to_dict(
            feedback
        ),
    }


def update_feedback_draft(
    db: Session,
    feedback_id: int,
    updates: dict[str, Any],
) -> dict[str, Any]:
    feedback = db.get(
        ActionFeedback,
        feedback_id,
    )

    if feedback is None:
        raise ActionFeedbackError(
            "Feedback not found"
        )

    if (
        feedback.feedback_status
        != DRAFT
    ):
        raise ActionFeedbackError(
            "Only DRAFT feedback can be edited"
        )

    unknown_fields = (
        set(updates)
        - EDITABLE_FIELDS
    )

    if unknown_fields:
        raise ActionFeedbackError(
            "Unsupported feedback fields: "
            + ", ".join(
                sorted(
                    unknown_fields
                )
            )
        )

    # ---------------------------------------------
    # Phase 1:
    # Validate + normalize into a temporary dict.
    #
    # Do NOT mutate the ORM object yet.
    # ---------------------------------------------

    normalized_updates: dict[
        str,
        Any,
    ] = {}

    if "diagnosis_assessment" in updates:
        value = str(
            updates[
                "diagnosis_assessment"
            ]
        ).strip().upper()

        if (
            value
            not in DIAGNOSIS_ASSESSMENTS
        ):
            raise ActionFeedbackError(
                "Invalid diagnosis_assessment"
            )

        normalized_updates[
            "diagnosis_assessment"
        ] = value

    if "action_assessment" in updates:
        value = str(
            updates[
                "action_assessment"
            ]
        ).strip().upper()

        if (
            value
            not in ACTION_ASSESSMENTS
        ):
            raise ActionFeedbackError(
                "Invalid action_assessment"
            )

        normalized_updates[
            "action_assessment"
        ] = value

    if "resolution_status" in updates:
        value = str(
            updates[
                "resolution_status"
            ]
        ).strip().upper()

        if (
            value
            not in RESOLUTION_STATUSES
        ):
            raise ActionFeedbackError(
                "Invalid resolution_status"
            )

        normalized_updates[
            "resolution_status"
        ] = value

    if "operator_confidence" in updates:
        raw_confidence = updates[
            "operator_confidence"
        ]

        if raw_confidence is None:
            normalized_updates[
                "operator_confidence"
            ] = None

        else:
            try:
                confidence = float(
                    raw_confidence
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ActionFeedbackError(
                    "operator_confidence "
                    "must be a number"
                ) from exc

            if not (
                0.0
                <= confidence
                <= 1.0
            ):
                raise ActionFeedbackError(
                    "operator_confidence "
                    "must be between 0 and 1"
                )

            normalized_updates[
                "operator_confidence"
            ] = confidence

    for field_name in (
        "reviewer",
        "actual_root_cause",
        "actual_resolution",
        "notes",
    ):
        if field_name not in updates:
            continue

        raw_value = updates[
            field_name
        ]

        if raw_value is None:
            normalized_updates[
                field_name
            ] = None

            continue

        normalized = str(
            raw_value
        ).strip()

        normalized_updates[
            field_name
        ] = (
            normalized
            if normalized
            else None
        )

    # ---------------------------------------------
    # Phase 2:
    # Mutate only after ALL validation passed.
    # ---------------------------------------------

    for (
        field_name,
        value,
    ) in normalized_updates.items():
        setattr(
            feedback,
            field_name,
            value,
        )

    # 37C owns quality validation.
    feedback.quality_gate_status = (
        "PENDING"
    )

    # Editing feedback never automatically
    # promotes it into model training.
    feedback.training_eligible = (
        False
    )

    try:
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        raise ActionFeedbackError(
            "Failed to update feedback"
        ) from exc

    db.refresh(
        feedback
    )

    return {
        "changed":
            True,

        **feedback_to_dict(
            feedback
        ),
    }


def submit_feedback(
    db: Session,
    feedback_id: int,
) -> dict[str, Any]:
    feedback = db.get(
        ActionFeedback,
        feedback_id,
    )

    if feedback is None:
        raise ActionFeedbackError(
            "Feedback not found"
        )

    if (
        feedback.feedback_status
        == SUBMITTED
    ):
        return {
            "changed":
                False,

            **feedback_to_dict(
                feedback
            ),
        }

    if (
        feedback.feedback_status
        != DRAFT
    ):
        raise ActionFeedbackError(
            "Only DRAFT feedback can be submitted"
        )

    if not (
        feedback.reviewer
        and feedback.reviewer.strip()
    ):
        raise ActionFeedbackError(
            "Reviewer is required before submission"
        )

    if (
        feedback.diagnosis_assessment
        in {
            "UNREVIEWED",
            "UNKNOWN",
        }
    ):
        raise ActionFeedbackError(
            "Diagnosis assessment is required "
            "before submission"
        )

    if (
        feedback.action_assessment
        == "UNREVIEWED"
    ):
        raise ActionFeedbackError(
            "Action assessment is required "
            "before submission"
        )

    if (
        feedback.resolution_status
        == "UNKNOWN"
    ):
        raise ActionFeedbackError(
            "Resolution status is required "
            "before submission"
        )

    if (
        feedback.operator_confidence
        is None
    ):
        raise ActionFeedbackError(
            "Operator confidence is required "
            "before submission"
        )

    if (
        feedback.diagnosis_assessment
        == "INCORRECT"
        and not (
            feedback.actual_root_cause
            and feedback.actual_root_cause.strip()
        )
    ):
        raise ActionFeedbackError(
            "Actual root cause is required "
            "when diagnosis is INCORRECT"
        )

    timestamp = utc_now()

    feedback.feedback_status = (
        SUBMITTED
    )

    feedback.reviewed_at = (
        timestamp
    )

    feedback.submitted_at = (
        timestamp
    )

    # 37C owns quality/training eligibility.
    feedback.quality_gate_status = (
        "PENDING"
    )

    feedback.training_eligible = (
        False
    )

    db.commit()

    db.refresh(
        feedback
    )

    return {
        "changed":
            True,

        **feedback_to_dict(
            feedback
        ),
    }
