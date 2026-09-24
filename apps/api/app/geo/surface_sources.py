from __future__ import annotations

from math import (
    asin,
    cos,
    radians,
    sin,
    sqrt,
)

from app.geo.osm_context import (
    OSMContextError,
    fetch_osm_building_features,
)

from app.geo.worldcover import (
    WorldCoverError,
    get_worldcover_class_at_point,
)


EARTH_RADIUS_M = 6_371_000.0


def distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    lat1_r = radians(lat1)
    lat2_r = radians(lat2)

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1_r)
        * cos(lat2_r)
        * sin(dlon / 2) ** 2
    )

    return (
        EARTH_RADIUS_M
        * 2
        * asin(
            min(
                1.0,
                sqrt(a),
            )
        )
    )


def midpoint(
    profile: list[dict],
) -> tuple[float, float]:
    index = len(profile) // 2

    return (
        float(
            profile[index][
                "latitude"
            ]
        ),
        float(
            profile[index][
                "longitude"
            ]
        ),
    )


def nearest_sample_index(
    *,
    latitude: float,
    longitude: float,
    profile: list[dict],
) -> tuple[int, float]:
    best_index = 0
    best_distance = float("inf")

    for index, point in enumerate(profile):
        candidate = distance_m(
            latitude,
            longitude,
            float(
                point[
                    "latitude"
                ]
            ),
            float(
                point[
                    "longitude"
                ]
            ),
        )

        if candidate < best_distance:
            best_distance = candidate
            best_index = index

    return (
        best_index,
        best_distance,
    )


def project_point_to_path(
    *,
    latitude: float,
    longitude: float,
    profile: list[dict],
) -> dict:
    """
    Project a geographic point onto the
    straight Guardian X Tx -> Rx path.

    Returns:

    - nearest sample index
    - cross-track distance
    - path fraction
    - along-path distance

    This is more accurate than comparing
    a building only against sparse DEM
    sample centers.
    """

    if len(profile) < 2:
        raise ValueError(
            "profile must contain "
            "at least 2 points"
        )

    start = profile[0]
    end = profile[-1]

    lat0 = float(
        start["latitude"]
    )

    lon0 = float(
        start["longitude"]
    )

    lat1 = float(
        end["latitude"]
    )

    lon1 = float(
        end["longitude"]
    )

    mean_lat_rad = radians(
        (
            lat0
            + lat1
            + latitude
        )
        / 3.0
    )

    def to_xy(
        lat: float,
        lon: float,
    ) -> tuple[float, float]:
        x = (
            radians(
                lon - lon0
            )
            * EARTH_RADIUS_M
            * cos(
                mean_lat_rad
            )
        )

        y = (
            radians(
                lat - lat0
            )
            * EARTH_RADIUS_M
        )

        return x, y

    end_x, end_y = to_xy(
        lat1,
        lon1,
    )

    point_x, point_y = to_xy(
        latitude,
        longitude,
    )

    path_length_sq = (
        end_x ** 2
        + end_y ** 2
    )

    if path_length_sq <= 0:
        raise ValueError(
            "Invalid zero-length path"
        )

    path_fraction = (
        (
            point_x * end_x
            + point_y * end_y
        )
        / path_length_sq
    )

    path_fraction = max(
        0.0,
        min(
            1.0,
            path_fraction,
        ),
    )

    closest_x = (
        end_x
        * path_fraction
    )

    closest_y = (
        end_y
        * path_fraction
    )

    cross_track_distance_m = sqrt(
        (
            point_x
            - closest_x
        ) ** 2
        +
        (
            point_y
            - closest_y
        ) ** 2
    )

    path_length_m = sqrt(
        path_length_sq
    )

    sample_index = round(
        path_fraction
        * (
            len(profile)
            - 1
        )
    )

    sample_index = max(
        0,
        min(
            len(profile) - 1,
            sample_index,
        ),
    )

    return {
        "sample_index": sample_index,
        "path_fraction": round(
            path_fraction,
            6,
        ),
        "cross_track_distance_m": round(
            cross_track_distance_m,
            2,
        ),
        "along_path_m": round(
            path_length_m
            * path_fraction,
            2,
        ),
    }


def vegetation_height_estimate(
    class_name: str,
) -> dict | None:
    """
    Screening assumptions only.

    ESA WorldCover does NOT contain measured
    canopy height. These are deliberately
    lower-confidence inferred heights.
    """

    if class_name == "TREE_COVER":
        return {
            "height_m": 12.0,
            "surface_type": "TREE",
            "source": (
                "ESA_WORLDCOVER_"
                "INFERRED_TREE_HEIGHT"
            ),
            "confidence": 0.4,
        }

    if class_name == "MANGROVES":
        return {
            "height_m": 8.0,
            "surface_type": "VEGETATION",
            "source": (
                "ESA_WORLDCOVER_"
                "INFERRED_MANGROVE_HEIGHT"
            ),
            "confidence": 0.4,
        }

    if class_name == "SHRUBLAND":
        return {
            "height_m": 2.0,
            "surface_type": "VEGETATION",
            "source": (
                "ESA_WORLDCOVER_"
                "INFERRED_SHRUB_HEIGHT"
            ),
            "confidence": 0.3,
        }

    return None


def build_real_surface_obstructions(
    *,
    terrain_profile: list[dict],
    building_match_distance_m: float = 35.0,
) -> dict:
    """
    Build DSM-ready obstruction candidates.

    Building:
        OSM explicit/levels-derived heights.

    Vegetation:
        WorldCover class + inferred screening
        height.

    Every obstruction keeps provenance so
    downstream RCA logic can distinguish
    observed/explicit data from inferred data.
    """

    if len(terrain_profile) < 3:
        raise ValueError(
            "terrain_profile must have "
            "at least 3 points"
        )

    obstructions: list[dict] = []
    errors: list[str] = []

    # -----------------------------------------
    # WorldCover per interior sample
    # -----------------------------------------

    for index, point in enumerate(
        terrain_profile
    ):
        if (
            index == 0
            or index
            == len(terrain_profile) - 1
        ):
            continue

        try:
            landcover = (
                get_worldcover_class_at_point(
                    latitude=float(
                        point[
                            "latitude"
                        ]
                    ),
                    longitude=float(
                        point[
                            "longitude"
                        ]
                    ),
                )
            )

        except WorldCoverError as exc:
            errors.append(
                f"WorldCover sample "
                f"{index}: {exc}"
            )
            continue

        class_name = landcover[
            "class_name"
        ]

        estimate = (
            vegetation_height_estimate(
                class_name
            )
        )

        if estimate is None:
            continue

        obstructions.append(
            {
                "sample_index": index,

                "height_m": float(
                    estimate[
                        "height_m"
                    ]
                ),

                "surface_type": (
                    estimate[
                        "surface_type"
                    ]
                ),

                "source": (
                    estimate[
                        "source"
                    ]
                ),

                "confidence": float(
                    estimate[
                        "confidence"
                    ]
                ),

                "landcover_class":
                    class_name,

                "path_offset_m": 0.0,

                "along_path_m": None,

                "path_fraction": None,
            }
        )

    # -----------------------------------------
    # OSM building features
    # -----------------------------------------

    center_lat, center_lon = midpoint(
        terrain_profile
    )

    first = terrain_profile[0]
    last = terrain_profile[-1]

    path_length = distance_m(
        float(
            first[
                "latitude"
            ]
        ),
        float(
            first[
                "longitude"
            ]
        ),
        float(
            last[
                "latitude"
            ]
        ),
        float(
            last[
                "longitude"
            ]
        ),
    )

    search_radius = int(
        max(
            500,
            path_length / 2
            + 150,
        )
    )

    try:
        buildings = (
            fetch_osm_building_features(
                latitude=center_lat,
                longitude=center_lon,
                radius_m=search_radius,
            )
        )

    except OSMContextError as exc:
        buildings = []

        errors.append(
            f"OSM buildings: {exc}"
        )

    matched_buildings = 0

    # -----------------------------------------
    # Match buildings to actual Tx -> Rx path
    # -----------------------------------------

    for building in buildings:
        try:
            projection = (
                project_point_to_path(
                    latitude=float(
                        building[
                            "latitude"
                        ]
                    ),
                    longitude=float(
                        building[
                            "longitude"
                        ]
                    ),
                    profile=terrain_profile,
                )
            )

        except (
            TypeError,
            ValueError,
            KeyError,
        ) as exc:
            errors.append(
                "OSM building projection "
                f"failed: {exc}"
            )
            continue

        sample_index = projection[
            "sample_index"
        ]

        offset_m = projection[
            "cross_track_distance_m"
        ]

        # Never alter Tx/Rx endpoint ground.
        if (
            sample_index == 0
            or sample_index
            == len(
                terrain_profile
            ) - 1
        ):
            continue

        # Building must fall inside the
        # configured path corridor.
        if (
            offset_m
            > building_match_distance_m
        ):
            continue

        matched_buildings += 1

        obstructions.append(
            {
                "sample_index":
                    sample_index,

                "height_m":
                    float(
                        building[
                            "height_m"
                        ]
                    ),

                "surface_type":
                    "BUILDING",

                "source":
                    building[
                        "height_source"
                    ],

                "confidence":
                    float(
                        building[
                            "confidence"
                        ]
                    ),

                "osm_id":
                    building[
                        "osm_id"
                    ],

                "osm_type":
                    building[
                        "osm_type"
                    ],

                "building_type":
                    building.get(
                        "building_type"
                    ),

                "path_offset_m":
                    offset_m,

                "along_path_m":
                    projection[
                        "along_path_m"
                    ],

                "path_fraction":
                    projection[
                        "path_fraction"
                    ],
            }
        )

    # -----------------------------------------
    # Summary
    # -----------------------------------------

    return {
        "obstructions": obstructions,

        "worldcover_candidates":
            sum(
                1
                for item in obstructions
                if item[
                    "surface_type"
                ]
                in {
                    "TREE",
                    "VEGETATION",
                }
            ),

        "osm_building_candidates":
            matched_buildings,

        "osm_buildings_with_height":
            len(buildings),

        "search_radius_m":
            search_radius,

        "building_match_distance_m":
            building_match_distance_m,

        "errors":
            errors,
    }