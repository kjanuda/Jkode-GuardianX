def distance_risk_score(
    distance_km: float,
) -> float:
    if distance_km <= 1.5:
        return 10

    if distance_km <= 3:
        return 25

    if distance_km <= 5:
        return 45

    if distance_km <= 8:
        return 65

    return 80


def alignment_risk_score(
    alignment: str,
) -> float:
    if alignment == "ALIGNED":
        return 10

    if alignment == "PARTIAL":
        return 40

    if alignment == "OUTSIDE_MAIN_DIRECTION":
        return 70

    return 30


def calculate_geo_risk(
    obstruction_score: float,
    distance_km: float,
    sector_alignment: str,
) -> float:
    distance_risk = (
        distance_risk_score(
            distance_km
        )
    )

    alignment_risk = (
        alignment_risk_score(
            sector_alignment
        )
    )

    geo_risk = (
        obstruction_score * 0.70
        + distance_risk * 0.20
        + alignment_risk * 0.10
    )

    return round(
        min(max(geo_risk, 0), 100),
        2,
    )