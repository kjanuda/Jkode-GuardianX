
import sys

from pathlib import Path
from pprint import pprint


API_ROOT = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "api"
)

if str(API_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(API_ROOT),
    )


from app.geo.elevation import (
    build_elevation_context,
)

from app.geo.path_profile import (
    haversine_distance_m,
)

from app.geo.surface_profile import (
    analyze_surface_profile,
    build_surface_profile,
)

from app.geo.surface_sources import (
    build_real_surface_obstructions,
)


TOWER_LATITUDE = 7.2906
TOWER_LONGITUDE = 80.6337

DEVICE_LATITUDE = 7.2800
DEVICE_LONGITUDE = 80.6600

FREQUENCY_MHZ = 2350.0

TOWER_HEIGHT_M = 30.0
DEVICE_HEIGHT_M = 1.5

# DEM-native sample density.
#
# ~3.13 km path / 40 intervals
# ≈ 78 m spacing.
#
# This provides a reasonable sampling
# density for Copernicus DEM GLO-90
# while keeping the profile lightweight.
SAMPLE_COUNT = 41


def main():
    print()
    print(
        "GUARDIAN X - REAL SURFACE "
        "PROFILE TEST"
    )

    print(
        "-" * 70
    )

    distance = (
        haversine_distance_m(
            TOWER_LATITUDE,
            TOWER_LONGITUDE,
            DEVICE_LATITUDE,
            DEVICE_LONGITUDE,
        )
    )

    elevation = (
        build_elevation_context(
            tower_latitude=(
                TOWER_LATITUDE
            ),
            tower_longitude=(
                TOWER_LONGITUDE
            ),
            device_latitude=(
                DEVICE_LATITUDE
            ),
            device_longitude=(
                DEVICE_LONGITUDE
            ),
            distance_m=distance,
            sample_count=(
                SAMPLE_COUNT
            ),
        )
    )

    sources = (
        build_real_surface_obstructions(
            terrain_profile=(
                elevation[
                    "profile"
                ]
            )
        )
    )

    surface_profile = (
        build_surface_profile(
            terrain_profile=(
                elevation[
                    "profile"
                ]
            ),
            surface_obstructions=(
                sources[
                    "obstructions"
                ]
            ),
        )
    )

    result = (
        analyze_surface_profile(
            surface_profile=(
                surface_profile
            ),
            path_distance_m=distance,
            frequency_mhz=(
                FREQUENCY_MHZ
            ),
            tx_height_m=(
                TOWER_HEIGHT_M
            ),
            rx_height_m=(
                DEVICE_HEIGHT_M
            ),
        )
    )

    print()
    print(
        "PATH SUMMARY"
    )

    print(
        "-" * 70
    )

    pprint(
        {
            "path_distance_m":
                round(
                    distance,
                    2,
                ),

            "sample_count":
                SAMPLE_COUNT,

            "approx_spacing_m":
                round(
                    distance
                    / (
                        SAMPLE_COUNT
                        - 1
                    ),
                    2,
                ),

            "frequency_mhz":
                FREQUENCY_MHZ,

            "tower_height_m":
                TOWER_HEIGHT_M,

            "device_height_m":
                DEVICE_HEIGHT_M,
        }
    )

    print()
    print(
        "SOURCE SUMMARY"
    )

    print(
        "-" * 70
    )

    pprint(
        {
            "worldcover_candidates":
                sources[
                    "worldcover_candidates"
                ],

            "osm_building_candidates":
                sources[
                    "osm_building_candidates"
                ],

            "osm_buildings_with_height":
                sources[
                    "osm_buildings_with_height"
                ],

            "search_radius_m":
                sources[
                    "search_radius_m"
                ],

            "building_match_distance_m":
                sources.get(
                    "building_match_distance_m"
                ),

            "errors":
                sources[
                    "errors"
                ],
        }
    )

    print()
    print(
        "SURFACE ANALYSIS"
    )

    print(
        "-" * 70
    )

    pprint(
        {
            "status":
                result[
                    "status"
                ],

            "los_blocked_pct":
                result[
                    "los_blocked_pct"
                ],

            "fresnel_occupancy_pct":
                result[
                    "fresnel_occupancy_pct"
                ],

            "maximum_fresnel_intrusion_m":
                result[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                result[
                    "worst_obstruction"
                ],

            "surface_context":
                result[
                    "surface_context"
                ],
        }
    )


if __name__ == "__main__":
    main()
