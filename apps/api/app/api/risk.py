from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.features.engine import calculate_features
from app.features.historical import (
    calculate_historical_features,
)
from app.features.historical_health import (
    calculate_historical_health,
)

from app.geo.calculations import (
    calculate_azimuth_difference,
    calculate_spatial_metrics,
    classify_sector_alignment,
)

from app.geo.elevation import (
    ElevationServiceError,
    build_elevation_context,
)

from app.geo.osm_context import (
    OSMContextError,
    fetch_osm_environment_context,
)

from app.geo.propagation import (
    analyze_propagation,
)

from app.geo.worldcover import (
    WorldCoverError,
    get_worldcover_context,
)

from app.models import (
    Cell,
    Device,
    Sector,
    Telemetry,
    Tower,
)

from app.risk.engine import calculate_risk

from app.risk.environmental_risk import (
    calculate_environmental_vulnerability,
)

from app.risk.geo_risk import (
    calculate_geo_risk,
)

from app.schemas.risk import RiskResult

from app.services.weather import (
    WeatherServiceError,
    fetch_current_weather,
)


router = APIRouter(
    prefix="/api/v1/risk",
    tags=["Risk"],
)


@router.get(
    "/device/{device_external_id}",
    response_model=RiskResult,
)
def get_device_risk(
    device_external_id: str,
    history_limit: int = Query(
        default=10,
        ge=2,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    # ===================================================
    # FIND DEVICE
    # ===================================================

    device = db.scalar(
        select(Device).where(
            Device.device_id
            == device_external_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    # ===================================================
    # LOAD TELEMETRY HISTORY
    # ===================================================

    records = db.scalars(
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(history_limit)
    ).all()

    if len(records) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least two telemetry records "
                "are required for risk analysis"
            ),
        )

    latest = records[0]

    # ===================================================
    # VALIDATE LATEST TELEMETRY LOCATION
    # ===================================================

    if (
        latest.latitude is None
        or latest.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Latest telemetry has no location"
            ),
        )

    # ===================================================
    # RESOLVE SERVING CELL
    # ===================================================

    cell_db_id = (
        latest.cell_id
        or device.current_cell_id
    )

    if cell_db_id is None:
        raise HTTPException(
            status_code=400,
            detail="No serving cell available",
        )

    cell = db.get(
        Cell,
        cell_db_id,
    )

    if cell is None:
        raise HTTPException(
            status_code=404,
            detail="Cell not found",
        )

    # ===================================================
    # RESOLVE SECTOR
    # ===================================================

    sector = db.get(
        Sector,
        cell.sector_id,
    )

    if sector is None:
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    # ===================================================
    # RESOLVE TOWER
    # ===================================================

    tower = db.get(
        Tower,
        sector.tower_id,
    )

    if tower is None:
        raise HTTPException(
            status_code=404,
            detail="Tower not found",
        )

    # ===================================================
    # CURRENT RADIO / NETWORK FEATURES
    # ===================================================

    current_features = calculate_features(
        latest
    )

    # ===================================================
    # HISTORICAL FEATURES
    # ===================================================

    # Database query returns newest -> oldest.
    # Historical calculations need oldest -> newest.
    historical_records = list(
        reversed(records)
    )

    historical = calculate_historical_features(
        historical_records
    )

    # ===================================================
    # HISTORICAL HEALTH
    # ===================================================

    historical.update(
        calculate_historical_health(
            historical
        )
    )

    # ===================================================
    # GEO ANALYSIS
    # ===================================================

    spatial = calculate_spatial_metrics(
        db=db,
        device_latitude=latest.latitude,
        device_longitude=latest.longitude,
        tower_latitude=tower.latitude,
        tower_longitude=tower.longitude,
    )

    # ===================================================
    # SECTOR ALIGNMENT
    # ===================================================

    azimuth_difference = (
        calculate_azimuth_difference(
            bearing_deg=(
                spatial["bearing_deg"]
            ),
            sector_azimuth_deg=(
                sector.azimuth_deg
            ),
        )
    )

    sector_alignment = (
        classify_sector_alignment(
            azimuth_difference
        )
    )

    # ===================================================
    # DEM / ELEVATION PROFILE
    # ===================================================

    try:
        elevation = (
            build_elevation_context(
                tower_latitude=(
                    tower.latitude
                ),
                tower_longitude=(
                    tower.longitude
                ),
                device_latitude=(
                    latest.latitude
                ),
                device_longitude=(
                    latest.longitude
                ),
                distance_m=(
                    spatial["distance_m"]
                ),
                sample_count=31,
            )
        )

    except ElevationServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # ===================================================
    # RADIO PROPAGATION ANALYSIS
    # ===================================================

    propagation = analyze_propagation(
        profile=elevation["profile"],
        distance_m=spatial["distance_m"],
        frequency_mhz=2350,
        tower_antenna_height_m=30,
        device_antenna_height_m=1.5,
    )

    # ===================================================
    # GEO VULNERABILITY
    # ===================================================

    geo_vulnerability = calculate_geo_risk(
        obstruction_score=(
            propagation[
                "obstruction_score"
            ]
        ),
        distance_km=(
            spatial["distance_km"]
        ),
        sector_alignment=(
            sector_alignment
        ),
    )

    # ===================================================
    # ENVIRONMENTAL CONTEXT
    # ===================================================
    #
    # Environmental intelligence is a supporting layer.
    #
    # If Overpass or WorldCover temporarily fails,
    # the core Guardian X risk calculation continues.
    #

    environment_context = {
        "available": False,

        "environmental_vulnerability": 0.0,
        "environmental_vulnerability_level": (
            "UNAVAILABLE"
        ),

        "clutter_vulnerability": 0.0,

        "environment_type": (
            "UNAVAILABLE"
        ),

        "built_up_pct": 0.0,
        "tree_cover_pct": 0.0,

        "building_density_per_km2": 0.0,
    }

    try:
        # ------------------------------------------------
        # OpenStreetMap environment context
        # ------------------------------------------------

        osm_context = (
            fetch_osm_environment_context(
                latitude=latest.latitude,
                longitude=latest.longitude,
                radius_m=500,
            )
        )

        # ------------------------------------------------
        # ESA WorldCover context
        # ------------------------------------------------

        worldcover = (
            get_worldcover_context(
                latitude=latest.latitude,
                longitude=latest.longitude,
                radius_m=500,
            )
        )

        # ------------------------------------------------
        # Environmental vulnerability
        # ------------------------------------------------

        environmental = (
            calculate_environmental_vulnerability(
                osm_context=osm_context,
                worldcover=worldcover,
                propagation=propagation,
            )
        )

        # ------------------------------------------------
        # Build unified environment context
        # ------------------------------------------------

        environment_context = {
            "available": True,

            "environmental_vulnerability": (
                environmental[
                    "environmental_vulnerability_score"
                ]
            ),

            "environmental_vulnerability_level": (
                environmental[
                    "environmental_vulnerability_level"
                ]
            ),

            "clutter_vulnerability": (
                environmental[
                    "components"
                ][
                    "clutter_vulnerability"
                ]
            ),

            "environment_type": (
                environmental[
                    "environment_type"
                ]
            ),

            "built_up_pct": (
                worldcover[
                    "built_up_pct"
                ]
            ),

            "tree_cover_pct": (
                worldcover[
                    "tree_cover_pct"
                ]
            ),

            "building_density_per_km2": (
                osm_context[
                    "building_density_per_km2"
                ]
            ),
        }

    except (
        OSMContextError,
        WorldCoverError,
    ):
        # ------------------------------------------------
        # Graceful degradation
        # ------------------------------------------------
        #
        # Environment is supporting intelligence.
        # A temporary external-data failure must not
        # break the core Guardian X risk API.
        #

        pass

    # ===================================================
    # WEATHER CONTEXT
    # ===================================================
    #
    # Weather is supporting intelligence.
    #
    # If the external weather service fails,
    # the core Guardian X risk calculation continues.
    #

    weather_context = {
        "available": False,

        "weather_context_score": 0.0,
        "weather_context_level": (
            "UNAVAILABLE"
        ),

        "precipitation_mm": 0.0,
        "relative_humidity_pct": 0.0,

        "wind_speed_kmh": 0.0,
        "wind_gusts_kmh": 0.0,

        "factors": [],
    }

    try:
        # ------------------------------------------------
        # Current weather context
        # ------------------------------------------------

        weather = fetch_current_weather(
            latitude=latest.latitude,
            longitude=latest.longitude,
        )

        # ------------------------------------------------
        # Build unified weather context
        # ------------------------------------------------

        weather_context = {
            "available": True,

            "weather_context_score": (
                weather[
                    "weather_context_score"
                ]
            ),

            "weather_context_level": (
                weather[
                    "weather_context_level"
                ]
            ),

            "precipitation_mm": (
                weather[
                    "precipitation_mm"
                ]
            ),

            "relative_humidity_pct": (
                weather[
                    "relative_humidity_pct"
                ]
            ),

            "wind_speed_kmh": (
                weather[
                    "wind_speed_kmh"
                ]
            ),

            "wind_gusts_kmh": (
                weather[
                    "wind_gusts_kmh"
                ]
            ),

            "factors": (
                weather[
                    "factors"
                ]
            ),
        }

    except WeatherServiceError:
        # ------------------------------------------------
        # Graceful degradation
        # ------------------------------------------------
        #
        # Weather is supporting context.
        # A temporary external API failure must not
        # break the core Guardian X risk API.
        #

        pass

    # ===================================================
    # UNIFIED GEO CONTEXT
    # ===================================================

    geo_context = {
        "geo_vulnerability": (
            geo_vulnerability
        ),

        "distance_km": (
            spatial["distance_km"]
        ),

        "sector_alignment": (
            sector_alignment
        ),

        "terrain_obstructed": (
            propagation[
                "terrain_obstructed"
            ]
        ),

        "fresnel_60_obstructed": (
            propagation[
                "fresnel_60_obstructed"
            ]
        ),

        "obstruction_score": (
            propagation[
                "obstruction_score"
            ]
        ),

        "propagation_risk": (
            propagation[
                "propagation_risk"
            ]
        ),

        "los_status": (
            propagation[
                "los_status"
            ]
        ),
    }

    # ===================================================
    # FINAL RISK ENGINE
    # ===================================================

    result = calculate_risk(
        telemetry=latest,
        current_features=current_features,
        historical=historical,
        geo_context=geo_context,
        environment_context=environment_context,
        weather_context=weather_context,
    )

    # ===================================================
    # API RESPONSE
    # ===================================================
    #
    # fresnel_v2 comes from the existing propagation
    # analysis (same elevation profile, no extra DEM call).
    #

    return {
        "device_id": (
            device.device_id
        ),
        **result,
        "fresnel_v2": (
            propagation.get(
                "fresnel_v2"
            )
        ),
    }