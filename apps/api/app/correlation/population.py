
from collections import defaultdict
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DeviceProfile,
    Telemetry,
)


def is_affected(
    telemetry: Telemetry,
) -> bool:
    poor_radio = False
    poor_network = False

    # -------------------------
    # Radio degradation
    # -------------------------

    if (
        telemetry.rsrp is not None
        and telemetry.rsrp < -105
    ):
        poor_radio = True

    if (
        telemetry.sinr is not None
        and telemetry.sinr < 7
    ):
        poor_radio = True

    if (
        telemetry.rsrq is not None
        and telemetry.rsrq <= -13
    ):
        poor_radio = True

    # -------------------------
    # Network degradation
    # -------------------------

    if (
        telemetry.download_mbps is not None
        and telemetry.download_mbps < 15
    ):
        poor_network = True

    if (
        telemetry.latency_ms is not None
        and telemetry.latency_ms > 80
    ):
        poor_network = True

    if (
        telemetry.packet_loss is not None
        and telemetry.packet_loss > 2
    ):
        poor_network = True

    return (
        poor_radio
        or poor_network
    )


def select_latest_per_device(
    rows: list[Telemetry],
) -> list[Telemetry]:
    latest = {}

    for row in rows:
        if row.device_id not in latest:
            latest[row.device_id] = row

    return list(latest.values())


def get_population_status(
    *,
    total_devices: int,
    affected_ratio: float,
) -> str:
    if total_devices < 5:
        return "INSUFFICIENT_POPULATION"

    if affected_ratio >= 0.60:
        return "WIDESPREAD_DEGRADATION"

    if affected_ratio >= 0.25:
        return "PARTIAL_DEGRADATION"

    return "NO_WIDESPREAD_DEGRADATION"


def get_sample_quality(
    total_devices: int,
) -> str:
    if total_devices < 5:
        return "INSUFFICIENT"

    if total_devices < 15:
        return "LOW"

    if total_devices < 30:
        return "MODERATE"

    return "STRONG"


def model_key(
    profile: DeviceProfile | None,
) -> str:
    if profile is None:
        return "UNKNOWN_DEVICE_MODEL"

    manufacturer = (
        profile.manufacturer
        or "UNKNOWN"
    )

    model = (
        profile.model_name
        or "UNKNOWN"
    )

    return (
        f"{manufacturer} / {model}"
    )


def detect_device_model_pattern(
    cohorts: list[dict],
    total_affected: int,
) -> str:
    if len(cohorts) < 2:
        return "INSUFFICIENT_MODEL_DIVERSITY"

    strong_candidates = []

    for cohort in cohorts:
        if (
            cohort["total_devices"] >= 3
            and cohort["affected_ratio"] >= 0.70
        ):
            strong_candidates.append(
                cohort
            )

    if len(strong_candidates) != 1:
        return "NO_MODEL_SPECIFIC_PATTERN"

    candidate = strong_candidates[0]

    other_total = sum(
        item["total_devices"]
        for item in cohorts
        if item["cohort_key"]
        != candidate["cohort_key"]
    )

    other_affected = sum(
        item["affected_devices"]
        for item in cohorts
        if item["cohort_key"]
        != candidate["cohort_key"]
    )

    if other_total == 0:
        return "INSUFFICIENT_CONTROL_GROUP"

    other_ratio = (
        other_affected
        / other_total
    )

    if other_ratio <= 0.30:
        return "DEVICE_MODEL_SPECIFIC_PATTERN"

    return "NO_MODEL_SPECIFIC_PATTERN"


def analyze_cell_population(
    *,
    db: Session,
    cell_id: int,
    cell_external_id: str,
    window_minutes: int,
) -> dict:
    window_end = datetime.now(
        timezone.utc
    )

    window_start = (
        window_end
        - timedelta(
            minutes=window_minutes
        )
    )

    rows = list(
        db.scalars(
            select(Telemetry)
            .where(
                Telemetry.cell_id == cell_id,
                Telemetry.timestamp >= window_start,
            )
            .order_by(
                Telemetry.timestamp.desc(),
                Telemetry.id.desc(),
            )
        ).all()
    )

    latest_rows = (
        select_latest_per_device(
            rows
        )
    )

    total_devices = len(
        latest_rows
    )

    affected_rows = [
        row
        for row in latest_rows
        if is_affected(row)
    ]

    affected_devices = len(
        affected_rows
    )

    healthy_devices = (
        total_devices
        - affected_devices
    )

    affected_ratio = (
        affected_devices
        / total_devices
        if total_devices
        else 0.0
    )

    device_ids = [
        row.device_id
        for row in latest_rows
    ]

    profile_map = {}

    if device_ids:
        profiles = db.scalars(
            select(DeviceProfile).where(
                DeviceProfile.device_id.in_(
                    device_ids
                )
            )
        ).all()

        profile_map = {
            profile.device_id: profile
            for profile in profiles
        }

    cohort_data = defaultdict(
        lambda: {
            "total": 0,
            "affected": 0,
        }
    )

    for row in latest_rows:
        key = model_key(
            profile_map.get(
                row.device_id
            )
        )

        cohort_data[key]["total"] += 1

        if is_affected(row):
            cohort_data[key]["affected"] += 1

    cohorts = []

    for key, stats in cohort_data.items():
        total = stats["total"]
        affected = stats["affected"]

        ratio = (
            affected / total
            if total
            else 0.0
        )

        cohorts.append(
            {
                "cohort_type": "DEVICE_MODEL",

                "cohort_key": key,

                "total_devices": total,

                "affected_devices": affected,

                "affected_ratio": round(
                    ratio,
                    4,
                ),

                "healthy_devices": (
                    total - affected
                ),
            }
        )

    cohorts.sort(
        key=lambda item:
            item["affected_ratio"],
        reverse=True,
    )

    population_status = (
        get_population_status(
            total_devices=total_devices,
            affected_ratio=affected_ratio,
        )
    )

    sample_quality = (
        get_sample_quality(
            total_devices
        )
    )

    model_pattern = (
        detect_device_model_pattern(
            cohorts,
            affected_devices,
        )
    )

    evidence = []

    evidence.append(
        (
            f"{affected_devices} of "
            f"{total_devices} devices "
            f"are currently affected "
            f"({affected_ratio * 100:.1f}%)."
        )
    )

    if (
        population_status
        == "WIDESPREAD_DEGRADATION"
    ):
        evidence.append(
            "Degradation is widespread "
            "across the cell population."
        )

    elif (
        population_status
        == "PARTIAL_DEGRADATION"
    ):
        evidence.append(
            "A substantial subset of the "
            "cell population is degraded."
        )

    if (
        model_pattern
        == "DEVICE_MODEL_SPECIFIC_PATTERN"
    ):
        evidence.append(
            "The degradation is concentrated "
            "in one device-model cohort while "
            "other device models remain "
            "comparatively healthy."
        )

        likely_scope = (
            "DEVICE_MODEL_OR_FIRMWARE"
        )

    elif (
        population_status
        in {
            "WIDESPREAD_DEGRADATION",
            "PARTIAL_DEGRADATION",
        }
    ):
        likely_scope = (
            "CELL_OR_NETWORK"
        )

    else:
        likely_scope = (
            "INDIVIDUAL_OR_LOCAL"
        )

    return {
        "scope_type": "CELL",

        "scope_ref": cell_external_id,

        "window_minutes": window_minutes,

        "window_start": window_start,

        "window_end": window_end,

        "total_devices": total_devices,

        "affected_devices": affected_devices,

        "healthy_devices": healthy_devices,

        "affected_ratio": round(
            affected_ratio,
            4,
        ),

        "population_status": population_status,

        "sample_quality": sample_quality,

        "model_cohorts": cohorts,

        "device_model_pattern": model_pattern,

        "likely_scope": likely_scope,

        "evidence": evidence,
    }
