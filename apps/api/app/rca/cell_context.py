from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Device,
    Telemetry,
)

from app.correlation.population import (
    is_affected,
    select_latest_per_device,
)

from app.rca.synthetic_context import (
    build_synthetic_risk_context,
)


def mean(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return sum(values) / len(values)


def safe_mean(
    values: list[float],
) -> float | None:
    result = mean(values)

    if result is None:
        return None

    return round(
        result,
        2,
    )


def analyze_cell_context(
    *,
    db: Session,
    cell_id: int,
    window_start: datetime,
    window_end: datetime,
    max_devices: int = 3,
    history_limit: int = 10,
) -> dict:
    """
    Run the existing Guardian X risk/context
    engine on a small representative sample
    of affected devices.

    We intentionally do NOT execute DEM /
    weather / OSM / WorldCover analysis for
    every device in the population.

    That would be expensive and would also
    incorrectly treat correlated context
    observations as independent evidence.
    """

    rows = list(
        db.scalars(
            select(Telemetry)
            .where(
                Telemetry.cell_id == cell_id,
                Telemetry.timestamp >= window_start,
                Telemetry.timestamp <= window_end,
            )
            .order_by(
                Telemetry.timestamp.desc(),
                Telemetry.id.desc(),
            )
        ).all()
    )

    latest_rows = select_latest_per_device(rows)

    affected_rows = [
        row
        for row in latest_rows
        if is_affected(row)
    ]

    sampled_rows = affected_rows[:max_devices]

    contexts: list[dict] = []
    errors: list[str] = []

    # Local import avoids module-import
    # cycles with the API layer.
    from app.api.risk import (
        get_device_risk,
    )

    for row in sampled_rows:
        device = db.get(
            Device,
            row.device_id,
        )

        if device is None:
            continue

        # -----------------------------------------------------
        # Explicit synthetic terrain fixture path
        # -----------------------------------------------------

        synthetic_context = (
            build_synthetic_risk_context(
                row
            )
        )

        if synthetic_context is not None:
            contexts.append(
                synthetic_context
            )

            continue

        # -----------------------------------------------------
        # Normal production / live context path
        # -----------------------------------------------------

        try:
            risk = get_device_risk(
                device_external_id=device.device_id,
                history_limit=history_limit,
                db=db,
            )

            contexts.append(risk)

        except Exception as exc:
            errors.append(
                (
                    f"{device.device_id}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )
            )

    if not contexts:
        return {
            "context_available": False,

            "sampled_devices": len(
                sampled_rows
            ),

            "successful_devices": 0,

            "errors": errors,

            "context_sources": [],

            "los_blocked_ratio": 0.0,

            "propagation_high_ratio": 0.0,

            "vegetation_heavy_ratio": 0.0,

            "environment_high_ratio": 0.0,

            "weather_elevated_ratio": 0.0,

            "historical_poor_ratio": 0.0,

            "mean_geo_vulnerability": None,

            "mean_environmental_vulnerability": None,

            "mean_weather_score": None,

            "mean_historical_health": None,

            # Fresnel V2 defaults
            "fresnel_v2_available_ratio": 0.0,

            "mean_fresnel_occupancy_pct": None,

            "mean_los_blocked_pct": None,

            "mean_minimum_clearance_ratio": None,

            "mean_max_fresnel_intrusion_m": None,

            "worst_fresnel_obstruction": None,
        }

    total = len(contexts)

    context_sources = sorted(
        {
            str(
                item.get(
                    "_context_source",
                    "LIVE_RISK_CONTEXT",
                )
            )
            for item in contexts
        }
    )

    def fraction(
        predicate,
    ) -> float:
        count = sum(
            1
            for item in contexts
            if predicate(item)
        )

        return round(
            count / total,
            4,
        )

    # ---------------------------------------------------------
    # Fresnel V2 context
    # ---------------------------------------------------------

    fresnel_contexts = [
        item.get(
            "fresnel_v2"
        )
        for item in contexts
        if isinstance(
            item.get(
                "fresnel_v2"
            ),
            dict,
        )
    ]

    # ---------------------------------------------------------
    # Existing aggregate values
    # ---------------------------------------------------------

    geo_values = [
        float(
            item[
                "geo_vulnerability_score"
            ]
        )
        for item in contexts
        if item.get(
            "geo_vulnerability_score"
        ) is not None
    ]

    environment_values = [
        float(
            item[
                "environmental_vulnerability_score"
            ]
        )
        for item in contexts
        if item.get(
            "environmental_vulnerability_score"
        ) is not None
    ]

    weather_values = [
        float(
            item[
                "weather_context_score"
            ]
        )
        for item in contexts
        if item.get(
            "weather_context_score"
        ) is not None
    ]

    history_values = [
        float(
            item[
                "historical_health_score"
            ]
        )
        for item in contexts
        if item.get(
            "historical_health_score"
        ) is not None
    ]

    # ---------------------------------------------------------
    # Fresnel V2 aggregate values
    # ---------------------------------------------------------

    fresnel_occupancy_values = [
        float(
            item[
                "fresnel_occupancy_pct"
            ]
        )
        for item in fresnel_contexts
        if item.get(
            "fresnel_occupancy_pct"
        ) is not None
    ]

    fresnel_los_values = [
        float(
            item[
                "los_blocked_pct"
            ]
        )
        for item in fresnel_contexts
        if item.get(
            "los_blocked_pct"
        ) is not None
    ]

    clearance_ratio_values = [
        float(
            item[
                "minimum_clearance_ratio"
            ]
        )
        for item in fresnel_contexts
        if item.get(
            "minimum_clearance_ratio"
        ) is not None
    ]

    fresnel_intrusion_values = [
        float(
            item[
                "maximum_fresnel_intrusion_m"
            ]
        )
        for item in fresnel_contexts
        if item.get(
            "maximum_fresnel_intrusion_m"
        ) is not None
    ]

    # ---------------------------------------------------------
    # Worst Fresnel obstruction
    # ---------------------------------------------------------

    worst_fresnel = None

    if fresnel_contexts:
        worst_fresnel = max(
            fresnel_contexts,
            key=lambda item:
                float(
                    item.get(
                        "maximum_fresnel_intrusion_m",
                        0.0,
                    )
                    or 0.0
                ),
        )

    # ---------------------------------------------------------
    # Final aggregated cell context
    # ---------------------------------------------------------

    return {
        "context_available": True,

        "context_sources":
            context_sources,

        "sampled_devices": len(
            sampled_rows
        ),

        "successful_devices": total,

        "errors": errors,

        # Existing context
        "los_blocked_ratio": fraction(
            lambda item:
                item.get(
                    "los_status"
                )
                == "BLOCKED"
        ),

        "propagation_high_ratio": fraction(
            lambda item:
                item.get(
                    "propagation_risk"
                )
                == "HIGH"
        ),

        "vegetation_heavy_ratio": fraction(
            lambda item:
                item.get(
                    "environment_type"
                )
                == "VEGETATION_HEAVY"
        ),

        "environment_high_ratio": fraction(
            lambda item:
                item.get(
                    "environmental_vulnerability_level"
                )
                == "HIGH"
        ),

        "weather_elevated_ratio": fraction(
            lambda item:
                float(
                    item.get(
                        "weather_context_score",
                        0,
                    )
                )
                >= 25
        ),

        "historical_poor_ratio": fraction(
            lambda item:
                item.get(
                    "historical_health"
                )
                in {
                    "POOR",
                    "CRITICAL",
                }
        ),

        "mean_geo_vulnerability": safe_mean(
            geo_values
        ),

        "mean_environmental_vulnerability": safe_mean(
            environment_values
        ),

        "mean_weather_score": safe_mean(
            weather_values
        ),

        "mean_historical_health": safe_mean(
            history_values
        ),

        # -----------------------------------------------------
        # Fresnel V2 aggregation
        # -----------------------------------------------------

        "fresnel_v2_available_ratio": round(
            len(
                fresnel_contexts
            )
            / total,
            4,
        ),

        "mean_fresnel_occupancy_pct": safe_mean(
            fresnel_occupancy_values
        ),

        "mean_los_blocked_pct": safe_mean(
            fresnel_los_values
        ),

        "mean_minimum_clearance_ratio": safe_mean(
            clearance_ratio_values
        ),

        "mean_max_fresnel_intrusion_m": safe_mean(
            fresnel_intrusion_values
        ),

        "worst_fresnel_obstruction": (
            worst_fresnel.get(
                "worst_obstruction"
            )
            if worst_fresnel
            else None
        ),
    }