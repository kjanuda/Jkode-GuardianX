from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.feedback.service import (
    FEEDBACK_SERVICE_VERSION,
    HANDOVER_ELIGIBLE_ACTION_STATUSES,
    feedback_to_dict,
)
from app.models.action import ActionPlan
from app.models.action_feedback import (
    ActionFeedback,
)
from app.models.action_verification import (
    ActionVerification,
)


QUALITY_GATE_VERSION = (
    "ACTION_FEEDBACK_QUALITY_V1"
)

FINGERPRINT_VERSION = (
    "ACTION_FEEDBACK_SOURCE_SHA256_V1"
)

PASSED = "PASSED"
PASSED_TEST_ONLY = "PASSED_TEST_ONLY"
FAILED = "FAILED"


class ActionFeedbackQualityError(
    RuntimeError
):
    pass


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def build_quality_source_snapshot(
    feedback: ActionFeedback,
    plan: ActionPlan | None,
    verification: ActionVerification | None,
) -> dict[str, Any]:

    provenance = deepcopy(
        feedback.provenance_json
        or {}
    )

    # Quality gate writes its own audit data here.
    # Exclude it from the fingerprint source.
    provenance.pop(
        "quality_gate",
        None,
    )

    return {
        "feedback": {
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
                feedback.evidence_json
                or {},

            "provenance_json":
                provenance,

            "schema_version":
                feedback.schema_version,
        },

        "action_plan": (
            {
                "id":
                    plan.id,

                "rca_case_id":
                    plan.rca_case_id,

                "alert_id":
                    plan.alert_id,

                "status":
                    plan.status,

                "source_primary_cause":
                    plan.source_primary_cause,

                "source_verifier_status":
                    plan.source_verifier_status,

                "action_code":
                    plan.action_code,

                "action_type":
                    plan.action_type,

                "execution_mode":
                    plan.execution_mode,

                "requires_human_approval":
                    plan.requires_human_approval,

                "auto_eligible":
                    plan.auto_eligible,
            }
            if plan
            else None
        ),

        "verification": (
            {
                "id":
                    verification.id,

                "simulation_id":
                    verification.simulation_id,

                "status":
                    verification.status,

                "rollback_decision":
                    verification.rollback_decision,

                "execution_allowed":
                    verification.execution_allowed,

                "integrity_valid":
                    (
                        verification.result_json
                        or {}
                    ).get(
                        "integrity_valid"
                    ),
            }
            if verification
            else None
        ),
    }


def compute_quality_fingerprint(
    snapshot: dict[str, Any],
) -> str:

    canonical = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode(
            "utf-8"
        )
    ).hexdigest()


def build_quality_checks(
    feedback: ActionFeedback,
    plan: ActionPlan | None,
    verification: ActionVerification | None,
) -> dict[str, bool]:

    evidence = (
        feedback.evidence_json
        or {}
    )

    provenance = (
        feedback.provenance_json
        or {}
    )

    confidence_valid = (
        feedback.operator_confidence
        is not None
        and 0.0
        <= feedback.operator_confidence
        <= 1.0
    )

    incorrect_cause_valid = (
        feedback.diagnosis_assessment
        != "INCORRECT"
        or bool(
            feedback.actual_root_cause
            and feedback.actual_root_cause.strip()
        )
    )

    verification_required = (
        feedback.verification_id
        is not None
    )

    verification_exists = (
        verification is not None
        if verification_required
        else True
    )

    verification_verified = (
        verification.status
        == "VERIFIED"
        if verification
        else not verification_required
    )

    verification_execution_disabled = (
        verification.execution_allowed
        is False
        if verification
        else not verification_required
    )

    verification_integrity_valid = (
        (
            verification.result_json
            or {}
        ).get(
            "integrity_valid"
        )
        is True
        if verification
        else not verification_required
    )

    return {
        "feedback_submitted":
            feedback.feedback_status
            == "SUBMITTED",

        "reviewer_present":
            bool(
                feedback.reviewer
                and feedback.reviewer.strip()
            ),

        "diagnosis_reviewed":
            feedback.diagnosis_assessment
            not in {
                "UNREVIEWED",
                "UNKNOWN",
            },

        "action_reviewed":
            feedback.action_assessment
            != "UNREVIEWED",

        "resolution_known":
            feedback.resolution_status
            != "UNKNOWN",

        "operator_confidence_valid":
            confidence_valid,

        "incorrect_diagnosis_has_actual_cause":
            incorrect_cause_valid,

        "feedback_schema_valid":
            feedback.schema_version
            == "ACTION_FEEDBACK_V1",

        "action_plan_exists":
            plan is not None,

        "plan_case_binding":
            (
                plan is not None
                and feedback.rca_case_id
                == plan.rca_case_id
            ),

        "plan_alert_binding":
            (
                plan is not None
                and feedback.alert_id
                == plan.alert_id
            ),

        "plan_handover_eligible":
            (
                plan is not None
                and plan.status
                in HANDOVER_ELIGIBLE_ACTION_STATUSES
            ),

        "plan_execution_still_advisory":
            (
                plan is not None
                and plan.execution_mode
                == "ADVISORY"
            ),

        "plan_auto_execution_disabled":
            (
                plan is not None
                and plan.auto_eligible
                is False
            ),

        "evidence_plan_status_matches":
            (
                plan is not None
                and evidence.get(
                    "action_plan_status"
                )
                == plan.status
            ),

        "evidence_action_code_matches":
            (
                plan is not None
                and evidence.get(
                    "action_code"
                )
                == plan.action_code
            ),

        "evidence_primary_cause_matches":
            (
                plan is not None
                and evidence.get(
                    "source_primary_cause"
                )
                == plan.source_primary_cause
            ),

        "evidence_execution_mode_matches":
            (
                plan is not None
                and evidence.get(
                    "execution_mode"
                )
                == plan.execution_mode
            ),

        "evidence_auto_eligible_matches":
            (
                plan is not None
                and evidence.get(
                    "auto_eligible"
                )
                == plan.auto_eligible
            ),

        "provenance_source_valid":
            provenance.get(
                "source"
            )
            == "OPERATOR_HANDOVER",

        "provenance_service_version_valid":
            provenance.get(
                "service_version"
            )
            == FEEDBACK_SERVICE_VERSION,

        "provenance_plan_binding":
            (
                plan is not None
                and provenance.get(
                    "action_plan_id"
                )
                == plan.id
            ),

        "provenance_case_binding":
            (
                plan is not None
                and provenance.get(
                    "rca_case_id"
                )
                == plan.rca_case_id
            ),

        "provenance_alert_binding":
            (
                plan is not None
                and provenance.get(
                    "alert_id"
                )
                == plan.alert_id
            ),

        "verification_exists_if_bound":
            verification_exists,

        "verification_status_valid":
            verification_verified,

        "verification_execution_disabled":
            verification_execution_disabled,

        "verification_integrity_valid":
            verification_integrity_valid,

        "verification_feedback_binding":
            (
                verification is not None
                and feedback.verification_id
                == verification.id
                if verification_required
                else True
            ),

        "evidence_verification_binding":
            (
                verification is not None
                and evidence.get(
                    "verification_id"
                )
                == verification.id
                if verification_required
                else evidence.get(
                    "verification_id"
                )
                is None
            ),

        "provenance_verification_binding":
            (
                verification is not None
                and provenance.get(
                    "verification_id"
                )
                == verification.id
                if verification_required
                else provenance.get(
                    "verification_id"
                )
                is None
            ),
    }


def evaluate_feedback_quality(
    db: Session,
    feedback_id: int,
) -> dict[str, Any]:

    feedback = db.get(
        ActionFeedback,
        feedback_id,
    )

    if feedback is None:
        raise ActionFeedbackQualityError(
            "Feedback not found"
        )

    if (
        feedback.feedback_status
        != "SUBMITTED"
    ):
        raise ActionFeedbackQualityError(
            "Only SUBMITTED feedback "
            "can enter the quality gate"
        )

    plan = db.get(
        ActionPlan,
        feedback.action_plan_id,
    )

    verification = None

    if (
        feedback.verification_id
        is not None
    ):
        verification = db.get(
            ActionVerification,
            feedback.verification_id,
        )

    snapshot = (
        build_quality_source_snapshot(
            feedback=feedback,
            plan=plan,
            verification=verification,
        )
    )

    current_fingerprint = (
        compute_quality_fingerprint(
            snapshot
        )
    )

    provenance = deepcopy(
        feedback.provenance_json
        or {}
    )

    existing_gate = (
        provenance.get(
            "quality_gate"
        )
        or {}
    )

    sealed_fingerprint = (
        existing_gate.get(
            "source_fingerprint"
        )
    )

    # -------------------------------------------------
    # Detect mutation after first quality evaluation.
    # Never silently reseal changed feedback.
    # -------------------------------------------------

    if (
        sealed_fingerprint
        and sealed_fingerprint
        != current_fingerprint
    ):
        reasons = [
            "FEEDBACK_CHANGED_AFTER_QUALITY_GATE"
        ]

        provenance[
            "quality_gate"
        ] = {
            **existing_gate,

            "quality_gate_version":
                QUALITY_GATE_VERSION,

            "fingerprint_version":
                FINGERPRINT_VERSION,

            "source_fingerprint":
                sealed_fingerprint,

            "current_fingerprint":
                current_fingerprint,

            "integrity_valid":
                False,

            "status":
                FAILED,

            "reasons":
                reasons,
        }

        feedback.provenance_json = (
            provenance
        )

        feedback.quality_gate_status = (
            FAILED
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

            "quality_gate_status":
                FAILED,

            "training_eligible":
                False,

            "integrity_valid":
                False,

            "checks":
                existing_gate.get(
                    "checks",
                    {},
                ),

            "reasons":
                reasons,

            "source_fingerprint":
                sealed_fingerprint,

            "current_fingerprint":
                current_fingerprint,

            "feedback":
                feedback_to_dict(
                    feedback
                ),
        }

    # -------------------------------------------------
    # Idempotent return after sealed evaluation
    # -------------------------------------------------

    if sealed_fingerprint:
        return {
            "changed":
                False,

            "quality_gate_status":
                feedback.quality_gate_status,

            "training_eligible":
                feedback.training_eligible,

            "integrity_valid":
                existing_gate.get(
                    "integrity_valid"
                ),

            "checks":
                existing_gate.get(
                    "checks",
                    {},
                ),

            "reasons":
                existing_gate.get(
                    "reasons",
                    [],
                ),

            "source_fingerprint":
                sealed_fingerprint,

            "current_fingerprint":
                current_fingerprint,

            "feedback":
                feedback_to_dict(
                    feedback
                ),
        }

    # -------------------------------------------------
    # First deterministic quality evaluation
    # -------------------------------------------------

    checks = build_quality_checks(
        feedback=feedback,
        plan=plan,
        verification=verification,
    )

    failed_checks = [
        name
        for name, passed
        in checks.items()
        if not passed
    ]

    test_only = (
        provenance.get(
            "test_only"
        )
        is True
    )

    if failed_checks:
        status = FAILED

        reasons = [
            f"QUALITY_CHECK_FAILED:{name}"
            for name
            in failed_checks
        ]

    elif test_only:
        status = PASSED_TEST_ONLY

        reasons = [
            "TEST_ONLY_FEEDBACK_EXCLUDED_FROM_TRAINING"
        ]

    else:
        status = PASSED
        reasons = []

    provenance[
        "quality_gate"
    ] = {
        "quality_gate_version":
            QUALITY_GATE_VERSION,

        "fingerprint_version":
            FINGERPRINT_VERSION,

        "source_fingerprint":
            current_fingerprint,

        "current_fingerprint":
            current_fingerprint,

        "integrity_valid":
            True,

        "status":
            status,

        "checks":
            checks,

        "reasons":
            reasons,

        "evaluated_at":
            utc_now().isoformat(),
    }

    feedback.provenance_json = (
        provenance
    )

    feedback.quality_gate_status = (
        status
    )

    # IMPORTANT:
    # Step 37C validates trustworthiness only.
    # Step 37D owns training/evaluation promotion.
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

        "quality_gate_status":
            status,

        "training_eligible":
            False,

        "integrity_valid":
            True,

        "checks":
            checks,

        "reasons":
            reasons,

        "source_fingerprint":
            current_fingerprint,

        "current_fingerprint":
            current_fingerprint,

        "feedback":
            feedback_to_dict(
                feedback
            ),
    }
