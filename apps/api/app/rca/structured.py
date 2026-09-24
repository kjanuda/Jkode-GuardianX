from __future__ import annotations

from typing import Any


ALLOWED_DOMAINS = {
    "DEVICE_DOMAIN",
    "NETWORK_DOMAIN",
    "PROPAGATION_DOMAIN",
    "UNKNOWN",
}


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


def build_structured_rca(
    *,
    case_id: int,
    hierarchy: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert hierarchical RCA output into a
    stable machine-readable diagnosis
    contract.

    No LLM is required here.
    """

    incident_domain = (
        hierarchy.get(
            "incident_domain"
        )
        or {}
    )

    primary = (
        hierarchy.get(
            "primary_root_cause"
        )
        or {}
    )

    contributors = (
        hierarchy.get(
            "contributing_factors"
        )
        or []
    )

    conditions = (
        hierarchy.get(
            "conditions"
        )
        or {}
    )

    domain_cause = (
        incident_domain.get(
            "cause"
        )
        or "UNKNOWN"
    )

    primary_cause = (
        primary.get(
            "cause"
        )
        or "UNKNOWN"
    )

    if primary_cause not in ALLOWED_CAUSES:
        primary_cause = "UNKNOWN"

    # Normalize incident domain.
    #
    # The upstream RCA hierarchy may provide either:
    #   - an explicit domain value
    #   - a concrete root-cause value
    #
    # Both forms are normalized into the stable
    # structured RCA domain contract.
    if domain_cause in {
        "PROPAGATION_DOMAIN",
        "COVERAGE_OR_PROPAGATION",
        "TERRAIN_PROPAGATION_LIKELY",
        "VEGETATION_PROPAGATION_POSSIBLE",
        "WEATHER_STRESS_POSSIBLE",
    }:
        domain = "PROPAGATION_DOMAIN"

    elif domain_cause in {
        "NETWORK_DOMAIN",
        "CONGESTION_OR_BACKHAUL",
        "CELL_OR_NETWORK",
        "INTERFERENCE",
        "OUTAGE",
    }:
        domain = "NETWORK_DOMAIN"

    elif domain_cause in {
        "DEVICE_DOMAIN",
        "DEVICE_MODEL_OR_FIRMWARE",
    }:
        domain = "DEVICE_DOMAIN"

    else:
        domain = "UNKNOWN"

    primary_confidence = clamp01(
        primary.get(
            "confidence",
            0.0,
        )
    )

    normalized_contributors = []

    for contributor in contributors:
        cause = contributor.get(
            "cause"
        )

        if cause not in ALLOWED_CAUSES:
            continue

        if cause == primary_cause:
            continue

        normalized_contributors.append(
            {
                "cause":
                    cause,

                "confidence":
                    clamp01(
                        contributor.get(
                            "confidence",
                            0.0,
                        )
                    ),

                "confidence_label":
                    contributor.get(
                        "confidence_label",
                        "UNKNOWN",
                    ),
            }
        )

    return {
        "engine_type":
            "STRUCTURED_RCA_V1",

        "schema_version":
            "RCA_STRUCTURED_V1",

        "case_id":
            case_id,

        "domain":
            domain,

        "incident_domain_cause":
            domain_cause,

        "primary_root_cause":
            primary_cause,

        "confidence":
            primary_confidence,

        "confidence_percent":
            round(
                primary_confidence * 100,
                2,
            ),

        "contributors":
            normalized_contributors,

        "conditions": {
            "persistent_degradation":
                bool(
                    conditions.get(
                        "persistent_degradation",
                        False,
                    )
                ),

            "weather_causal_evidence":
                bool(
                    conditions.get(
                        "weather_causal_evidence",
                        False,
                    )
                ),

            "device_specific_pattern":
                bool(
                    conditions.get(
                        "device_specific_pattern",
                        False,
                    )
                ),
        },

        "verification_required":
            True,

        "verification_status":
            "PENDING",

        "verification_reasons":
            [],
    }