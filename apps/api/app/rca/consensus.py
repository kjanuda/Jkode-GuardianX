from __future__ import annotations

from typing import Any

from sqlalchemy import (
    delete,
    select,
)

from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAPrediction,
)


CONSENSUS_ENGINE_TYPE = (
    "RCA_CONSENSUS_V1"
)


def contributor_causes(
    contributors: list | None,
) -> set[str]:
    if not contributors:
        return set()

    return {
        item.get("cause")
        for item in contributors
        if item.get("cause")
    }


def build_consensus_result(
    *,
    case_id: int,
    deterministic: dict[str, Any],
    llm_audit: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare verified deterministic RCA with the
    latest audited LLM proposal.

    LLM agreement is corroboration only.
    It does not increase deterministic confidence.
    """

    deterministic_output = (
        deterministic.get(
            "output_json"
        )
        or {}
    )

    llm_output = (
        llm_audit.get(
            "output_json"
        )
        or {}
    )

    llm_proposal = (
        llm_output.get(
            "proposal"
        )
        or {}
    )

    llm_verification = (
        llm_output.get(
            "verification"
        )
        or {}
    )

    deterministic_verified = (
        deterministic.get(
            "verifier_status"
        )
        == "VERIFIED"
        and deterministic_output.get(
            "verified"
        )
        is True
    )

    llm_accepted = (
        llm_audit.get(
            "verifier_status"
        )
        == "ACCEPTED"
        and llm_verification.get(
            "verified"
        )
        is True
    )

    deterministic_cause = (
        deterministic_output.get(
            "primary_root_cause"
        )
        or deterministic.get(
            "primary_cause"
        )
    )

    deterministic_domain = (
        deterministic_output.get(
            "domain"
        )
    )

    deterministic_confidence = (
        deterministic_output.get(
            "confidence"
        )
    )

    llm_cause = (
        llm_verification.get(
            "primary_cause"
        )
        or llm_proposal.get(
            "primary_cause"
        )
        or llm_audit.get(
            "primary_cause"
        )
    )

    llm_domain = (
        llm_verification.get(
            "proposed_domain"
        )
        or llm_proposal.get(
            "proposed_domain"
        )
    )

    llm_confidence = (
        llm_verification.get(
            "confidence"
        )
        or llm_proposal.get(
            "confidence"
        )
    )

    deterministic_contributors = (
        deterministic_output.get(
            "contributors"
        )
        or []
    )

    llm_contributors = (
        llm_verification.get(
            "verified_contributors"
        )
        or []
    )

    deterministic_contributor_set = (
        contributor_causes(
            deterministic_contributors
        )
    )

    llm_contributor_set = (
        contributor_causes(
            llm_contributors
        )
    )

    contributor_overlap = sorted(
        deterministic_contributor_set
        & llm_contributor_set
    )

    primary_match = (
        deterministic_cause
        == llm_cause
    )

    domain_match = (
        deterministic_domain
        == llm_domain
    )

    reasons = []

    # -----------------------------------------
    # Deterministic RCA is mandatory.
    # -----------------------------------------

    if not deterministic_verified:
        reasons.append(
            "DETERMINISTIC_RCA_NOT_VERIFIED"
        )

    # -----------------------------------------
    # LLM proposal must itself have passed
    # the evidence-aware proposal verifier.
    # -----------------------------------------

    if not llm_accepted:
        reasons.append(
            "LATEST_LLM_PROPOSAL_NOT_ACCEPTED"
        )

    # Only compare diagnoses when both inputs
    # are valid.
    if (
        deterministic_verified
        and llm_accepted
    ):
        if not domain_match:
            reasons.append(
                "DOMAIN_DISAGREEMENT"
            )

        if not primary_match:
            reasons.append(
                "ROOT_CAUSE_DISAGREEMENT"
            )

    agreement = (
        deterministic_verified
        and llm_accepted
        and primary_match
        and domain_match
    )

    if agreement:
        consensus_status = (
            "AGREEMENT"
        )

        human_review_required = False

        action_gate = (
            "ELIGIBLE_FOR_POLICY_REVIEW"
        )

    else:
        consensus_status = (
            "DISAGREEMENT"
        )

        human_review_required = True

        action_gate = (
            "BLOCKED"
        )

    return {
        "schema_version":
            "RCA_CONSENSUS_V1",

        "case_id":
            case_id,

        "deterministic": {
            "verified":
                deterministic_verified,

            "primary_cause":
                deterministic_cause,

            "domain":
                deterministic_domain,

            "confidence":
                deterministic_confidence,

            "prediction_id":
                deterministic.get(
                    "id"
                ),
        },

        "llm": {
            "accepted":
                llm_accepted,

            "primary_cause":
                llm_cause,

            "domain":
                llm_domain,

            "confidence":
                llm_confidence,

            "audit_prediction_id":
                llm_audit.get(
                    "id"
                ),

            "proposal_id":
                llm_verification.get(
                    "proposal_id"
                ),
        },

        "agreement": {
            "primary_cause_match":
                primary_match,

            "domain_match":
                domain_match,

            "deterministic_contributors":
                sorted(
                    deterministic_contributor_set
                ),

            "llm_contributors":
                sorted(
                    llm_contributor_set
                ),

            "contributor_overlap":
                contributor_overlap,
        },

        "consensus_status":
            consensus_status,

        "human_review_required":
            human_review_required,

        "action_gate":
            action_gate,

        "reasons":
            reasons,

        "note": (
            "LLM agreement is corroborating "
            "evidence only. Confidence values "
            "are not combined or boosted."
        ),
    }


def prediction_to_dict(
    prediction: RCAPrediction,
) -> dict:
    return {
        "id":
            prediction.id,

        "primary_cause":
            prediction.primary_cause,

        "confidence":
            prediction.confidence,

        "verifier_status":
            prediction.verifier_status,

        "verifier_reason":
            prediction.verifier_reason,

        "output_json":
            prediction.output_json
            or {},
    }


def run_case_consensus(
    *,
    db: Session,
    case_id: int,
) -> dict:
    case = db.get(
        RCACase,
        case_id,
    )

    if case is None:
        raise ValueError(
            "RCA case not found"
        )

    # Latest deterministic verified RCA.
    deterministic_prediction = (
        db.scalar(
            select(
                RCAPrediction
            )
            .where(
                RCAPrediction.case_id
                == case_id,

                RCAPrediction.engine_type
                == "STRUCTURED_RCA_V1",
            )
            .order_by(
                RCAPrediction.created_at.desc(),
                RCAPrediction.id.desc(),
            )
            .limit(1)
        )
    )

    if deterministic_prediction is None:
        raise ValueError(
            "Structured RCA prediction not found"
        )

    # Use the latest proposal attempt.
    #
    # Do NOT silently select an older accepted
    # proposal if the latest one was rejected.
    llm_prediction = (
        db.scalar(
            select(
                RCAPrediction
            )
            .where(
                RCAPrediction.case_id
                == case_id,

                RCAPrediction.engine_type
                == "RCA_PROPOSAL_AUDIT_V1",
            )
            .order_by(
                RCAPrediction.created_at.desc(),
                RCAPrediction.id.desc(),
            )
            .limit(1)
        )
    )

    if llm_prediction is None:
        raise ValueError(
            "LLM proposal audit not found"
        )

    result = (
        build_consensus_result(
            case_id=case_id,

            deterministic=(
                prediction_to_dict(
                    deterministic_prediction
                )
            ),

            llm_audit=(
                prediction_to_dict(
                    llm_prediction
                )
            ),
        )
    )

    # -----------------------------------------
    # Idempotent consensus persistence
    # -----------------------------------------

    db.execute(
        delete(
            RCAPrediction
        ).where(
            RCAPrediction.case_id
            == case_id,

            RCAPrediction.engine_type
            == CONSENSUS_ENGINE_TYPE,
        )
    )

    reasons = (
        result.get(
            "reasons"
        )
        or []
    )

    consensus_prediction = (
        RCAPrediction(
            case_id=case_id,

            engine_type=(
                CONSENSUS_ENGINE_TYPE
            ),

            primary_cause=(
                result[
                    "deterministic"
                ][
                    "primary_cause"
                ]
            ),

            # Keep deterministic confidence.
            # Never boost it using LLM output.
            confidence=(
                result[
                    "deterministic"
                ][
                    "confidence"
                ]
            ),

            rank=1,

            output_json=result,

            verifier_status=(
                result[
                    "consensus_status"
                ]
            ),

            verifier_reason=(
                "; ".join(
                    reasons
                )
                if reasons
                else None
            ),
        )
    )

    try:
        db.add(
            consensus_prediction
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return result