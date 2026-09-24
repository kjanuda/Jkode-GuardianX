
from __future__ import annotations

from math import prod

from sqlalchemy import (
    delete,
    select,
)

from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)


# ==========================================================
# Cause Classification
# ==========================================================


# These describe system state rather than
# a root cause. They remain useful evidence,
# but should not win the RCA ranking.
NON_ROOT_CAUSES = {
    "SERVICE_DEGRADATION",
    "PERSISTENT_DEGRADATION",
}


# Broad causes receive a lower specificity
# weight than specific root-cause hypotheses.
#
# This prevents a generic:
#
#     CELL_OR_NETWORK
#
# from automatically outranking a more
# actionable specific cause when both have
# similar evidence support.
CAUSE_SPECIFICITY_WEIGHT = {
    "CELL_OR_NETWORK": 0.65,

    "CONGESTION_OR_BACKHAUL": 1.0,
    "COVERAGE_OR_PROPAGATION": 1.0,
    "INTERFERENCE": 1.0,
    "OUTAGE": 1.0,

    "DEVICE_MODEL_OR_FIRMWARE": 1.0,

    "TERRAIN_PROPAGATION_LIKELY": 1.0,
    "VEGETATION_PROPAGATION_POSSIBLE": 0.95,
    "WEATHER_STRESS_POSSIBLE": 0.95,
}


# ==========================================================
# Utility Functions
# ==========================================================


def clamp01(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            float(value),
        ),
    )


def noisy_or(
    values: list[float],
) -> float:
    """
    Combine multiple independent-ish
    pieces of evidence without simple
    unbounded addition.

    Example:
    0.80 + 0.80 should not become 1.60.

    Noisy-OR:
    1 - Π(1 - evidence)
    """

    if not values:
        return 0.0

    clean_values = [
        clamp01(value)
        for value in values
    ]

    return clamp01(
        1.0
        - prod(
            1.0 - value
            for value in clean_values
        )
    )


def confidence_label(
    confidence: float,
) -> str:
    if confidence >= 0.85:
        return "VERY_HIGH"

    if confidence >= 0.70:
        return "HIGH"

    if confidence >= 0.50:
        return "MODERATE"

    if confidence >= 0.30:
        return "LOW"

    return "VERY_LOW"


# ==========================================================
# Evidence Strength
# ==========================================================


def support_strength(
    evidence: RCAEvidence,
) -> float:
    """
    Effective supporting strength.

    Raw support alone is not enough.
    We discount evidence using:

    reliability
    freshness
    specificity
    gate
    """

    if evidence.gate_passed is False:
        return 0.0

    return clamp01(
        float(
            evidence.support_score
        )
        * float(
            evidence.reliability_score
        )
        * float(
            evidence.freshness_score
        )
        * float(
            evidence.specificity_score
        )
    )


def contradiction_strength(
    evidence: RCAEvidence,
) -> float:
    """
    Calculate contradiction strength.

    There are two patterns in our
    current evidence model:

    1. Evidence supports one hypothesis
       while contradicting another.

       Example:
       DEVICE_MODEL_PATTERN supports
       DEVICE_MODEL_OR_FIRMWARE and
       contradicts CELL_OR_NETWORK.

       In this case support_score is
       already the evidence strength.

    2. Evidence only contradicts a cause.

       Example:
       LOS is CLEAR and therefore
       contradicts terrain obstruction.

       Current builder stores a low
       support_score for this healthy/
       negative observation, so its
       inverse becomes the contradiction
       strength.
    """

    if evidence.supports_causes:
        raw = float(
            evidence.support_score
        )

    else:
        raw = max(
            0.25,
            1.0
            - float(
                evidence.support_score
            ),
        )

    return clamp01(
        raw
        * float(
            evidence.reliability_score
        )
        * float(
            evidence.freshness_score
        )
        * float(
            evidence.specificity_score
        )
    )


def diversity_factor(
    evidence_count: int,
) -> float:
    """
    Prevent one isolated evidence item
    from producing near-100% confidence.

    More independent evidence items
    increase confidence.
    """

    if evidence_count <= 0:
        return 0.0

    if evidence_count == 1:
        return 0.85

    if evidence_count == 2:
        return 0.93

    return 1.0


# ==========================================================
# Candidate Cause Collection
# ==========================================================


def collect_candidate_causes(
    evidence_items: list[RCAEvidence],
) -> set[str]:
    causes: set[str] = set()

    for item in evidence_items:
        for cause in (
            item.supports_causes
            or []
        ):
            if cause not in NON_ROOT_CAUSES:
                causes.add(
                    cause
                )

        for cause in (
            item.contradicts_causes
            or []
        ):
            if cause not in NON_ROOT_CAUSES:
                causes.add(
                    cause
                )

    return causes


# ==========================================================
# Cause Evaluation
# ==========================================================


def evaluate_cause(
    *,
    cause: str,
    evidence_items: list[RCAEvidence],
) -> dict:
    support_values: list[float] = []

    contradiction_values: list[float] = []

    supporting_details: list[dict] = []

    contradicting_details: list[dict] = []

    for item in evidence_items:
        supports = (
            item.supports_causes
            or []
        )

        contradicts = (
            item.contradicts_causes
            or []
        )

        # --------------------------------------------------
        # Supporting Evidence
        # --------------------------------------------------

        if cause in supports:
            strength = (
                support_strength(
                    item
                )
            )

            if strength > 0:
                support_values.append(
                    strength
                )

                supporting_details.append(
                    {
                        "evidence_id":
                            item.id,

                        "evidence_key":
                            item.evidence_key,

                        "source":
                            item.source,

                        "category":
                            item.category,

                        "strength":
                            round(
                                strength,
                                4,
                            ),

                        "value":
                            item.value_json,
                    }
                )

        # --------------------------------------------------
        # Contradicting Evidence
        # --------------------------------------------------

        if cause in contradicts:
            strength = (
                contradiction_strength(
                    item
                )
            )

            if strength > 0:
                contradiction_values.append(
                    strength
                )

                contradicting_details.append(
                    {
                        "evidence_id":
                            item.id,

                        "evidence_key":
                            item.evidence_key,

                        "source":
                            item.source,

                        "category":
                            item.category,

                        "strength":
                            round(
                                strength,
                                4,
                            ),

                        "value":
                            item.value_json,
                    }
                )

    # ------------------------------------------------------
    # Aggregate Evidence
    # ------------------------------------------------------

    support_score = noisy_or(
        support_values
    )

    contradiction_score = noisy_or(
        contradiction_values
    )

    diversity = diversity_factor(
        len(
            supporting_details
        )
    )

    # ------------------------------------------------------
    # Contradiction Penalty
    # ------------------------------------------------------

    # Contradiction reduces but does not
    # automatically erase good evidence.
    contradiction_penalty = (
        1.0
        - (
            0.70
            * contradiction_score
        )
    )

    # ------------------------------------------------------
    # Cause Specificity
    # ------------------------------------------------------

    # Broad causes receive a lower weight.
    #
    # Specific causes default to 1.0.
    #
    # This means we do not need to explicitly
    # register every future specific cause here.
    cause_specificity = (
        CAUSE_SPECIFICITY_WEIGHT.get(
            cause,
            1.0,
        )
    )

    # ------------------------------------------------------
    # Final Confidence
    # ------------------------------------------------------

    confidence = clamp01(
        support_score
        * diversity
        * contradiction_penalty
        * cause_specificity
    )

    # ------------------------------------------------------
    # Sort Evidence
    # ------------------------------------------------------

    supporting_details.sort(
        key=lambda item:
            item["strength"],
        reverse=True,
    )

    contradicting_details.sort(
        key=lambda item:
            item["strength"],
        reverse=True,
    )

    # ------------------------------------------------------
    # Result
    # ------------------------------------------------------

    return {
        "cause":
            cause,

        "confidence":
            round(
                confidence,
                4,
            ),

        "confidence_percent":
            round(
                confidence * 100,
                2,
            ),

        "confidence_label":
            confidence_label(
                confidence
            ),

        "support_score":
            round(
                support_score,
                4,
            ),

        "contradiction_score":
            round(
                contradiction_score,
                4,
            ),

        "diversity_factor":
            round(
                diversity,
                4,
            ),

        "cause_specificity_weight":
            round(
                cause_specificity,
                4,
            ),

        "supporting_evidence_count":
            len(
                supporting_details
            ),

        "contradicting_evidence_count":
            len(
                contradicting_details
            ),

        "supporting_evidence":
            supporting_details,

        "contradicting_evidence":
            contradicting_details,
    }


# ==========================================================
# Evidence Fusion
# ==========================================================


def fuse_evidence(
    evidence_items: list[RCAEvidence],
) -> dict:
    candidates = (
        collect_candidate_causes(
            evidence_items
        )
    )

    rankings = [
        evaluate_cause(
            cause=cause,
            evidence_items=evidence_items,
        )
        for cause in candidates
    ]

    rankings.sort(
        key=lambda item:
            (
                item[
                    "confidence"
                ],
                item[
                    "support_score"
                ],
            ),
        reverse=True,
    )

    for index, result in enumerate(
        rankings,
        start=1,
    ):
        result[
            "rank"
        ] = index

    primary = (
        rankings[0]
        if rankings
        else None
    )

    return {
        "engine_type":
            "EVIDENCE_FUSION_V1",

        "primary_cause":
            (
                primary[
                    "cause"
                ]
                if primary
                else None
            ),

        "primary_confidence":
            (
                primary[
                    "confidence"
                ]
                if primary
                else 0.0
            ),

        "primary_confidence_percent":
            (
                primary[
                    "confidence_percent"
                ]
                if primary
                else 0.0
            ),

        "confidence_label":
            (
                primary[
                    "confidence_label"
                ]
                if primary
                else "VERY_LOW"
            ),

        "rankings":
            rankings,

        "note": (
            "Confidence is an "
            "evidence-fusion score, "
            "not yet a calibrated "
            "statistical probability."
        ),
    }


# ==========================================================
# Run Case Fusion
# ==========================================================


def run_case_fusion(
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

    if not evidence_items:
        raise ValueError(
            "RCA case has no evidence"
        )

    result = fuse_evidence(
        evidence_items
    )

    # Make endpoint idempotent:
    # running fusion again replaces
    # previous fusion predictions.
    db.execute(
        delete(
            RCAPrediction
        ).where(
            RCAPrediction.case_id
            == case.id,

            RCAPrediction.engine_type
            == "EVIDENCE_FUSION_V1",
        )
    )

    for ranking in result[
        "rankings"
    ]:
        prediction = RCAPrediction(
            case_id=case.id,

            engine_type=(
                "EVIDENCE_FUSION_V1"
            ),

            primary_cause=(
                ranking[
                    "cause"
                ]
            ),

            confidence=(
                ranking[
                    "confidence"
                ]
            ),

            rank=(
                ranking[
                    "rank"
                ]
            ),

            output_json=(
                ranking
            ),

            verifier_status=(
                "FUSED_NOT_VERIFIED"
            ),

            verifier_reason=None,
        )

        db.add(
            prediction
        )

    db.commit()

    return result

