
from sqlalchemy import text
from sqlalchemy.orm import Session


def calculate_spatial_metrics(
    db: Session,
    device_latitude: float,
    device_longitude: float,
    tower_latitude: float,
    tower_longitude: float,
) -> dict:
    """
    Calculate the spatial relationship between a device
    and its serving tower.

    Returns:
        distance_m
        distance_km
        bearing_deg
    """

    query = text(
        """
        SELECT
            ST_Distance(
                ST_SetSRID(
                    ST_MakePoint(
                        :tower_longitude,
                        :tower_latitude
                    ),
                    4326
                )::geography,

                ST_SetSRID(
                    ST_MakePoint(
                        :device_longitude,
                        :device_latitude
                    ),
                    4326
                )::geography
            ) AS distance_m,

            degrees(
                ST_Azimuth(
                    ST_SetSRID(
                        ST_MakePoint(
                            :tower_longitude,
                            :tower_latitude
                        ),
                        4326
                    )::geography,

                    ST_SetSRID(
                        ST_MakePoint(
                            :device_longitude,
                            :device_latitude
                        ),
                        4326
                    )::geography
                )
            ) AS bearing_deg
        """
    )

    result = db.execute(
        query,
        {
            "device_latitude": device_latitude,
            "device_longitude": device_longitude,
            "tower_latitude": tower_latitude,
            "tower_longitude": tower_longitude,
        },
    ).mappings().one()

    distance_m = float(
        result["distance_m"]
    )

    bearing = result["bearing_deg"]

    if bearing is not None:
        bearing = float(bearing)

    return {
        "distance_m": round(
            distance_m,
            2,
        ),
        "distance_km": round(
            distance_m / 1000,
            3,
        ),
        "bearing_deg": (
            round(
                bearing,
                2,
            )
            if bearing is not None
            else None
        ),
    }


def calculate_azimuth_difference(
    bearing_deg: float | None,
    sector_azimuth_deg: float | None,
) -> float | None:
    """
    Calculate the smallest angular difference between
    the device bearing and the sector azimuth.

    Both angles are expected in degrees.

    Example:

        bearing = 350°
        sector azimuth = 10°

        Difference = 20°

    The result is always between 0° and 180°.
    """

    if (
        bearing_deg is None
        or sector_azimuth_deg is None
    ):
        return None

    bearing = float(bearing_deg) % 360
    azimuth = float(sector_azimuth_deg) % 360

    difference = abs(
        bearing - azimuth
    )

    if difference > 180:
        difference = 360 - difference

    return round(
        difference,
        2,
    )


def classify_sector_alignment(
    azimuth_difference_deg: float | None,
) -> str:
    """
    Classify how well the device direction aligns
    with the sector azimuth.

    The classification is based on angular difference.
    """

    if azimuth_difference_deg is None:
        return "unknown"

    difference = abs(
        float(azimuth_difference_deg)
    )

    if difference <= 30:
        return "strong"

    if difference <= 60:
        return "moderate"

    if difference <= 90:
        return "weak"

    return "misaligned"

