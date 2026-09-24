from __future__ import annotations

from math import sqrt
from typing import Any


SPEED_OF_LIGHT_MPS = 299_792_458.0
EARTH_RADIUS_M = 6_371_000.0


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def fresnel_radius_m(
    *,
    frequency_mhz: float,
    d1_m: float,
    d2_m: float,
) -> float:
    """
    First Fresnel-zone radius.

    r = sqrt(
        wavelength * d1 * d2
        / (d1 + d2)
    )
    """

    if frequency_mhz <= 0:
        raise ValueError(
            "frequency_mhz must be > 0"
        )

    if d1_m < 0:
        raise ValueError(
            "d1_m must be >= 0"
        )

    if d2_m < 0:
        raise ValueError(
            "d2_m must be >= 0"
        )

    total = d1_m + d2_m

    if total <= 0:
        return 0.0

    wavelength_m = (
        SPEED_OF_LIGHT_MPS
        / (
            frequency_mhz
            * 1_000_000.0
        )
    )

    return sqrt(
        wavelength_m
        * d1_m
        * d2_m
        / total
    )


def earth_curvature_bulge_m(
    *,
    d1_m: float,
    d2_m: float,
    k_factor: float = 4.0 / 3.0,
) -> float:
    """
    Effective-Earth-radius curvature bulge.

    k = 4/3 is a common engineering
    approximation for standard atmosphere.
    """

    if d1_m < 0:
        raise ValueError(
            "d1_m must be >= 0"
        )

    if d2_m < 0:
        raise ValueError(
            "d2_m must be >= 0"
        )

    if k_factor <= 0:
        raise ValueError(
            "k_factor must be > 0"
        )

    effective_radius = (
        EARTH_RADIUS_M
        * k_factor
    )

    return (
        d1_m
        * d2_m
        / (
            2.0
            * effective_radius
        )
    )


def line_of_sight_altitude_m(
    *,
    tx_altitude_m: float,
    rx_altitude_m: float,
    distance_m: float,
    total_distance_m: float,
) -> float:
    """
    Calculate the straight-line altitude between
    transmitter and receiver at a given distance.
    """

    if total_distance_m <= 0:
        return tx_altitude_m

    fraction = clamp(
        distance_m
        / total_distance_m,
        0.0,
        1.0,
    )

    return (
        tx_altitude_m
        + (
            rx_altitude_m
            - tx_altitude_m
        )
        * fraction
    )


def classify_path(
    *,
    los_blocked_points: int,
    fresnel_occupied_points: int,
) -> str:
    """
    Classify the propagation path.

    BLOCKED:
        At least one terrain point intersects
        the direct line of sight.

    FRESNEL_OBSTRUCTED:
        LOS is clear, but at least one terrain
        point intrudes into the required Fresnel
        clearance zone.

    CLEAR:
        LOS and required Fresnel clearance are clear.
    """

    if los_blocked_points > 0:
        return "BLOCKED"

    if fresnel_occupied_points > 0:
        return "FRESNEL_OBSTRUCTED"

    return "CLEAR"


def analyze_fresnel_profile(
    *,
    samples: list[dict[str, Any]],
    frequency_mhz: float,
    tx_height_m: float = 30.0,
    rx_height_m: float = 1.5,
    clearance_fraction: float = 0.60,
    k_factor: float = 4.0 / 3.0,
) -> dict[str, Any]:
    """
    Analyze a DEM terrain path using Fresnel-zone
    and effective-Earth-radius calculations.

    Required sample format:

    {
        "distance_m": 500,
        "elevation_m": 420,
        "latitude": optional,
        "longitude": optional
    }

    Samples are sorted by distance from transmitter
    to receiver.

    Important:
        fresnel_occupancy_pct means percentage of
        interior sampled path points that intrude
        into the required Fresnel clearance zone.

        It is NOT geometric area occupancy.
    """

    if len(samples) < 3:
        raise ValueError(
            "At least 3 terrain samples "
            "are required"
        )

    if frequency_mhz <= 0:
        raise ValueError(
            "frequency_mhz must be > 0"
        )

    if tx_height_m < 0:
        raise ValueError(
            "tx_height_m must be >= 0"
        )

    if rx_height_m < 0:
        raise ValueError(
            "rx_height_m must be >= 0"
        )

    if not (
        0.0
        < clearance_fraction
        <= 1.0
    ):
        raise ValueError(
            "clearance_fraction must be "
            "between 0 and 1"
        )

    if k_factor <= 0:
        raise ValueError(
            "k_factor must be > 0"
        )

    samples = sorted(
        samples,
        key=lambda item: float(
            item["distance_m"]
        ),
    )

    first = samples[0]
    last = samples[-1]

    total_distance_m = float(
        last["distance_m"]
    )

    if total_distance_m <= 0:
        raise ValueError(
            "Path distance must be > 0"
        )

    tx_ground_m = float(
        first["elevation_m"]
    )

    rx_ground_m = float(
        last["elevation_m"]
    )

    tx_altitude_m = (
        tx_ground_m
        + tx_height_m
    )

    rx_altitude_m = (
        rx_ground_m
        + rx_height_m
    )

    analyzed_points: list[
        dict[str, Any]
    ] = []

    los_blocked_points = 0
    fresnel_occupied_points = 0

    minimum_clearance_ratio: (
        float | None
    ) = None

    maximum_los_intrusion_m = 0.0
    maximum_fresnel_intrusion_m = 0.0

    worst_point: dict[str, Any] | None = (
        None
    )

    # Endpoints are excluded because the
    # Fresnel radius is zero at Tx and Rx.
    interior_samples = samples[1:-1]

    for sample in interior_samples:
        distance_m = float(
            sample["distance_m"]
        )

        terrain_m = float(
            sample["elevation_m"]
        )

        # Keep the point inside the physical
        # path range even if malformed input
        # contains a distance outside the path.
        distance_m = clamp(
            distance_m,
            0.0,
            total_distance_m,
        )

        d1_m = distance_m

        d2_m = (
            total_distance_m
            - distance_m
        )

        los_altitude_m = (
            line_of_sight_altitude_m(
                tx_altitude_m=(
                    tx_altitude_m
                ),
                rx_altitude_m=(
                    rx_altitude_m
                ),
                distance_m=distance_m,
                total_distance_m=(
                    total_distance_m
                ),
            )
        )

        curvature_m = (
            earth_curvature_bulge_m(
                d1_m=d1_m,
                d2_m=d2_m,
                k_factor=k_factor,
            )
        )

        effective_terrain_m = (
            terrain_m
            + curvature_m
        )

        fresnel_radius = (
            fresnel_radius_m(
                frequency_mhz=(
                    frequency_mhz
                ),
                d1_m=d1_m,
                d2_m=d2_m,
            )
        )

        required_clearance_m = (
            fresnel_radius
            * clearance_fraction
        )

        actual_clearance_m = (
            los_altitude_m
            - effective_terrain_m
        )

        clearance_ratio = (
            actual_clearance_m
            / fresnel_radius
            if fresnel_radius > 0
            else 1.0
        )

        los_intrusion_m = max(
            0.0,
            effective_terrain_m
            - los_altitude_m,
        )

        required_clearance_altitude_m = (
            los_altitude_m
            - required_clearance_m
        )

        fresnel_intrusion_m = max(
            0.0,
            effective_terrain_m
            - required_clearance_altitude_m,
        )

        los_blocked = (
            los_intrusion_m > 0
        )

        fresnel_occupied = (
            fresnel_intrusion_m > 0
        )

        if los_blocked:
            los_blocked_points += 1

        if fresnel_occupied:
            fresnel_occupied_points += 1

        if (
            minimum_clearance_ratio
            is None
            or clearance_ratio
            < minimum_clearance_ratio
        ):
            minimum_clearance_ratio = (
                clearance_ratio
            )

        maximum_los_intrusion_m = max(
            maximum_los_intrusion_m,
            los_intrusion_m,
        )

        if (
            fresnel_intrusion_m
            > maximum_fresnel_intrusion_m
        ):
            maximum_fresnel_intrusion_m = (
                fresnel_intrusion_m
            )

            worst_point = {
                "distance_m": round(
                    distance_m,
                    2,
                ),
                "distance_ratio": round(
                    distance_m
                    / total_distance_m,
                    4,
                ),
                "latitude": sample.get(
                    "latitude"
                ),
                "longitude": sample.get(
                    "longitude"
                ),
                "terrain_elevation_m": round(
                    terrain_m,
                    2,
                ),
                "effective_terrain_m": round(
                    effective_terrain_m,
                    2,
                ),
                "los_altitude_m": round(
                    los_altitude_m,
                    2,
                ),
                "fresnel_radius_m": round(
                    fresnel_radius,
                    2,
                ),
                "required_clearance_m": round(
                    required_clearance_m,
                    2,
                ),
                "actual_clearance_m": round(
                    actual_clearance_m,
                    2,
                ),
                "fresnel_intrusion_m": round(
                    fresnel_intrusion_m,
                    2,
                ),
                "los_intrusion_m": round(
                    los_intrusion_m,
                    2,
                ),
            }

        analyzed_points.append(
            {
                "distance_m": round(
                    distance_m,
                    2,
                ),
                "terrain_elevation_m": round(
                    terrain_m,
                    2,
                ),
                "earth_bulge_m": round(
                    curvature_m,
                    4,
                ),
                "effective_terrain_m": round(
                    effective_terrain_m,
                    2,
                ),
                "los_altitude_m": round(
                    los_altitude_m,
                    2,
                ),
                "fresnel_radius_m": round(
                    fresnel_radius,
                    2,
                ),
                "required_clearance_m": round(
                    required_clearance_m,
                    2,
                ),
                "actual_clearance_m": round(
                    actual_clearance_m,
                    2,
                ),
                "clearance_ratio": round(
                    clearance_ratio,
                    4,
                ),
                "los_intrusion_m": round(
                    los_intrusion_m,
                    2,
                ),
                "fresnel_intrusion_m": round(
                    fresnel_intrusion_m,
                    2,
                ),
                "los_blocked": los_blocked,
                "fresnel_occupied": fresnel_occupied,
                "latitude": sample.get(
                    "latitude"
                ),
                "longitude": sample.get(
                    "longitude"
                ),
            }
        )

    total_interior = len(
        interior_samples
    )

    los_blocked_pct = (
        los_blocked_points
        / total_interior
        * 100.0
        if total_interior
        else 0.0
    )

    fresnel_occupancy_pct = (
        fresnel_occupied_points
        / total_interior
        * 100.0
        if total_interior
        else 0.0
    )

    status = classify_path(
        los_blocked_points=(
            los_blocked_points
        ),
        fresnel_occupied_points=(
            fresnel_occupied_points
        ),
    )

    return {
        "status": status,

        "frequency_mhz": (
            frequency_mhz
        ),

        "path_distance_m": round(
            total_distance_m,
            2,
        ),

        "tx_ground_elevation_m": round(
            tx_ground_m,
            2,
        ),

        "rx_ground_elevation_m": round(
            rx_ground_m,
            2,
        ),

        "tx_height_m": tx_height_m,

        "rx_height_m": rx_height_m,

        "tx_altitude_m": round(
            tx_altitude_m,
            2,
        ),

        "rx_altitude_m": round(
            rx_altitude_m,
            2,
        ),

        "clearance_fraction": (
            clearance_fraction
        ),

        "k_factor": round(
            k_factor,
            4,
        ),

        "sample_count": len(
            samples
        ),

        "interior_sample_count": (
            total_interior
        ),

        "los_blocked_points": (
            los_blocked_points
        ),

        "los_blocked_pct": round(
            los_blocked_pct,
            2,
        ),

        "fresnel_occupied_points": (
            fresnel_occupied_points
        ),

        "fresnel_occupancy_pct": round(
            fresnel_occupancy_pct,
            2,
        ),

        "minimum_clearance_ratio": (
            round(
                minimum_clearance_ratio,
                4,
            )
            if minimum_clearance_ratio
            is not None
            else None
        ),

        "maximum_los_intrusion_m": round(
            maximum_los_intrusion_m,
            2,
        ),

        "maximum_fresnel_intrusion_m": round(
            maximum_fresnel_intrusion_m,
            2,
        ),

        "worst_obstruction": (
            worst_point
        ),

        "profile": analyzed_points,
    }


def profile_to_fresnel_samples(
    *,
    profile: list[dict],
    path_distance_m: float,
) -> list[dict]:
    """
    Convert Guardian X's existing
    elevation profile into the distance-aware
    format required by Fresnel v2.

    The existing elevation profile is assumed
    to contain evenly distributed points along
    the path.

    Example input:

    [
        {
            "elevation_m": 120.0,
            "latitude": 6.92,
            "longitude": 79.86
        },
        ...
    ]

    Example output:

    [
        {
            "distance_m": 0.0,
            "elevation_m": 120.0,
            "latitude": 6.92,
            "longitude": 79.86
        },
        ...
    ]
    """

    if len(profile) < 3:
        raise ValueError(
            "Elevation profile must contain "
            "at least 3 points"
        )

    if path_distance_m <= 0:
        raise ValueError(
            "path_distance_m must be > 0"
        )

    intervals = len(profile) - 1

    samples: list[dict] = []

    for index, point in enumerate(profile):
        if "elevation_m" not in point:
            raise ValueError(
                f"Profile point {index} "
                "has no elevation_m"
            )

        try:
            elevation_m = float(
                point["elevation_m"]
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"Profile point {index} "
                "has an invalid elevation_m"
            ) from exc

        fraction = (
            index / intervals
        )

        distance_m = (
            path_distance_m
            * fraction
        )

        samples.append(
            {
                "distance_m": round(
                    distance_m,
                    2,
                ),

                "elevation_m": (
                    elevation_m
                ),

                "latitude": point.get(
                    "latitude"
                ),

                "longitude": point.get(
                    "longitude"
                ),
            }
        )

    return samples


def analyze_elevation_profile_v2(
    *,
    profile: list[dict],
    path_distance_m: float,
    frequency_mhz: float,
    tx_height_m: float = 30.0,
    rx_height_m: float = 1.5,
    clearance_fraction: float = 0.60,
    k_factor: float = 4.0 / 3.0,
) -> dict:
    """
    Analyze Guardian X's existing
    Open-Meteo / Copernicus elevation profile
    with Fresnel v2.

    This function acts as the integration
    wrapper between Guardian X's existing
    elevation-profile pipeline and the Fresnel
    analysis engine.
    """

    samples = (
        profile_to_fresnel_samples(
            profile=profile,
            path_distance_m=path_distance_m,
        )
    )

    return analyze_fresnel_profile(
        samples=samples,
        frequency_mhz=frequency_mhz,
        tx_height_m=tx_height_m,
        rx_height_m=rx_height_m,
        clearance_fraction=(
            clearance_fraction
        ),
        k_factor=k_factor,
    )