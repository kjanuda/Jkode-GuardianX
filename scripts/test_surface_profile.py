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


from app.geo.surface_profile import (
    analyze_surface_profile,
    build_surface_profile,
)


def terrain_profile():
    return [
        {
            "latitude": 7.2900,
            "longitude": 80.6300,
            "elevation_m": 100,
        },
        {
            "latitude": 7.2890,
            "longitude": 80.6310,
            "elevation_m": 98,
        },
        {
            "latitude": 7.2880,
            "longitude": 80.6320,
            "elevation_m": 97,
        },
        {
            "latitude": 7.2870,
            "longitude": 80.6330,
            "elevation_m": 96,
        },
        {
            "latitude": 7.2860,
            "longitude": 80.6340,
            "elevation_m": 100,
        },
    ]


def main():
    terrain = terrain_profile()

    print()
    print("TERRAIN ONLY")
    print("-" * 60)

    terrain_surface = (
        build_surface_profile(
            terrain_profile=terrain,
        )
    )

    terrain_result = (
        analyze_surface_profile(
            surface_profile=(
                terrain_surface
            ),
            path_distance_m=2000,
            frequency_mhz=2350,
            tx_height_m=30,
            rx_height_m=10,
        )
    )

    pprint(
        {
            "status":
                terrain_result[
                    "status"
                ],

            "fresnel_occupancy_pct":
                terrain_result[
                    "fresnel_occupancy_pct"
                ],

            "surface_context":
                terrain_result[
                    "surface_context"
                ],
        }
    )


    print()
    print("BUILDING OBSTRUCTION")
    print("-" * 60)

    building_surface = (
        build_surface_profile(
            terrain_profile=terrain,

            surface_obstructions=[
                {
                    "sample_index": 2,
                    "height_m": 35,
                    "surface_type":
                        "BUILDING",
                    "source":
                        "TEST_DSM",
                    "confidence":
                        1.0,
                }
            ],
        )
    )

    building_result = (
        analyze_surface_profile(
            surface_profile=(
                building_surface
            ),
            path_distance_m=2000,
            frequency_mhz=2350,
            tx_height_m=30,
            rx_height_m=10,
        )
    )

    pprint(
        {
            "status":
                building_result[
                    "status"
                ],

            "los_blocked_pct":
                building_result[
                    "los_blocked_pct"
                ],

            "fresnel_occupancy_pct":
                building_result[
                    "fresnel_occupancy_pct"
                ],

            "maximum_fresnel_intrusion_m":
                building_result[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                building_result[
                    "worst_obstruction"
                ],

            "surface_context":
                building_result[
                    "surface_context"
                ],
        }
    )


    print()
    print("VEGETATION OBSTRUCTION")
    print("-" * 60)

    vegetation_surface = (
        build_surface_profile(
            terrain_profile=terrain,

            surface_obstructions=[
                {
                    "sample_index": 2,
                    "height_m": 22,
                    "surface_type":
                        "TREE",
                    "source":
                        "TEST_DSM",
                    "confidence":
                        0.85,
                }
            ],
        )
    )

    vegetation_result = (
        analyze_surface_profile(
            surface_profile=(
                vegetation_surface
            ),
            path_distance_m=2000,
            frequency_mhz=2350,
            tx_height_m=30,
            rx_height_m=10,
        )
    )

    pprint(
        {
            "status":
                vegetation_result[
                    "status"
                ],

            "fresnel_occupancy_pct":
                vegetation_result[
                    "fresnel_occupancy_pct"
                ],

            "surface_context":
                vegetation_result[
                    "surface_context"
                ],
        }
    )


if __name__ == "__main__":
    main()