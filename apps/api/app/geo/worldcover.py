from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.windows import from_bounds

from app.core.config import settings


class WorldCoverError(Exception):
    pass


WORLD_COVER_CLASSES = {
    10: "TREE_COVER",
    20: "SHRUBLAND",
    30: "GRASSLAND",
    40: "CROPLAND",
    50: "BUILT_UP",
    60: "BARE_OR_SPARSE_VEGETATION",
    70: "SNOW_AND_ICE",
    80: "PERMANENT_WATER",
    90: "HERBACEOUS_WETLAND",
    95: "MANGROVES",
    100: "MOSS_AND_LICHEN",
}


def get_tile_origin(
    latitude: float,
    longitude: float,
) -> tuple[int, int]:
    lat_origin = (
        math.floor(latitude / 3) * 3
    )

    lon_origin = (
        math.floor(longitude / 3) * 3
    )

    return lat_origin, lon_origin


def format_tile_id(
    latitude: float,
    longitude: float,
) -> str:
    lat_origin, lon_origin = (
        get_tile_origin(
            latitude,
            longitude,
        )
    )

    if lat_origin >= 0:
        lat_code = (
            f"N{abs(lat_origin):02d}"
        )
    else:
        lat_code = (
            f"S{abs(lat_origin):02d}"
        )

    if lon_origin >= 0:
        lon_code = (
            f"E{abs(lon_origin):03d}"
        )
    else:
        lon_code = (
            f"W{abs(lon_origin):03d}"
        )

    return (
        f"{lat_code}{lon_code}"
    )


def get_tile_filename(
    tile_id: str,
) -> str:
    return (
        "ESA_WorldCover_10m_2021_"
        f"v200_{tile_id}_Map.tif"
    )


def ensure_worldcover_tile(
    latitude: float,
    longitude: float,
) -> tuple[Path, str]:
    tile_id = format_tile_id(
        latitude,
        longitude,
    )

    filename = get_tile_filename(
        tile_id
    )

    cache_dir = Path(
        settings.worldcover_cache_dir
    )

    cache_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    tile_path = (
        cache_dir / filename
    )

    if tile_path.exists():
        return tile_path, tile_id

    url = (
        f"{settings.worldcover_base_url}/"
        f"{filename}"
    )

    temporary_path = (
        tile_path.with_suffix(
            ".download"
        )
    )

    try:
        with requests.get(
            url,
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()

            with open(
                temporary_path,
                "wb",
            ) as output:
                for chunk in (
                    response.iter_content(
                        chunk_size=1024 * 1024
                    )
                ):
                    if chunk:
                        output.write(
                            chunk
                        )

        temporary_path.replace(
            tile_path
        )

    except (
        requests.RequestException,
        OSError,
    ) as exc:
        if temporary_path.exists():
            temporary_path.unlink()

        raise WorldCoverError(
            f"Could not download "
            f"WorldCover tile {tile_id}"
        ) from exc

    return tile_path, tile_id


def calculate_bounds(
    latitude: float,
    longitude: float,
    radius_m: int,
):
    latitude_delta = (
        radius_m / 111_320
    )

    longitude_scale = (
        111_320
        * math.cos(
            math.radians(latitude)
        )
    )

    longitude_delta = (
        radius_m / longitude_scale
    )

    return (
        longitude - longitude_delta,
        latitude - latitude_delta,
        longitude + longitude_delta,
        latitude + latitude_delta,
    )


def build_class_distribution(
    values: np.ndarray,
) -> list[dict]:
    valid_values = values[
        np.isin(
            values,
            list(
                WORLD_COVER_CLASSES.keys()
            ),
        )
    ]

    if valid_values.size == 0:
        raise WorldCoverError(
            "No valid WorldCover pixels "
            "found in requested area"
        )

    unique, counts = np.unique(
        valid_values,
        return_counts=True,
    )

    total = int(
        counts.sum()
    )

    distribution = []

    for code, count in zip(
        unique,
        counts,
    ):
        code = int(code)
        count = int(count)

        percentage = (
            count / total
        ) * 100

        distribution.append(
            {
                "code": code,

                "class_name":
                    WORLD_COVER_CLASSES[
                        code
                    ],

                "pixel_count":
                    count,

                "percentage":
                    round(
                        percentage,
                        2,
                    ),
            }
        )

    distribution.sort(
        key=lambda item:
            item["percentage"],
        reverse=True,
    )

    return distribution


def get_percentage(
    distribution: list[dict],
    code: int,
) -> float:
    for item in distribution:
        if item["code"] == code:
            return item["percentage"]

    return 0.0


def get_worldcover_context(
    latitude: float,
    longitude: float,
    radius_m: int = 500,
) -> dict:
    tile_path, tile_id = (
        ensure_worldcover_tile(
            latitude,
            longitude,
        )
    )

    try:
        with rasterio.open(
            tile_path
        ) as dataset:
            row, col = dataset.index(
                longitude,
                latitude,
            )

            center_value = int(
                dataset.read(
                    1,
                    window=(
                        (
                            row,
                            row + 1,
                        ),
                        (
                            col,
                            col + 1,
                        ),
                    ),
                )[0, 0]
            )

            bounds = calculate_bounds(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
            )

            window = from_bounds(
                *bounds,
                transform=dataset.transform,
            )

            data = dataset.read(
                1,
                window=window,
                boundless=True,
                fill_value=0,
            )

            window_transform = (
                dataset.window_transform(
                    window
                )
            )

    except Exception as exc:
        raise WorldCoverError(
            "Could not read WorldCover raster"
        ) from exc

    # -------------------------------------------------
    # Create circular radius mask
    # instead of using the full square window.
    # -------------------------------------------------

    rows, cols = np.indices(
        data.shape
    )

    xs = (
        window_transform.c
        + (
            cols + 0.5
        )
        * window_transform.a
    )

    ys = (
        window_transform.f
        + (
            rows + 0.5
        )
        * window_transform.e
    )

    latitude_distance_m = (
        (ys - latitude)
        * 111_320
    )

    longitude_distance_m = (
        (xs - longitude)
        * 111_320
        * math.cos(
            math.radians(
                latitude
            )
        )
    )

    distance_m = np.sqrt(
        latitude_distance_m ** 2
        + longitude_distance_m ** 2
    )

    circular_mask = (
        distance_m <= radius_m
    )

    circular_values = (
        data[circular_mask]
    )

    distribution = (
        build_class_distribution(
            circular_values
        )
    )

    if (
        center_value
        not in WORLD_COVER_CLASSES
    ):
        center_class_name = "UNKNOWN"
    else:
        center_class_name = (
            WORLD_COVER_CLASSES[
                center_value
            ]
        )

    dominant = distribution[0]

    return {
        "center_class_code":
            center_value,

        "center_class_name":
            center_class_name,

        "dominant_class":
            dominant[
                "class_name"
            ],

        "dominant_percentage":
            dominant[
                "percentage"
            ],

        "tree_cover_pct":
            get_percentage(
                distribution,
                10,
            ),

        "shrubland_pct":
            get_percentage(
                distribution,
                20,
            ),

        "grassland_pct":
            get_percentage(
                distribution,
                30,
            ),

        "cropland_pct":
            get_percentage(
                distribution,
                40,
            ),

        "built_up_pct":
            get_percentage(
                distribution,
                50,
            ),

        "water_pct":
            get_percentage(
                distribution,
                80,
            ),

        "wetland_pct":
            (
                get_percentage(
                    distribution,
                    90,
                )
                + get_percentage(
                    distribution,
                    95,
                )
            ),

        "class_distribution":
            distribution,

        "tile_id":
            tile_id,

        "year":
            2021,

        "resolution_m":
            10,

        "source":
            (
                "ESA WorldCover 2021 v200 "
                "/ Sentinel-1 + Sentinel-2"
            ),
    }


def get_worldcover_class_at_point(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Return the ESA WorldCover class for one
    geographic point.

    This is land-cover classification only.

    It does NOT provide:
    - tree height
    - canopy height
    - building height
    - obstruction height
    - DSM elevation

    WorldCover classification can be used to
    identify the surface/land-cover type at
    the point, while height information should
    come from a separate DSM / OSM / LiDAR /
    building-height source.
    """

    tile_path, tile_id = (
        ensure_worldcover_tile(
            latitude,
            longitude,
        )
    )

    try:
        with rasterio.open(
            tile_path
        ) as dataset:
            row, col = dataset.index(
                longitude,
                latitude,
            )

            value = int(
                dataset.read(
                    1,
                    window=(
                        (
                            row,
                            row + 1,
                        ),
                        (
                            col,
                            col + 1,
                        ),
                    ),
                )[0, 0]
            )

    except Exception as exc:
        raise WorldCoverError(
            "Could not read WorldCover "
            "point classification"
        ) from exc

    return {
        "class_code":
            value,

        "class_name":
            WORLD_COVER_CLASSES.get(
                value,
                "UNKNOWN",
            ),

        "tile_id":
            tile_id,

        "source":
            "ESA WorldCover 2021 v200",

        "resolution_m":
            10,
    }