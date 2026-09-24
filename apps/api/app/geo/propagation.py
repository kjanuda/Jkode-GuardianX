from math import sqrt


from app.geo.fresnel_v2 import (
    analyze_elevation_profile_v2,
)


SPEED_OF_LIGHT = 299_792_458.0


def calculate_fresnel_radius(
    frequency_mhz: float,
    distance_1_m: float,
    distance_2_m: float,
) -> float:
    if (
        distance_1_m <= 0
        or distance_2_m <= 0
    ):
        return 0.0

    frequency_hz = (
        frequency_mhz
        * 1_000_000
    )

    wavelength = (
        SPEED_OF_LIGHT
        / frequency_hz
    )

    total_distance = (
        distance_1_m
        + distance_2_m
    )

    radius = sqrt(
        (
            wavelength
            * distance_1_m
            * distance_2_m
        )
        / total_distance
    )

    return radius


def calculate_obstruction_score(
    terrain_obstructed: bool,
    fresnel_obstructed: bool,
    minimum_terrain_clearance_m: float,
    minimum_fresnel_clearance_m: float,
) -> float:
    """
    Existing MVP obstruction score.

    This remains unchanged and is kept for
    backward compatibility.

    Later this can be calibrated against
    real RF measurements.
    """

    if terrain_obstructed:
        penetration = abs(
            min(
                minimum_terrain_clearance_m,
                0,
            )
        )

        score = (
            70
            + min(
                penetration * 3,
                30,
            )
        )

        return round(
            min(score, 100),
            2,
        )

    if fresnel_obstructed:
        penetration = abs(
            min(
                minimum_fresnel_clearance_m,
                0,
            )
        )

        score = (
            40
            + min(
                penetration * 3,
                30,
            )
        )

        return round(
            min(score, 70),
            2,
        )

    return 10.0


def classify_propagation_risk(
    terrain_obstructed: bool,
    fresnel_obstructed: bool,
) -> str:
    if terrain_obstructed:
        return "HIGH"

    if fresnel_obstructed:
        return "MODERATE"

    return "LOW"


def analyze_propagation(
    profile: list[dict],
    distance_m: float,
    frequency_mhz: float,
    tower_antenna_height_m: float,
    device_antenna_height_m: float,
) -> dict:
    """
    Analyze a propagation path using the
    existing Guardian X propagation engine.

    The existing MVP calculations are preserved.

    Fresnel v2 is additionally attached under:

        result["fresnel_v2"]
    """

    if len(profile) < 2:
        raise ValueError(
            "Elevation profile must contain "
            "at least two points"
        )

    if distance_m <= 0:
        raise ValueError(
            "distance_m must be > 0"
        )

    if frequency_mhz <= 0:
        raise ValueError(
            "frequency_mhz must be > 0"
        )

    if tower_antenna_height_m < 0:
        raise ValueError(
            "tower_antenna_height_m "
            "must be >= 0"
        )

    if device_antenna_height_m < 0:
        raise ValueError(
            "device_antenna_height_m "
            "must be >= 0"
        )

    tower_ground_elevation = (
        float(
            profile[0]["elevation_m"]
        )
    )

    device_ground_elevation = (
        float(
            profile[-1]["elevation_m"]
        )
    )

    tower_radio_height = (
        tower_ground_elevation
        + tower_antenna_height_m
    )

    device_radio_height = (
        device_ground_elevation
        + device_antenna_height_m
    )

    profile_result = []

    terrain_obstructed_points = 0
    fresnel_obstructed_points = 0

    terrain_clearances = []
    fresnel_clearances = []

    total_intervals = (
        len(profile) - 1
    )

    for index, point in enumerate(
        profile
    ):
        fraction = (
            index
            / total_intervals
        )

        distance_1_m = (
            distance_m
            * fraction
        )

        distance_2_m = (
            distance_m
            - distance_1_m
        )

        los_height = (
            tower_radio_height
            + (
                device_radio_height
                - tower_radio_height
            )
            * fraction
        )

        terrain_elevation = float(
            point["elevation_m"]
        )

        terrain_clearance = (
            los_height
            - terrain_elevation
        )

        fresnel_radius = (
            calculate_fresnel_radius(
                frequency_mhz=(
                    frequency_mhz
                ),
                distance_1_m=(
                    distance_1_m
                ),
                distance_2_m=(
                    distance_2_m
                ),
            )
        )

        required_fresnel_clearance = (
            fresnel_radius
            * 0.60
        )

        fresnel_60_clearance = (
            terrain_clearance
            - required_fresnel_clearance
        )

        # Do not count the actual antenna
        # endpoint locations as terrain
        # obstructions.
        interior_point = (
            index != 0
            and index
            != len(profile) - 1
        )

        obstructed = (
            interior_point
            and terrain_clearance < 0
        )

        fresnel_obstructed = (
            interior_point
            and fresnel_60_clearance < 0
        )

        if obstructed:
            terrain_obstructed_points += 1

        if fresnel_obstructed:
            fresnel_obstructed_points += 1

        if interior_point:
            terrain_clearances.append(
                terrain_clearance
            )

            fresnel_clearances.append(
                fresnel_60_clearance
            )

        profile_result.append(
            {
                "latitude": point.get(
                    "latitude"
                ),

                "longitude": point.get(
                    "longitude"
                ),

                "terrain_elevation_m":
                    round(
                        terrain_elevation,
                        2,
                    ),

                "los_height_m":
                    round(
                        los_height,
                        2,
                    ),

                "terrain_clearance_m":
                    round(
                        terrain_clearance,
                        2,
                    ),

                "fresnel_radius_m":
                    round(
                        fresnel_radius,
                        2,
                    ),

                "fresnel_60_clearance_m":
                    round(
                        fresnel_60_clearance,
                        2,
                    ),

                "obstructed":
                    obstructed,

                "fresnel_obstructed":
                    fresnel_obstructed,
            }
        )

    if terrain_clearances:
        minimum_terrain_clearance = (
            min(terrain_clearances)
        )
    else:
        minimum_terrain_clearance = 0.0

    if fresnel_clearances:
        minimum_fresnel_clearance = (
            min(fresnel_clearances)
        )
    else:
        minimum_fresnel_clearance = 0.0

    terrain_obstructed = (
        terrain_obstructed_points > 0
    )

    fresnel_obstructed = (
        fresnel_obstructed_points > 0
    )

    if terrain_obstructed:
        los_status = "BLOCKED"

    elif fresnel_obstructed:
        los_status = (
            "LOS_CLEAR_FRESNEL_OBSTRUCTED"
        )

    else:
        los_status = "CLEAR"

    obstruction_score = (
        calculate_obstruction_score(
            terrain_obstructed=(
                terrain_obstructed
            ),
            fresnel_obstructed=(
                fresnel_obstructed
            ),
            minimum_terrain_clearance_m=(
                minimum_terrain_clearance
            ),
            minimum_fresnel_clearance_m=(
                minimum_fresnel_clearance
            ),
        )
    )

    propagation_risk = (
        classify_propagation_risk(
            terrain_obstructed=(
                terrain_obstructed
            ),
            fresnel_obstructed=(
                fresnel_obstructed
            ),
        )
    )

    # -------------------------------------------------
    # Fresnel v2
    # -------------------------------------------------
    #
    # The existing propagation engine remains
    # unchanged. Fresnel v2 provides a more
    # detailed DEM-aware analysis including:
    #
    # - Earth curvature
    # - effective Earth radius
    # - Fresnel radius
    # - required Fresnel clearance
    # - actual clearance
    # - LOS intrusion
    # - Fresnel intrusion
    # - worst obstruction location
    # - obstruction percentages
    #
    fresnel_v2 = (
        analyze_elevation_profile_v2(
            profile=profile,
            path_distance_m=distance_m,
            frequency_mhz=frequency_mhz,
            tx_height_m=(
                tower_antenna_height_m
            ),
            rx_height_m=(
                device_antenna_height_m
            ),
            clearance_fraction=0.60,
        )
    )

    return {
        # ---------------------------------------------
        # Existing propagation engine output
        # ---------------------------------------------

        "tower_ground_elevation_m":
            round(
                tower_ground_elevation,
                2,
            ),

        "tower_antenna_height_m":
            tower_antenna_height_m,

        "tower_radio_height_m":
            round(
                tower_radio_height,
                2,
            ),

        "device_ground_elevation_m":
            round(
                device_ground_elevation,
                2,
            ),

        "device_antenna_height_m":
            device_antenna_height_m,

        "device_radio_height_m":
            round(
                device_radio_height,
                2,
            ),

        "los_status":
            los_status,

        "terrain_obstructed":
            terrain_obstructed,

        "fresnel_60_obstructed":
            fresnel_obstructed,

        "obstructed_points":
            terrain_obstructed_points,

        "fresnel_obstructed_points":
            fresnel_obstructed_points,

        "minimum_terrain_clearance_m":
            round(
                minimum_terrain_clearance,
                2,
            ),

        "minimum_fresnel_60_clearance_m":
            round(
                minimum_fresnel_clearance,
                2,
            ),

        "obstruction_score":
            obstruction_score,

        "propagation_risk":
            propagation_risk,

        "sample_count":
            len(profile),

        "profile":
            profile_result,

        # ---------------------------------------------
        # Fresnel v2 output
        # ---------------------------------------------

        "fresnel_v2":
            fresnel_v2,
    }