from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)


STRUCTURED_ENGINE = (
    "STRUCTURED_RCA_V1"
)

CONSENSUS_ENGINE = (
    "RCA_CONSENSUS_V1"
)


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


def latest_prediction(
    *,
    db: Session,
    case_id: int,
    engine_type: str,
) -> RCAPrediction | None:
    return db.scalar(
        select(
            RCAPrediction
        )
        .where(
            RCAPrediction.case_id
            == case_id,

            RCAPrediction.engine_type
            == engine_type,
        )
        .order_by(
            RCAPrediction.created_at.desc(),
            RCAPrediction.id.desc(),
        )
        .limit(1)
    )


def build_case_training_row(
    *,
    db: Session,
    case: RCACase,
) -> dict[str, Any] | None:
    structured = latest_prediction(
        db=db,
        case_id=case.id,
        engine_type=STRUCTURED_ENGINE,
    )

    # -----------------------------------------
    # Only deterministic verified RCA cases
    # may become labelled ML examples.
    # -----------------------------------------

    if structured is None:
        return None

    structured_output = (
        structured.output_json
        or {}
    )

    if (
        structured.verifier_status
        != "VERIFIED"
        or structured_output.get(
            "verified"
        )
        is not True
    ):
        return None

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

    evidence_map = {
        item.evidence_key: item
        for item in evidence_items
    }

    consensus = latest_prediction(
        db=db,
        case_id=case.id,
        engine_type=CONSENSUS_ENGINE,
    )

    consensus_output = (
        consensus.output_json
        if consensus is not None
        else {}
    ) or {}

    consensus_status = (
        consensus_output.get(
            "consensus_status"
        )
        if consensus is not None
        else None
    )

    human_review_required = (
        consensus_output.get(
            "human_review_required"
        )
        if consensus is not None
        else None
    )

    features = {}

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

    # -----------------------------------------
    # Additional continuous context features
    # -----------------------------------------

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

    root_cause = (
        structured_output.get(
            "primary_root_cause"
        )
        or structured.primary_cause
    )

    domain = structured_output.get(
        "domain"
    )

    confidence = (
        structured_output.get(
            "confidence"
        )
    )

    # For now, only consensus-agreement rows
    # are considered high-quality training rows.
    #
    # We retain other verified rows in the
    # exported dataset but mark them ineligible.

    training_eligible = (
        consensus_status
        == "AGREEMENT"
        and human_review_required
        is False
    )

    return {
        "case_id":
            case.id,

        "case_uuid":
            case.case_uuid,

        "scope_type":
            case.scope_type,

        "scope_ref":
            case.scope_ref,

        "trigger_type":
            case.trigger_type,

        "risk_score":
            case.risk_score,

        "risk_level":
            case.risk_level,

        **features,

        # Labels
        "label_domain":
            domain,

        "label_primary_cause":
            root_cause,

        # Metadata — not model features
        "label_confidence":
            confidence,

        "structured_verified":
            True,

        "consensus_status":
            consensus_status,

        "human_review_required":
            human_review_required,

        "training_eligible":
            training_eligible,

        "created_at":
            (
                case.created_at.isoformat()
                if case.created_at
                else None
            ),
    }


def build_rca_dataset(
    *,
    db: Session,
) -> list[dict[str, Any]]:
    cases = list(
        db.scalars(
            select(
                RCACase
            )
            .order_by(
                RCACase.id.asc()
            )
        ).all()
    )

    rows = []

    for case in cases:
        row = (
            build_case_training_row(
                db=db,
                case=case,
            )
        )

        if row is not None:
            rows.append(
                row
            )

    return rows