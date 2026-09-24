def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def score_osm_building_density(
    density_per_km2: float,
) -> float:
    if density_per_km2 < 25:
        return 10

    if density_per_km2 < 75:
        return 25

    if density_per_km2 < 200:
        return 50

    if density_per_km2 < 500:
        return 75

    return 90


def score_satellite_built_up(
    built_up_pct: float,
) -> float:
    if built_up_pct < 5:
        return 10

    if built_up_pct < 15:
        return 30

    if built_up_pct < 30:
        return 55

    if built_up_pct < 50:
        return 75

    return 90


def score_vegetation(
    tree_cover_pct: float,
    shrubland_pct: float,
    vegetation_context_level: str,
) -> float:
    # Tree cover is treated as the
    # strongest vegetation-clutter indicator.

    satellite_score = clamp(
        tree_cover_pct * 1.25
        + shrubland_pct * 0.50
    )

    if vegetation_context_level == "HIGH":
        osm_score = 70

    elif vegetation_context_level == "MODERATE":
        osm_score = 40

    else:
        osm_score = 10

    score = (
        satellite_score * 0.85
        + osm_score * 0.15
    )

    return round(
        clamp(score),
        2,
    )


def classify_environment(
    built_up_pct: float,
    tree_cover_pct: float,
    shrubland_pct: float,
    cropland_pct: float,
) -> str:
    vegetation_pct = (
        tree_cover_pct
        + shrubland_pct
    )

    if (
        built_up_pct >= 25
        and vegetation_pct >= 30
    ):
        return "MIXED_URBAN_GREEN"

    if built_up_pct >= 25:
        return "URBAN_BUILT_UP"

    if vegetation_pct >= 50:
        return "VEGETATION_HEAVY"

    if cropland_pct >= 50:
        return "AGRICULTURAL"

    return "OPEN_OR_MIXED"


def get_vulnerability_level(
    score: float,
) -> str:
    if score < 30:
        return "LOW"

    if score < 60:
        return "MODERATE"

    return "HIGH"


def build_environment_evidence(
    osm_context: dict,
    worldcover: dict,
    propagation: dict,
) -> list[str]:
    evidence = []

    built_up_pct = worldcover[
        "built_up_pct"
    ]

    tree_cover_pct = worldcover[
        "tree_cover_pct"
    ]

    if built_up_pct >= 25:
        evidence.append(
            f"Satellite land cover shows "
            f"{built_up_pct:.2f}% built-up area"
        )

    if tree_cover_pct >= 30:
        evidence.append(
            f"Satellite land cover shows "
            f"{tree_cover_pct:.2f}% tree cover"
        )

    if (
        osm_context[
            "building_density_per_km2"
        ]
        >= 200
    ):
        evidence.append(
            "OpenStreetMap indicates high "
            "nearby building density"
        )

    if propagation[
        "terrain_obstructed"
    ]:
        evidence.append(
            "Terrain intersects the direct "
            "tower-to-device radio path"
        )

    elif propagation[
        "fresnel_60_obstructed"
    ]:
        evidence.append(
            "The 60% Fresnel zone has "
            "terrain obstruction"
        )

    if not evidence:
        evidence.append(
            "No strong environmental "
            "clutter indicator detected"
        )

    return evidence


def calculate_environmental_vulnerability(
    osm_context: dict,
    worldcover: dict,
    propagation: dict,
) -> dict:
    osm_building_risk = (
        score_osm_building_density(
            osm_context[
                "building_density_per_km2"
            ]
        )
    )

    satellite_built_up_risk = (
        score_satellite_built_up(
            worldcover[
                "built_up_pct"
            ]
        )
    )

    # Satellite coverage receives more weight
    # because OSM mapping completeness varies.
    building_vulnerability = (
        osm_building_risk * 0.35
        + satellite_built_up_risk * 0.65
    )

    vegetation_vulnerability = (
        score_vegetation(
            tree_cover_pct=(
                worldcover[
                    "tree_cover_pct"
                ]
            ),
            shrubland_pct=(
                worldcover[
                    "shrubland_pct"
                ]
            ),
            vegetation_context_level=(
                osm_context[
                    "vegetation_context_level"
                ]
            ),
        )
    )

    # Buildings OR vegetation can create
    # meaningful clutter. Avoid averaging
    # away one strong factor.
    dominant_clutter = max(
        building_vulnerability,
        vegetation_vulnerability,
    )

    secondary_clutter = min(
        building_vulnerability,
        vegetation_vulnerability,
    )

    clutter_vulnerability = (
        dominant_clutter * 0.70
        + secondary_clutter * 0.30
    )

    terrain_vulnerability = (
        propagation[
            "obstruction_score"
        ]
    )

    # Terrain remains the dominant physics
    # signal, with land-cover/clutter providing
    # additional structural context.
    environmental_score = (
        terrain_vulnerability * 0.60
        + clutter_vulnerability * 0.40
    )

    environmental_score = round(
        clamp(
            environmental_score
        ),
        2,
    )

    environment_type = (
        classify_environment(
            built_up_pct=(
                worldcover[
                    "built_up_pct"
                ]
            ),
            tree_cover_pct=(
                worldcover[
                    "tree_cover_pct"
                ]
            ),
            shrubland_pct=(
                worldcover[
                    "shrubland_pct"
                ]
            ),
            cropland_pct=(
                worldcover[
                    "cropland_pct"
                ]
            ),
        )
    )

    return {
        "environment_type":
            environment_type,

        "environmental_vulnerability_score":
            environmental_score,

        "environmental_vulnerability_level":
            get_vulnerability_level(
                environmental_score
            ),

        "components": {
            "osm_building_risk":
                round(
                    osm_building_risk,
                    2,
                ),

            "satellite_built_up_risk":
                round(
                    satellite_built_up_risk,
                    2,
                ),

            "building_vulnerability":
                round(
                    building_vulnerability,
                    2,
                ),

            "vegetation_vulnerability":
                round(
                    vegetation_vulnerability,
                    2,
                ),

            "clutter_vulnerability":
                round(
                    clutter_vulnerability,
                    2,
                ),

            "terrain_vulnerability":
                round(
                    terrain_vulnerability,
                    2,
                ),
        },

        "evidence":
            build_environment_evidence(
                osm_context,
                worldcover,
                propagation,
            ),
    }