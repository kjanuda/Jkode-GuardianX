import hashlib
import json
from pathlib import Path
from statistics import mean
import time

import requests

from app.core.config import settings


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[4]
)

ELEVATION_CACHE_DIR = (
    PROJECT_ROOT
    / "data"
    / "cache"
    / "elevation"
)

ELEVATION_CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


class ElevationServiceError(Exception):
    pass


def interpolate_points(
    tower_latitude: float,
    tower_longitude: float,
    device_latitude: float,
    device_longitude: float,
    sample_count: int = 11,
) -> list[tuple[float, float]]:
    if sample_count < 2:
        raise ValueError(
            "sample_count must be at least 2"
        )

    points = []

    for index in range(sample_count):
        fraction = index / (
            sample_count - 1
        )

        latitude = (
            tower_latitude
            + (
                device_latitude
                - tower_latitude
            )
            * fraction
        )

        longitude = (
            tower_longitude
            + (
                device_longitude
                - tower_longitude
            )
            * fraction
        )

        points.append(
            (
                round(latitude, 6),
                round(longitude, 6),
            )
        )

    return points


def _elevation_cache_path(
    points: list[tuple[float, float]],
) -> Path:
    cache_payload = {
        "api_url": settings.elevation_api_url,
        "points": points,
    }

    serialized = json.dumps(
        cache_payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()

    return (
        ELEVATION_CACHE_DIR
        / f"{digest}.json"
    )


def _read_cached_elevations(
    points: list[tuple[float, float]],
) -> list[float] | None:
    cache_path = _elevation_cache_path(
        points
    )

    if not cache_path.exists():
        return None

    try:
        payload = json.loads(
            cache_path.read_text(
                encoding="utf-8"
            )
        )

        elevations = payload.get(
            "elevations"
        )

        if not isinstance(
            elevations,
            list,
        ):
            return None

        if len(elevations) != len(points):
            return None

        values = []

        for value in elevations:
            if value is None:
                return None

            values.append(
                float(value)
            )

        return values

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        return None


def _write_cached_elevations(
    points: list[tuple[float, float]],
    elevations: list[float],
) -> None:
    cache_path = _elevation_cache_path(
        points
    )

    payload = {
        "points": points,
        "elevations": elevations,
        "source": (
            "Open-Meteo Elevation API / "
            "Copernicus DEM GLO-90"
        ),
    }

    temporary_path = cache_path.with_name(
        (
            f"{cache_path.name}."
            f"{time.time_ns()}.tmp"
        )
    )

    try:
        temporary_path.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            cache_path
        )

    finally:
        if temporary_path.exists():
            temporary_path.unlink(
                missing_ok=True
            )


def _retry_delay_seconds(
    response: requests.Response,
    attempt: int,
) -> float:
    retry_after = response.headers.get(
        "Retry-After"
    )

    if retry_after:
        try:
            value = float(
                retry_after
            )

            return min(
                max(value, 1.0),
                15.0,
            )

        except ValueError:
            pass

    return (
        1.5
        * (
            2 ** attempt
        )
    )


def fetch_elevations(
    points: list[tuple[float, float]],
    retries: int = 2,
) -> list[float]:
    cached = _read_cached_elevations(
        points
    )

    if cached is not None:
        return cached

    latitudes = ",".join(
        str(latitude)
        for latitude, _ in points
    )

    longitudes = ",".join(
        str(longitude)
        for _, longitude in points
    )

    last_error: Exception | str | None = None

    transient_status_codes = {
        429,
        500,
        502,
        503,
        504,
    }

    for attempt in range(
        retries + 1
    ):
        try:
            response = requests.get(
                settings.elevation_api_url,
                params={
                    "latitude": latitudes,
                    "longitude": longitudes,
                },
                timeout=10,
            )

            if (
                response.status_code
                in transient_status_codes
            ):
                last_error = (
                    "Transient elevation "
                    f"HTTP {response.status_code}"
                )

                if attempt < retries:
                    delay_seconds = (
                        _retry_delay_seconds(
                            response=response,
                            attempt=attempt,
                        )
                    )

                    time.sleep(
                        delay_seconds
                    )

                    continue

                break

            response.raise_for_status()

            payload = response.json()

            elevations = payload.get(
                "elevation"
            )

            if not isinstance(
                elevations,
                list,
            ):
                raise ElevationServiceError(
                    "Elevation API returned "
                    "an invalid response"
                )

            if (
                len(elevations)
                != len(points)
            ):
                raise ElevationServiceError(
                    "Elevation API returned "
                    "an unexpected number "
                    "of values"
                )

            values = []

            for value in elevations:
                if value is None:
                    raise ElevationServiceError(
                        "Elevation API returned "
                        "a null elevation value"
                    )

                values.append(
                    float(value)
                )

            # Cache write is best-effort: a disk / permission
            # problem must not fail an otherwise good lookup.
            try:
                _write_cached_elevations(
                    points=points,
                    elevations=values,
                )
            except OSError:
                pass

            return values

        except (
            requests.RequestException,
            ValueError,
            ElevationServiceError,
        ) as exc:
            last_error = exc

            if attempt < retries:
                time.sleep(
                    1.5
                    * (
                        2 ** attempt
                    )
                )

                continue

            break

    raise ElevationServiceError(
        "Could not retrieve elevation "
        f"data after {retries + 1} attempts: "
        f"{last_error}"
    )


def build_elevation_context(
    tower_latitude: float,
    tower_longitude: float,
    device_latitude: float,
    device_longitude: float,
    distance_m: float,
    sample_count: int = 11,
) -> dict:
    points = interpolate_points(
        tower_latitude=tower_latitude,
        tower_longitude=tower_longitude,
        device_latitude=device_latitude,
        device_longitude=device_longitude,
        sample_count=sample_count,
    )

    elevations = fetch_elevations(
        points
    )

    tower_elevation = elevations[0]
    device_elevation = elevations[-1]

    elevation_difference = (
        device_elevation
        - tower_elevation
    )

    minimum_elevation = min(
        elevations
    )

    maximum_elevation = max(
        elevations
    )

    mean_elevation = mean(
        elevations
    )

    terrain_relief = (
        maximum_elevation
        - minimum_elevation
    )

    if distance_m > 0:
        endpoint_slope_percent = (
            elevation_difference
            / distance_m
        ) * 100
    else:
        endpoint_slope_percent = 0

    profile = []

    for (
        latitude,
        longitude,
    ), elevation in zip(
        points,
        elevations,
    ):
        profile.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "elevation_m": round(
                    elevation,
                    2,
                ),
            }
        )

    return {
        "tower_elevation_m": round(
            tower_elevation,
            2,
        ),

        "device_elevation_m": round(
            device_elevation,
            2,
        ),

        "elevation_difference_m": round(
            elevation_difference,
            2,
        ),

        "path_min_elevation_m": round(
            minimum_elevation,
            2,
        ),

        "path_max_elevation_m": round(
            maximum_elevation,
            2,
        ),

        "path_mean_elevation_m": round(
            mean_elevation,
            2,
        ),

        "terrain_relief_m": round(
            terrain_relief,
            2,
        ),

        "endpoint_slope_percent": round(
            endpoint_slope_percent,
            2,
        ),

        "sample_count": len(
            elevations
        ),

        "profile": profile,

        "source": (
            "Open-Meteo Elevation API / "
            "Copernicus DEM GLO-90"
        ),

        "resolution_m": 90,
    }