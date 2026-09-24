from __future__ import annotations

from math import (
    asin,
    atan2,
    cos,
    radians,
    sin,
    sqrt,
)
from typing import Callable


EARTH_RADIUS_M = 6_371_000.0


def haversine_distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    lat1_r = radians(lat1)
    lon1_r = radians(lon1)
    lat2_r = radians(lat2)
    lon2_r = radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (
        sin(dlat / 2.0) ** 2
        + cos(lat1_r)
        * cos(lat2_r)
        * sin(dlon / 2.0) ** 2
    )

    c = 2.0 * asin(
        min(
            1.0,
            sqrt(a),
        )
    )

    return EARTH_RADIUS_M * c


def interpolate_coordinate(
    *,
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    fraction: float,
) -> tuple[float, float]:
    """
    Linear geographic interpolation.

    Suitable for the relatively short
    tower-device paths used by Guardian X.
    """

    fraction = max(
        0.0,
        min(
            1.0,
            fraction,
        ),
    )

    lat = (
        lat1
        + (
            lat2 - lat1
        )
        * fraction
    )

    lon = (
        lon1
        + (
            lon2 - lon1
        )
        * fraction
    )

    return lat, lon


def build_dem_profile(
    *,
    tx_latitude: float,
    tx_longitude: float,
    rx_latitude: float,
    rx_longitude: float,
    elevation_lookup: Callable[
        [float, float],
        float | None,
    ],
    sample_count: int = 41,
) -> list[dict]:
    """
    Generate an ordered Tx → Rx terrain
    profile using the existing Guardian X
    elevation provider.

    elevation_lookup must accept:

        latitude, longitude

    and return elevation in metres.
    """

    if sample_count < 3:
        raise ValueError(
            "sample_count must be >= 3"
        )

    total_distance_m = (
        haversine_distance_m(
            tx_latitude,
            tx_longitude,
            rx_latitude,
            rx_longitude,
        )
    )

    if total_distance_m <= 0:
        raise ValueError(
            "Tx and Rx locations must differ"
        )

    samples: list[dict] = []

    for index in range(
        sample_count
    ):
        fraction = (
            index
            / (
                sample_count - 1
            )
        )

        latitude, longitude = (
            interpolate_coordinate(
                lat1=tx_latitude,
                lon1=tx_longitude,
                lat2=rx_latitude,
                lon2=rx_longitude,
                fraction=fraction,
            )
        )

        elevation = elevation_lookup(
            latitude,
            longitude,
        )

        if elevation is None:
            raise RuntimeError(
                "Elevation provider returned "
                f"no data at sample {index}: "
                f"{latitude}, {longitude}"
            )

        samples.append(
            {
                "distance_m":
                    round(
                        total_distance_m
                        * fraction,
                        2,
                    ),

                "elevation_m":
                    float(
                        elevation
                    ),

                "latitude":
                    round(
                        latitude,
                        7,
                    ),

                "longitude":
                    round(
                        longitude,
                        7,
                    ),
            }
        )

    return samples