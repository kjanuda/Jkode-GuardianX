from __future__ import annotations

from typing import Any


MIN_ROOT_CAUSE_CONFIDENCE = 0.50


def verify_structured_rca(
    *,
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    """
    Guardian X deterministic RCA verifier.

    The verifier is the final safety gate.

    Rules can later be extended with:
    - evidence provenance
    - freshness
    - blast radius
    - telemetry consistency
    - model calibration
    """

    reasons: list[str] = []

    confidence = float(
        diagnosis.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    primary = diagnosis.get(
        "primary_root_cause"
    )

    domain = diagnosis.get(
        "domain"
    )

    conditions = (
        diagnosis.get(
            "conditions"
        )
        or {}
    )

    if primary in {
        None,
        "",
        "UNKNOWN",
    }:
        reasons.append(
            "NO_SUPPORTED_ROOT_CAUSE"
        )

    if confidence < (
        MIN_ROOT_CAUSE_CONFIDENCE
    ):
        reasons.append(
            "ROOT_CAUSE_CONFIDENCE_TOO_LOW"
        )

    if domain == "UNKNOWN":
        reasons.append(
            "INCIDENT_DOMAIN_UNKNOWN"
        )

    if (
        primary
        == "DEVICE_MODEL_OR_FIRMWARE"
        and not conditions.get(
            "device_specific_pattern",
            False,
        )
    ):
        reasons.append(
            "DEVICE_CAUSE_WITHOUT_"
            "DEVICE_PATTERN"
        )

    if (
        primary
        == "WEATHER_STRESS_POSSIBLE"
        and not conditions.get(
            "weather_causal_evidence",
            False,
        )
    ):
        reasons.append(
            "WEATHER_CAUSE_WITHOUT_"
            "WEATHER_EVIDENCE"
        )

    verified = (
        len(reasons) == 0
    )

    return {
        **diagnosis,

        "verification_required":
            True,

        "verification_status":
            (
                "VERIFIED"
                if verified
                else "REJECTED"
            ),

        "verification_reasons":
            reasons,

        "verified":
            verified,
    }


# ==========================================================
# Evidence-Aware Verification
# ==========================================================


MIN_EVIDENCE_FRESHNESS = 0.50

MIN_EVIDENCE_RELIABILITY = 0.60

STRONG_CONTRADICTION_THRESHOLD = 0.65


CAUSE_REQUIREMENTS = {
    "COVERAGE_OR_PROPAGATION": {
        "domain":
            "PROPAGATION_DOMAIN",

        "evidence_key":
            "CELL_COVERAGE_SIGNATURE",
    },

    "TERRAIN_PROPAGATION_LIKELY": {
        "domain":
            "PROPAGATION_DOMAIN",

        "evidence_key":
            "CELL_TERRAIN_CONTEXT",
    },

    "VEGETATION_PROPAGATION_POSSIBLE": {
        "domain":
            "PROPAGATION_DOMAIN",

        "evidence_key":
            "CELL_VEGETATION_CONTEXT",
    },

    "WEATHER_STRESS_POSSIBLE": {
        "domain":
            "PROPAGATION_DOMAIN",

        "evidence_key":
            "CELL_WEATHER_CONTEXT",
    },

    "CONGESTION_OR_BACKHAUL": {
        "domain":
            "NETWORK_DOMAIN",

        "evidence_key":
            "CELL_CONGESTION_SIGNATURE",
    },

    "INTERFERENCE": {
        "domain":
            "NETWORK_DOMAIN",

        "evidence_key":
            "CELL_INTERFERENCE_SIGNATURE",
    },

    "OUTAGE": {
        "domain":
            "NETWORK_DOMAIN",

        "evidence_key":
            "CELL_OUTAGE_SIGNATURE",
    },

    "CELL_OR_NETWORK": {
        "domain":
            "NETWORK_DOMAIN",

        "evidence_key":
            "POPULATION_AFFECTED_RATIO",
    },

    "DEVICE_MODEL_OR_FIRMWARE": {
        "domain":
            "DEVICE_DOMAIN",

        "evidence_key":
            "DEVICE_MODEL_PATTERN",
    },
}


def effective_evidence_strength(
    evidence,
) -> float:
    """
    Calculate the effective strength of an
    evidence item.

    Failed evidence gates contribute zero.
    """

    if evidence.gate_passed is False:
        return 0.0

    return (
        float(
            evidence.support_score
            or 0.0
        )
        * float(
            evidence.reliability_score
            or 0.0
        )
        * float(
            evidence.freshness_score
            or 0.0
        )
        * float(
            evidence.specificity_score
            or 0.0
        )
    )


def verify_structured_rca_with_evidence(
    *,
    diagnosis: dict[str, Any],
    evidence_items: list,
) -> dict[str, Any]:
    """
    Guardian X final deterministic verifier.

    Layer 1:
        structured diagnosis validation.

    Layer 2:
        actual RCA evidence validation.
    """

    base_result = (
        verify_structured_rca(
            diagnosis=diagnosis
        )
    )

    reasons = list(
        base_result.get(
            "verification_reasons"
        )
        or []
    )

    primary = (
        diagnosis.get(
            "primary_root_cause"
        )
    )

    domain = (
        diagnosis.get(
            "domain"
        )
    )

    requirement = (
        CAUSE_REQUIREMENTS.get(
            primary
        )
    )

    # -----------------------------------------
    # Domain / cause consistency
    # -----------------------------------------

    if requirement is not None:
        expected_domain = (
            requirement[
                "domain"
            ]
        )

        if domain != expected_domain:
            reasons.append(
                "DOMAIN_CAUSE_MISMATCH"
            )

    # -----------------------------------------
    # Required evidence
    # -----------------------------------------

    if requirement is not None:
        required_key = (
            requirement[
                "evidence_key"
            ]
        )

        matching = [
            item
            for item in evidence_items
            if item.evidence_key
            == required_key
        ]

        if not matching:
            reasons.append(
                "REQUIRED_EVIDENCE_MISSING:"
                f"{required_key}"
            )

        else:
            # Normally one item per key.
            # Using strongest item makes this
            # safe if duplicates ever exist.
            evidence = max(
                matching,
                key=lambda item:
                    effective_evidence_strength(
                        item
                    ),
            )

            if evidence.gate_passed is False:
                reasons.append(
                    "REQUIRED_EVIDENCE_"
                    "GATE_FAILED:"
                    f"{required_key}"
                )

            freshness = float(
                evidence.freshness_score
                or 0.0
            )

            if freshness < (
                MIN_EVIDENCE_FRESHNESS
            ):
                reasons.append(
                    "REQUIRED_EVIDENCE_STALE:"
                    f"{required_key}"
                )

            reliability = float(
                evidence.reliability_score
                or 0.0
            )

            if reliability < (
                MIN_EVIDENCE_RELIABILITY
            ):
                reasons.append(
                    "REQUIRED_EVIDENCE_"
                    "LOW_RELIABILITY:"
                    f"{required_key}"
                )

            supported_causes = (
                evidence.supports_causes
                or []
            )

            if (
                primary
                not in supported_causes
            ):
                reasons.append(
                    "REQUIRED_EVIDENCE_"
                    "DOES_NOT_SUPPORT_CAUSE:"
                    f"{required_key}"
                )

    # -----------------------------------------
    # Strong contradiction guard
    # -----------------------------------------

    for evidence in evidence_items:
        contradicted_causes = (
            evidence.contradicts_causes
            or []
        )

        if (
            primary
            not in contradicted_causes
        ):
            continue

        if evidence.gate_passed is False:
            continue

        contradiction_strength = (
            effective_evidence_strength(
                evidence
            )
        )

        if (
            contradiction_strength
            >= STRONG_CONTRADICTION_THRESHOLD
        ):
            reasons.append(
                "ROOT_CAUSE_STRONGLY_"
                "CONTRADICTED:"
                f"{evidence.evidence_key}"
            )

    # -----------------------------------------
    # Remove duplicate reasons
    # -----------------------------------------

    reasons = list(
        dict.fromkeys(
            reasons
        )
    )

    verified = (
        len(reasons) == 0
    )

    return {
        **base_result,

        "verification_status":
            (
                "VERIFIED"
                if verified
                else "REJECTED"
            ),

        "verification_reasons":
            reasons,

        "verified":
            verified,
    }