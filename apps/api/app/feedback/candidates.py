from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.feedback.quality import (
    PASSED,
    evaluate_feedback_quality,
)
from app.ml.features import (
    ML_FEATURE_COLUMNS,
    validate_ml_features,
)
from app.ml.provenance import (
    load_rca_provenance,
)
from app.ml.rca_dataset import (
    build_case_training_row,
)
from app.models.action_feedback import (
    ActionFeedback,
)
from app.models.rca import RCACase


CANDIDATE_SCHEMA_VERSION = (
    "FEEDBACK_ML_CANDIDATE_V1"
)

TRAINING_CANDIDATE = (
    "TRAINING_CANDIDATE"
)

EVALUATION_CANDIDATE = (
    "EVALUATION_CANDIDATE"
)

EXCLUDED = "EXCLUDED"


ALLOWED_CAUSES = {
    "DEVICE_MODEL_OR_FIRMWARE",
    "CELL_OR_NETWORK",
    "CONGESTION_OR_BACKHAUL",
    "COVERAGE_OR_PROPAGATION",
    "INTERFERENCE",
    "OUTAGE",
    "TERRAIN_PROPAGATION_LIKELY",
    "VEGETATION_PROPAGATION_POSSIBLE",
    "WEATHER_STRESS_POSSIBLE",
    "UNKNOWN",
}


class FeedbackCandidateError(
    RuntimeError
):
    pass


def resolve_split_group(
    provenance: dict[str, Any] | None,
) -> str | None:

    if not provenance:
        return None

    explicit = provenance.get(
        "split_group"
    )

    if explicit:
        return str(
            explicit
        )

    generation_group = provenance.get(
        "generation_group"
    )

    if generation_group:
        return str(
            generation_group
        )

    batch_id = provenance.get(
        "batch_id"
    )

    scenario_name = provenance.get(
        "scenario_name"
    )

    if (
        batch_id
        and scenario_name
    ):
        return (
            f"{batch_id}:"
            f"{scenario_name}"
        )

    return None


def resolve_feedback_label(
    *,
    feedback: ActionFeedback,
    base_row: dict[str, Any] | None,
) -> tuple[
    str | None,
    str | None,
]:

    if base_row is None:
        return (
            None,
            None,
        )

    structured_label = (
        base_row.get(
            "label_primary_cause"
        )
    )

    if (
        feedback.diagnosis_assessment
        == "INCORRECT"
    ):
        corrected = (
            feedback.actual_root_cause
            or ""
        ).strip().upper()

        if not corrected:
            return (
                None,
                "OPERATOR_CORRECTION_MISSING",
            )

        return (
            corrected,
            "OPERATOR_CORRECTED",
        )

    if (
        feedback.diagnosis_assessment
        == "CORRECT"
    ):
        return (
            structured_label,
            "OPERATOR_CONFIRMED_STRUCTURED",
        )

    if (
        feedback.diagnosis_assessment
        == "PARTIALLY_CORRECT"
    ):
        return (
            structured_label,
            "OPERATOR_PARTIAL_REVIEW",
        )

    return (
        None,
        "UNRESOLVED_OPERATOR_LABEL",
    )


def classify_candidate(
    *,
    quality_status: str,
    integrity_valid: bool,
    test_only: bool,
    data_origin: str,
    provenance_registered: bool,
    split_group: str | None,
    diagnosis_assessment: str,
    label_valid: bool,
    ml_row_available: bool,
    ml_features_valid: bool,
) -> tuple[
    str,
    list[str],
]:

    reasons: list[str] = []

    # -------------------------------------------------
    # Hard exclusions
    # -------------------------------------------------

    if test_only:
        return (
            EXCLUDED,
            [
                "TEST_ONLY_FEEDBACK",
            ],
        )

    if quality_status != PASSED:
        return (
            EXCLUDED,
            [
                "QUALITY_GATE_NOT_PASSED",
            ],
        )

    if integrity_valid is not True:
        return (
            EXCLUDED,
            [
                "QUALITY_INTEGRITY_INVALID",
            ],
        )

    if not ml_row_available:
        return (
            EXCLUDED,
            [
                "NO_VERIFIED_ML_ROW",
            ],
        )

    if not ml_features_valid:
        return (
            EXCLUDED,
            [
                "ML_FEATURES_INVALID",
            ],
        )

    if not label_valid:
        return (
            EXCLUDED,
            [
                "FEEDBACK_LABEL_INVALID",
            ],
        )

    # -------------------------------------------------
    # Human uncertainty stays evaluation-only
    # -------------------------------------------------

    if (
        diagnosis_assessment
        == "PARTIALLY_CORRECT"
    ):
        return (
            EVALUATION_CANDIDATE,
            [
                "PARTIAL_DIAGNOSIS_REVIEW",
            ],
        )

    # -------------------------------------------------
    # Unknown / unregistered provenance
    #
    # Never silently promote to REAL.
    # -------------------------------------------------

    if (
        data_origin == "UNKNOWN"
        or not provenance_registered
    ):
        return (
            EVALUATION_CANDIDATE,
            [
                "PROVENANCE_NOT_CONFIRMED_REAL",
            ],
        )

    # -------------------------------------------------
    # Synthetic evidence may help evaluation,
    # never human-real training promotion.
    # -------------------------------------------------

    if data_origin == "SYNTHETIC":
        return (
            EVALUATION_CANDIDATE,
            [
                "SYNTHETIC_SOURCE_EVALUATION_ONLY",
            ],
        )

    # -------------------------------------------------
    # Explicit REAL provenance only.
    # Group is mandatory to preserve leakage safety.
    # -------------------------------------------------

    if data_origin == "REAL":
        if not split_group:
            return (
                EVALUATION_CANDIDATE,
                [
                    "REAL_PROVENANCE_MISSING_SPLIT_GROUP",
                ],
            )

        if diagnosis_assessment not in {
            "CORRECT",
            "INCORRECT",
        }:
            return (
                EVALUATION_CANDIDATE,
                [
                    "DIAGNOSIS_NOT_FINAL",
                ],
            )

        return (
            TRAINING_CANDIDATE,
            [],
        )

    # Any future/unknown provenance type fails toward
    # evaluation, never toward training.
    return (
        EVALUATION_CANDIDATE,
        [
            "UNRECOGNIZED_DATA_ORIGIN",
        ],
    )


def build_feedback_candidate(
    *,
    db: Session,
    feedback_id: int,
) -> dict[str, Any]:

    feedback = db.get(
        ActionFeedback,
        feedback_id,
    )

    if feedback is None:
        raise FeedbackCandidateError(
            "Feedback not found"
        )

    if (
        feedback.feedback_status
        != "SUBMITTED"
    ):
        raise FeedbackCandidateError(
            "Only SUBMITTED feedback "
            "can become an ML candidate"
        )

    # -------------------------------------------------
    # Re-run 37C integrity gate.
    # A sealed-but-mutated record fails closed here.
    # -------------------------------------------------

    quality = evaluate_feedback_quality(
        db=db,
        feedback_id=feedback_id,
    )

    db.refresh(
        feedback
    )

    quality_status = quality[
        "quality_gate_status"
    ]

    integrity_valid = (
        quality.get(
            "integrity_valid"
        )
        is True
    )

    feedback_provenance = (
        feedback.provenance_json
        or {}
    )

    test_only = (
        feedback_provenance.get(
            "test_only"
        )
        is True
    )

    # -------------------------------------------------
    # Underlying verified RCA row
    # -------------------------------------------------

    case = db.get(
        RCACase,
        feedback.rca_case_id,
    )

    base_row = None

    if case is not None:
        base_row = build_case_training_row(
            db=db,
            case=case,
        )

    ml_row_available = (
        base_row is not None
    )

    # -------------------------------------------------
    # Existing explicit RCA provenance
    # -------------------------------------------------

    provenance_map = (
        load_rca_provenance()
    )

    case_provenance = (
        provenance_map.get(
            feedback.rca_case_id
        )
    )

    if case_provenance is None:
        data_origin = "UNKNOWN"
        provenance_registered = False
        provenance_source = None

    else:
        data_origin = str(
            case_provenance.get(
                "data_origin",
                "UNKNOWN",
            )
        ).upper()

        provenance_registered = (
            case_provenance.get(
                "provenance_registered"
            )
            is True
        )

        provenance_source = (
            case_provenance.get(
                "provenance_source"
            )
        )

    split_group = resolve_split_group(
        case_provenance
    )

    # -------------------------------------------------
    # Human label
    # -------------------------------------------------

    (
        candidate_label,
        label_source,
    ) = resolve_feedback_label(
        feedback=feedback,
        base_row=base_row,
    )

    label_valid = (
        candidate_label
        in ALLOWED_CAUSES
    )

    structured_label = (
        base_row.get(
            "label_primary_cause"
        )
        if base_row
        else None
    )

    # -------------------------------------------------
    # Explicit ML feature allowlist only
    # -------------------------------------------------

    feature_payload = {}

    ml_features_valid = False
    ml_feature_error = None

    if base_row is not None:
        feature_payload = {
            feature_name:
                base_row.get(
                    feature_name
                )
            for feature_name
            in ML_FEATURE_COLUMNS
        }

        try:
            validate_ml_features(
                feature_payload
            )

            ml_features_valid = True

        except Exception as exc:
            ml_feature_error = str(
                exc
            )

    # -------------------------------------------------
    # Final conservative classification
    # -------------------------------------------------

    (
        candidate_type,
        reasons,
    ) = classify_candidate(
        quality_status=
            quality_status,

        integrity_valid=
            integrity_valid,

        test_only=
            test_only,

        data_origin=
            data_origin,

        provenance_registered=
            provenance_registered,

        split_group=
            split_group,

        diagnosis_assessment=
            feedback.diagnosis_assessment,

        label_valid=
            label_valid,

        ml_row_available=
            ml_row_available,

        ml_features_valid=
            ml_features_valid,
    )

    training_eligible = (
        candidate_type
        == TRAINING_CANDIDATE
    )

    previous_training_eligible = (
        feedback.training_eligible
    )

    feedback.training_eligible = (
        training_eligible
    )

    training_flag_changed = (
        previous_training_eligible
        != training_eligible
    )

    if training_flag_changed:
        db.commit()

        db.refresh(
            feedback
        )

    return {
        "schema_version":
            CANDIDATE_SCHEMA_VERSION,

        "candidate_type":
            candidate_type,

        "reasons":
            reasons,

        "training_eligible":
            training_eligible,

        "training_flag_changed":
            training_flag_changed,

        # ---------------------------------------------
        # Feedback traceability
        # ---------------------------------------------

        "feedback_id":
            feedback.id,

        "feedback_uuid":
            feedback.feedback_uuid,

        "feedback_revision":
            feedback.revision,

        "action_plan_id":
            feedback.action_plan_id,

        "rca_case_id":
            feedback.rca_case_id,

        "verification_id":
            feedback.verification_id,

        # ---------------------------------------------
        # Quality/integrity
        # ---------------------------------------------

        "quality_gate_status":
            quality_status,

        "quality_integrity_valid":
            integrity_valid,

        "quality_source_fingerprint":
            quality.get(
                "source_fingerprint"
            ),

        # ---------------------------------------------
        # Provenance
        # ---------------------------------------------

        "data_origin":
            data_origin,

        "provenance_registered":
            provenance_registered,

        "provenance_source":
            provenance_source,

        "split_group":
            split_group,

        "test_only":
            test_only,

        # ---------------------------------------------
        # Human adjudication
        # ---------------------------------------------

        "diagnosis_assessment":
            feedback.diagnosis_assessment,

        "action_assessment":
            feedback.action_assessment,

        "resolution_status":
            feedback.resolution_status,

        "operator_confidence":
            feedback.operator_confidence,

        "structured_label":
            structured_label,

        "candidate_label":
            candidate_label,

        "label_source":
            label_source,

        "label_valid":
            label_valid,

        # ---------------------------------------------
        # ML payload
        #
        # ONLY explicit feature allowlist is here.
        # No label/provenance metadata enters features.
        # ---------------------------------------------

        "ml_row_available":
            ml_row_available,

        "ml_features_valid":
            ml_features_valid,

        "ml_feature_error":
            ml_feature_error,

        "feature_payload":
            feature_payload,
    }
