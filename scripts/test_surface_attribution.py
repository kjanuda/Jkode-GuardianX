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

from app.geo.surface_attribution import (
    analyze_surface_attribution,
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

SAMPLE_COUNT = 41


def main():
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

    result = (
        analyze_surface_attribution(
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

            path_distance_m=(
                distance
            ),

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
        "GUARDIAN X - SURFACE "
        "ATTRIBUTION TEST"
    )

    print(
        "-" * 70
    )

    pprint(
        {
            "attribution":
                result[
                    "attribution"
                ],

            "terrain_only":
                result[
                    "terrain_only"
                ],

            "surface_aware":
                result[
                    "surface_aware"
                ],

            "delta":
                result[
                    "delta"
                ],

            "provenance":
                result[
                    "provenance"
                ],

            "gates":
                result[
                    "gates"
                ],
        }
    )


if __name__ == "__main__":
    main()