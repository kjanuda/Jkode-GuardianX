from __future__ import annotations

import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAEvidence,
)


# ==========================================================
# Raw evidence -> feature mapping
# ==========================================================

FEATURE_EVIDENCE_MAP = {
    "population_affected_ratio":
        "POPULATION_AFFECTED_RATIO",

    "device_model_pattern":
        "DEVICE_MODEL_PATTERN",

    "population_sample_quality":
        "POPULATION_SAMPLE_QUALITY",

    "congestion_signature":
        "CELL_CONGESTION_SIGNATURE",

    "coverage_signature":
        "CELL_COVERAGE_SIGNATURE",

    "interference_signature":
        "CELL_INTERFERENCE_SIGNATURE",

    "outage_signature":
        "CELL_OUTAGE_SIGNATURE",

    "terrain_context":
        "CELL_TERRAIN_CONTEXT",

    "vegetation_context":
        "CELL_VEGETATION_CONTEXT",

    "weather_context":
        "CELL_WEATHER_CONTEXT",

    "historical_context":
        "CELL_HISTORICAL_CONTEXT",
}


# ==========================================================
# Exact 18 features used by RCA_RANDOM_FOREST_V1
#
# IMPORTANT:
# This is an explicit allowlist.
# Labels / provenance / scenario metadata must never enter it.
# ==========================================================

ML_FEATURE_COLUMNS = [
    "population_affected_ratio",

    "congestion_signature",
    "coverage_signature",
    "interference_signature",
    "outage_signature",

    "terrain_context",
    "vegetation_context",
    "historical_context",

    "affected_devices",
    "healthy_devices",

    "mean_los_blocked_pct",
    "mean_geo_vulnerability",
    "mean_fresnel_occupancy_pct",
    "mean_max_fresnel_intrusion_m",
    "mean_minimum_clearance_ratio",

    "mean_environmental_vulnerability",
    "mean_weather_score",

    "device_model_pattern",
]


def evidence_value(
    evidence: RCAEvidence | None,
) -> Any:
    if evidence is None:
        return None

    value_json = (
        evidence.value_json
        or {}
    )

    return value_json.get(
        "value"
    )


def build_features_from_evidence_map(
    evidence_map: dict[
        str,
        RCAEvidence,
    ],
) -> dict[str, Any]:

    features: dict[str, Any] = {}

    for (
        feature_name,
        evidence_key,
    ) in FEATURE_EVIDENCE_MAP.items():

        features[
            feature_name
        ] = evidence_value(
            evidence_map.get(
                evidence_key
            )
        )

    # ------------------------------------------------------
    # Continuous population / terrain / environment context
    # ------------------------------------------------------

    terrain = evidence_map.get(
        "CELL_TERRAIN_CONTEXT"
    )

    terrain_context = (
        terrain.context_json
        if terrain is not None
        else {}
    ) or {}


    vegetation = evidence_map.get(
        "CELL_VEGETATION_CONTEXT"
    )

    vegetation_context = (
        vegetation.context_json
        if vegetation is not None
        else {}
    ) or {}


    weather = evidence_map.get(
        "CELL_WEATHER_CONTEXT"
    )

    weather_context = (
        weather.context_json
        if weather is not None
        else {}
    ) or {}


    population = evidence_map.get(
        "POPULATION_AFFECTED_RATIO"
    )

    population_context = (
        population.context_json
        if population is not None
        else {}
    ) or {}


    features.update(
        {
            "total_devices":
                population_context.get(
                    "total_devices"
                ),

            "affected_devices":
                population_context.get(
                    "affected_devices"
                ),

            "healthy_devices":
                population_context.get(
                    "healthy_devices"
                ),

            "mean_los_blocked_pct":
                terrain_context.get(
                    "mean_los_blocked_pct"
                ),

            "mean_geo_vulnerability":
                terrain_context.get(
                    "mean_geo_vulnerability"
                ),

            "mean_fresnel_occupancy_pct":
                terrain_context.get(
                    "mean_fresnel_occupancy_pct"
                ),

            "mean_max_fresnel_intrusion_m":
                terrain_context.get(
                    "mean_max_fresnel_intrusion_m"
                ),

            "mean_minimum_clearance_ratio":
                terrain_context.get(
                    "mean_minimum_clearance_ratio"
                ),

            "mean_environmental_vulnerability":
                vegetation_context.get(
                    "mean_environmental_vulnerability"
                ),

            "mean_weather_score":
                weather_context.get(
                    "mean_weather_score"
                ),
        }
    )

    return features


def build_case_ml_features(
    *,
    db: Session,
    case_id: int,
) -> dict[str, Any]:

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
                == case_id
            )
            .order_by(
                RCAEvidence.id.asc()
            )
        ).all()
    )

    evidence_map = {
        item.evidence_key:
            item

        for item
        in evidence_items
    }

    raw_features = (
        build_features_from_evidence_map(
            evidence_map
        )
    )

    # Exact serving order / allowlist.
    features = {
        feature_name:
            raw_features.get(
                feature_name
            )

        for feature_name
        in ML_FEATURE_COLUMNS
    }

    return features


def validate_ml_features(
    features: dict[str, Any],
) -> None:

    missing = [
        name
        for name in ML_FEATURE_COLUMNS
        if features.get(
            name
        ) is None
    ]

    if missing:
        raise ValueError(
            "ML features incomplete: "
            + ", ".join(
                missing
            )
        )

    non_finite = []

    for name in ML_FEATURE_COLUMNS:

        value = features[
            name
        ]

        if isinstance(
            value,
            (int, float),
        ):
            if not math.isfinite(
                float(value)
            ):
                non_finite.append(
                    name
                )

    if non_finite:
        raise ValueError(
            "ML features contain non-finite values: "
            + ", ".join(
                non_finite
            )
        )
