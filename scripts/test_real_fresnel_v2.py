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

from app.geo.fresnel_v2 import (
    analyze_elevation_profile_v2,
)

from app.geo.path_profile import (
    haversine_distance_m,
)

from app.geo.propagation import (
    analyze_propagation,
)


# Current Guardian X demo path
TOWER_LATITUDE = 7.2906
TOWER_LONGITUDE = 80.6337

DEVICE_LATITUDE = 7.2800
DEVICE_LONGITUDE = 80.6600

FREQUENCY_MHZ = 2350.0

TOWER_HEIGHT_M = 30.0
DEVICE_HEIGHT_M = 1.5

SAMPLE_COUNT = 41


def main():
    print()
    print(
        "GUARDIAN X - REAL DEM "
        "FRESNEL V2 TEST"
    )
    print(
        "-" * 70
    )

    distance_m = (
        haversine_distance_m(
            TOWER_LATITUDE,
            TOWER_LONGITUDE,
            DEVICE_LATITUDE,
            DEVICE_LONGITUDE,
        )
    )

    print(
        f"Path distance : "
        f"{distance_m:.2f} m"
    )

    print(
        f"Frequency     : "
        f"{FREQUENCY_MHZ:.0f} MHz"
    )

    print(
        f"DEM samples   : "
        f"{SAMPLE_COUNT}"
    )

    print()
    print(
        "Fetching existing Guardian X "
        "elevation profile..."
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

            distance_m=distance_m,

            sample_count=(
                SAMPLE_COUNT
            ),
        )
    )

    print(
        "Elevation source : "
        f"{elevation['source']}"
    )

    print(
        "Terrain relief   : "
        f"{elevation['terrain_relief_m']} m"
    )

    print()
    print(
        "LEGACY PROPAGATION ENGINE"
    )
    print(
        "-" * 70
    )

    legacy = analyze_propagation(
        profile=(
            elevation[
                "profile"
            ]
        ),

        distance_m=distance_m,

        frequency_mhz=(
            FREQUENCY_MHZ
        ),

        tower_antenna_height_m=(
            TOWER_HEIGHT_M
        ),

        device_antenna_height_m=(
            DEVICE_HEIGHT_M
        ),
    )

    pprint(
        {
            "los_status":
                legacy[
                    "los_status"
                ],

            "propagation_risk":
                legacy[
                    "propagation_risk"
                ],

            "obstruction_score":
                legacy[
                    "obstruction_score"
                ],

            "obstructed_points":
                legacy[
                    "obstructed_points"
                ],

            "fresnel_obstructed_points":
                legacy[
                    "fresnel_obstructed_points"
                ],

            "minimum_terrain_clearance_m":
                legacy[
                    "minimum_terrain_clearance_m"
                ],

            "minimum_fresnel_60_clearance_m":
                legacy[
                    "minimum_fresnel_60_clearance_m"
                ],
        }
    )

    print()
    print(
        "FRESNEL V2 ENGINE"
    )
    print(
        "-" * 70
    )

    v2 = (
        analyze_elevation_profile_v2(
            profile=(
                elevation[
                    "profile"
                ]
            ),

            path_distance_m=(
                distance_m
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

            clearance_fraction=0.60,
        )
    )

    pprint(
        {
            "status":
                v2[
                    "status"
                ],

            "path_distance_m":
                v2[
                    "path_distance_m"
                ],

            "sample_count":
                v2[
                    "sample_count"
                ],

            "los_blocked_points":
                v2[
                    "los_blocked_points"
                ],

            "los_blocked_pct":
                v2[
                    "los_blocked_pct"
                ],

            "fresnel_occupied_points":
                v2[
                    "fresnel_occupied_points"
                ],

            "fresnel_occupancy_pct":
                v2[
                    "fresnel_occupancy_pct"
                ],

            "minimum_clearance_ratio":
                v2[
                    "minimum_clearance_ratio"
                ],

            "maximum_los_intrusion_m":
                v2[
                    "maximum_los_intrusion_m"
                ],

            "maximum_fresnel_intrusion_m":
                v2[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                v2[
                    "worst_obstruction"
                ],
        }
    )

    print()
    print(
        "ENGINE CONSISTENCY"
    )
    print(
        "-" * 70
    )

    legacy_blocked = (
        legacy[
            "los_status"
        ]
        == "BLOCKED"
    )

    v2_blocked = (
        v2[
            "status"
        ]
        == "BLOCKED"
    )

    print(
        "Legacy blocked :",
        legacy_blocked,
    )

    print(
        "V2 blocked     :",
        v2_blocked,
    )

    print(
        "LOS agreement  :",
        (
            "PASS"
            if legacy_blocked
            == v2_blocked
            else "CHECK"
        ),
    )


if __name__ == "__main__":
    main()