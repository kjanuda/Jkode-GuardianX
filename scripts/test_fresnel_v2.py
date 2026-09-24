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


from app.geo.fresnel_v2 import (
    analyze_fresnel_profile,
)


def clear_profile():
    return [
        {
            "distance_m": 0,
            "elevation_m": 100,
        },
        {
            "distance_m": 500,
            "elevation_m": 80,
        },
        {
            "distance_m": 1000,
            "elevation_m": 80,
        },
        {
            "distance_m": 1500,
            "elevation_m": 80,
        },
        {
            "distance_m": 2000,
            "elevation_m": 100,
        },
    ]


def blocked_profile():
    return [
        {
            "distance_m": 0,
            "elevation_m": 100,
        },
        {
            "distance_m": 500,
            "elevation_m": 95,
        },
        {
            "distance_m": 1000,
            "elevation_m": 135,
        },
        {
            "distance_m": 1500,
            "elevation_m": 95,
        },
        {
            "distance_m": 2000,
            "elevation_m": 100,
        },
    ]


def main():
    print()
    print("CLEAR PROFILE")
    print("-" * 60)

    clear_result = analyze_fresnel_profile(
        samples=clear_profile(),
        frequency_mhz=2350,
        tx_height_m=30,
        rx_height_m=10,
    )

    pprint(
        {
            "status":
                clear_result[
                    "status"
                ],

            "fresnel_occupancy_pct":
                clear_result[
                    "fresnel_occupancy_pct"
                ],

            "minimum_clearance_ratio":
                clear_result[
                    "minimum_clearance_ratio"
                ],

            "worst_obstruction":
                clear_result[
                    "worst_obstruction"
                ],
        }
    )


    print()
    print("BLOCKED PROFILE")
    print("-" * 60)

    blocked_result = analyze_fresnel_profile(
        samples=blocked_profile(),
        frequency_mhz=2350,
        tx_height_m=30,
        rx_height_m=10,
    )

    pprint(
        {
            "status":
                blocked_result[
                    "status"
                ],

            "los_blocked_pct":
                blocked_result[
                    "los_blocked_pct"
                ],

            "fresnel_occupancy_pct":
                blocked_result[
                    "fresnel_occupancy_pct"
                ],

            "maximum_los_intrusion_m":
                blocked_result[
                    "maximum_los_intrusion_m"
                ],

            "maximum_fresnel_intrusion_m":
                blocked_result[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                blocked_result[
                    "worst_obstruction"
                ],
        }
    )


if __name__ == "__main__":
    main()