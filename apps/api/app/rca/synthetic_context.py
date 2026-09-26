from __future__ import annotations

import os


FIXTURE_ENV = (
    "GUARDIANX_SYNTHETIC_TERRAIN_FIXTURES"
)

FIXTURE_SOURCE = (
    "SYNTHETIC_TERRAIN_FIXTURE_V1"
)

GENERIC_FIXTURE_SOURCE = (
    "SYNTHETIC_GENERIC_PROPAGATION_CONTEXT_V1"
)


TERRAIN_PROFILE_FIXTURES = {
    "mild": {
        "geo_vulnerability_score": 72.0,
        "fresnel_occupancy_pct": 40.0,
        "los_blocked_pct": 35.0,
        "minimum_clearance_ratio": -4.2,
        "maximum_fresnel_intrusion_m": 42.0,
    },

    "moderate": {
        "geo_vulnerability_score": 78.0,
        "fresnel_occupancy_pct": 48.27,
        "los_blocked_pct": 42.53,
        "minimum_clearance_ratio": -5.38,
        "maximum_fresnel_intrusion_m": 51.25,
    },

    "severe": {
        "geo_vulnerability_score": 82.0,
        "fresnel_occupancy_pct": 54.02,
        "los_blocked_pct": 47.12,
        "minimum_clearance_ratio": -6.97,
        "maximum_fresnel_intrusion_m": 67.01,
    },
}


def fixtures_enabled() -> bool:
    value = os.getenv(
        FIXTURE_ENV,
        "",
    )

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_coverage_scenario(
    scenario: str,
) -> tuple[str, str] | None:
    """
    Parse controlled synthetic coverage scenarios.

    Expected forms:
      population_coverage_generic_mild
      population_coverage_generic_moderate
      population_coverage_generic_severe

      population_coverage_terrain_mild
      population_coverage_terrain_moderate
      population_coverage_terrain_severe
    """

    prefix = "population_coverage_"

    if not scenario.startswith(
        prefix
    ):
        return None

    remainder = scenario[
        len(prefix):
    ]

    parts = remainder.split(
        "_",
        1,
    )

    if len(parts) != 2:
        return None

    subtype = parts[0]
    profile_name = parts[1]

    if subtype not in {
        "generic",
        "terrain",
    }:
        return None

    if (
        profile_name
        not in TERRAIN_PROFILE_FIXTURES
    ):
        return None

    return (
        subtype,
        profile_name,
    )


def build_synthetic_risk_context(
    telemetry,
) -> dict | None:
    if not fixtures_enabled():
        return None

    scenario = (
        telemetry.scenario
        or ""
    )

    parsed = get_coverage_scenario(
        scenario
    )

    if parsed is None:
        return None

    subtype, profile_name = parsed

    # ======================================================
    # Generic coverage / propagation
    # ======================================================
    #
    # RF degradation exists, but no terrain obstruction is
    # asserted. This prevents generic coverage cases from
    # being promoted into TERRAIN_PROPAGATION_LIKELY.
    # ======================================================

    if subtype == "generic":
        return {
            "_context_source":
                GENERIC_FIXTURE_SOURCE,

            "_synthetic_profile":
                profile_name,

            "_synthetic_subtype":
                "generic",

            "los_status":
                "CLEAR",

            "propagation_risk":
                "LOW",

            "geo_vulnerability_score":
                20.0,

            "environment_type":
                "UNAVAILABLE",

            "environmental_vulnerability_score":
                0.0,

            "environmental_vulnerability_level":
                "UNAVAILABLE",

            "weather_context_score":
                10.0,

            "historical_health_score":
                85.0,

            "historical_health":
                "HEALTHY",

            "fresnel_v2": {
                "status":
                    "CLEAR",

                "fresnel_occupancy_pct":
                    0.0,

                "los_blocked_pct":
                    0.0,

                "minimum_clearance_ratio":
                    1.5,

                "maximum_fresnel_intrusion_m":
                    0.0,

                "worst_obstruction":
                    None,
            },
        }

    # ======================================================
    # Terrain-driven coverage / propagation
    # ======================================================

    fixture = (
        TERRAIN_PROFILE_FIXTURES[
            profile_name
        ]
    )

    return {
        "_context_source":
            FIXTURE_SOURCE,

        "_synthetic_profile":
            profile_name,

        "_synthetic_subtype":
            "terrain",

        "los_status":
            "BLOCKED",

        "propagation_risk":
            "HIGH",

        "geo_vulnerability_score":
            fixture[
                "geo_vulnerability_score"
            ],

        "environment_type":
            "UNAVAILABLE",

        "environmental_vulnerability_score":
            0.0,

        "environmental_vulnerability_level":
            "UNAVAILABLE",

        "weather_context_score":
            10.0,

        "historical_health_score":
            85.0,

        "historical_health":
            "HEALTHY",

        "fresnel_v2": {
            "status":
                "BLOCKED",

            "fresnel_occupancy_pct":
                fixture[
                    "fresnel_occupancy_pct"
                ],

            "los_blocked_pct":
                fixture[
                    "los_blocked_pct"
                ],

            "minimum_clearance_ratio":
                fixture[
                    "minimum_clearance_ratio"
                ],

            "maximum_fresnel_intrusion_m":
                fixture[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                None,
        },
    }