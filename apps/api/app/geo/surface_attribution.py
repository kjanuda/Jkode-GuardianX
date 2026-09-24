from __future__ import annotations

from typing import Any

from app.geo.surface_profile import (
    analyze_surface_profile,
    build_surface_profile,
)


def round_delta(
    surface_value: float,
    terrain_value: float,
) -> float:
    return round(
        float(surface_value)
        - float(terrain_value),
        2,
    )


def analyze_surface_attribution(
    *,
    terrain_profile: list[dict[str, Any]],
    surface_obstructions: list[
        dict[str, Any]
    ],
    path_distance_m: float,
    frequency_mhz: float,
    tx_height_m: float = 30.0,
    rx_height_m: float = 1.5,
    clearance_fraction: float = 0.60,
    k_factor: float = 4.0 / 3.0,
) -> dict:
    """
    Compare pure DEM terrain propagation
    against terrain + surface/clutter.

    Important:
    this does NOT automatically declare
    surface clutter as the root cause.

    It measures how much additional
    obstruction the surface layer adds.
    """

    terrain_surface = (
        build_surface_profile(
            terrain_profile=(
                terrain_profile
            ),
            surface_obstructions=[],
        )
    )

    terrain_result = (
        analyze_surface_profile(
            surface_profile=(
                terrain_surface
            ),
            path_distance_m=(
                path_distance_m
            ),
            frequency_mhz=(
                frequency_mhz
            ),
            tx_height_m=(
                tx_height_m
            ),
            rx_height_m=(
                rx_height_m
            ),
            clearance_fraction=(
                clearance_fraction
            ),
            k_factor=k_factor,
        )
    )

    combined_surface = (
        build_surface_profile(
            terrain_profile=(
                terrain_profile
            ),
            surface_obstructions=(
                surface_obstructions
            ),
        )
    )

    surface_result = (
        analyze_surface_profile(
            surface_profile=(
                combined_surface
            ),
            path_distance_m=(
                path_distance_m
            ),
            frequency_mhz=(
                frequency_mhz
            ),
            tx_height_m=(
                tx_height_m
            ),
            rx_height_m=(
                rx_height_m
            ),
            clearance_fraction=(
                clearance_fraction
            ),
            k_factor=k_factor,
        )
    )

    fresnel_delta = round_delta(
        surface_result[
            "fresnel_occupancy_pct"
        ],
        terrain_result[
            "fresnel_occupancy_pct"
        ],
    )

    los_delta = round_delta(
        surface_result[
            "los_blocked_pct"
        ],
        terrain_result[
            "los_blocked_pct"
        ],
    )

    intrusion_delta = round_delta(
        surface_result[
            "maximum_fresnel_intrusion_m"
        ],
        terrain_result[
            "maximum_fresnel_intrusion_m"
        ],
    )

    surface_points = [
        point
        for point
        in combined_surface
        if float(
            point[
                "surface_height_m"
            ]
        ) > 0
    ]

    building_points = [
        point
        for point
        in surface_points
        if point[
            "surface_type"
        ] == "BUILDING"
    ]

    vegetation_points = [
        point
        for point
        in surface_points
        if point[
            "surface_type"
        ]
        in {
            "TREE",
            "VEGETATION",
        }
    ]

    strong_surface_points = [
        point
        for point
        in surface_points
        if float(
            point[
                "surface_confidence"
            ]
        ) >= 0.60
    ]

    inferred_surface_points = [
        point
        for point
        in surface_points
        if float(
            point[
                "surface_confidence"
            ]
        ) < 0.60
    ]

    terrain_already_obstructed = (
        terrain_result[
            "status"
        ]
        != "CLEAR"
    )

    surface_increased_obstruction = (
        fresnel_delta > 0.01
        or los_delta > 0.01
        or intrusion_delta > 0.01
    )

    worst_surface = (
        surface_result.get(
            "worst_obstruction"
        )
    )

    worst_surface_confidence = 0.0
    worst_surface_type = "NONE"

    if worst_surface:
        worst_surface_confidence = float(
            worst_surface.get(
                "surface_confidence",
                0.0,
            )
            or 0.0
        )

        worst_surface_type = (
            worst_surface.get(
                "surface_type"
            )
            or "NONE"
        )

    # --------------------------------------
    # Guardian X causal safety gates
    # --------------------------------------
    #
    # Surface clutter may become a primary
    # physical candidate only when:
    #
    # 1. terrain alone did NOT already
    #    explain obstruction,
    # 2. surface changes the propagation
    #    condition,
    # 3. worst surface evidence is not
    #    low-confidence inferred data.
    #
    # Inferred WorldCover heights may still
    # act as contributing evidence.
    # --------------------------------------

    surface_primary_eligible = (
        not terrain_already_obstructed
        and surface_increased_obstruction
        and worst_surface_type
        != "NONE"
        and worst_surface_confidence
        >= 0.60
    )

    surface_contributor_eligible = (
        surface_increased_obstruction
        and len(
            surface_points
        ) > 0
    )

    if (
        terrain_already_obstructed
        and surface_increased_obstruction
    ):
        attribution = (
            "TERRAIN_PRIMARY_"
            "SURFACE_CONTRIBUTING"
        )

    elif (
        not terrain_already_obstructed
        and surface_primary_eligible
    ):
        attribution = (
            "SURFACE_OBSTRUCTION_"
            "PRIMARY_CANDIDATE"
        )

    elif surface_increased_obstruction:
        attribution = (
            "SURFACE_CONTRIBUTION_"
            "INFERRED_OR_LOW_CONFIDENCE"
        )

    else:
        attribution = (
            "NO_MEASURABLE_SURFACE_"
            "CONTRIBUTION"
        )

    return {
        "attribution":
            attribution,

        "terrain_only": {
            "status":
                terrain_result[
                    "status"
                ],

            "los_blocked_pct":
                terrain_result[
                    "los_blocked_pct"
                ],

            "fresnel_occupancy_pct":
                terrain_result[
                    "fresnel_occupancy_pct"
                ],

            "maximum_fresnel_intrusion_m":
                terrain_result[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                terrain_result.get(
                    "worst_obstruction"
                ),
        },

        "surface_aware": {
            "status":
                surface_result[
                    "status"
                ],

            "los_blocked_pct":
                surface_result[
                    "los_blocked_pct"
                ],

            "fresnel_occupancy_pct":
                surface_result[
                    "fresnel_occupancy_pct"
                ],

            "maximum_fresnel_intrusion_m":
                surface_result[
                    "maximum_fresnel_intrusion_m"
                ],

            "worst_obstruction":
                surface_result.get(
                    "worst_obstruction"
                ),
        },

        "delta": {
            "los_blocked_pct":
                los_delta,

            "fresnel_occupancy_pct":
                fresnel_delta,

            "maximum_fresnel_intrusion_m":
                intrusion_delta,
        },

        "provenance": {
            "surface_points":
                len(
                    surface_points
                ),

            "building_points":
                len(
                    building_points
                ),

            "vegetation_points":
                len(
                    vegetation_points
                ),

            "strong_surface_points":
                len(
                    strong_surface_points
                ),

            "inferred_surface_points":
                len(
                    inferred_surface_points
                ),
        },

        "gates": {
            "terrain_already_obstructed":
                terrain_already_obstructed,

            "surface_increased_obstruction":
                surface_increased_obstruction,

            "surface_primary_eligible":
                surface_primary_eligible,

            "surface_contributor_eligible":
                surface_contributor_eligible,
        },
    }