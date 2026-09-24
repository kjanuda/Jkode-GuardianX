
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.geo.calculations import (
    calculate_spatial_metrics,
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

from app.risk.environmental_risk import (
    calculate_environmental_vulnerability,
)

from app.schemas.environment import (
    EnvironmentalVulnerabilityResult,
    EnvironmentContextResult,
    WorldCoverContextResult,
)


router = APIRouter(
    prefix="/api/v1/environment",
    tags=["Environment"],
)


# =====================================================
# OSM ENVIRONMENT CONTEXT
# =====================================================

@router.get(
    "/device/{device_external_id}",
    response_model=EnvironmentContextResult,
)
def get_device_environment_context(
    device_external_id: str,

    radius_m: int = Query(
        default=500,
        ge=100,
        le=2000,
    ),

    db: Session = Depends(get_db),
):
    # -------------------------------------------------
    # Find device
    # -------------------------------------------------

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

    # -------------------------------------------------
    # Get latest telemetry
    # -------------------------------------------------

    telemetry = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(1)
    )

    if telemetry is None:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found",
        )

    # -------------------------------------------------
    # Validate location
    # -------------------------------------------------

    if (
        telemetry.latitude is None
        or telemetry.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Latest telemetry "
                "has no location"
            ),
        )

    # -------------------------------------------------
    # Query OpenStreetMap / Overpass
    # -------------------------------------------------

    try:
        context = (
            fetch_osm_environment_context(
                latitude=(
                    telemetry.latitude
                ),
                longitude=(
                    telemetry.longitude
                ),
                radius_m=radius_m,
            )
        )

    except OSMContextError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # -------------------------------------------------
    # Response
    # -------------------------------------------------

    return {
        "device_id": (
            device.device_id
        ),

        "latitude": (
            telemetry.latitude
        ),

        "longitude": (
            telemetry.longitude
        ),

        **context,
    }


# =====================================================
# ESA WORLDCOVER LAND-COVER CONTEXT
# =====================================================

@router.get(
    "/device/{device_external_id}/land-cover",
    response_model=WorldCoverContextResult,
)
def get_device_land_cover(
    device_external_id: str,

    radius_m: int = Query(
        default=500,
        ge=100,
        le=2000,
    ),

    db: Session = Depends(get_db),
):
    # -------------------------------------------------
    # Find device
    # -------------------------------------------------

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

    # -------------------------------------------------
    # Get latest telemetry
    # -------------------------------------------------

    telemetry = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(1)
    )

    if telemetry is None:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found",
        )

    # -------------------------------------------------
    # Validate location
    # -------------------------------------------------

    if (
        telemetry.latitude is None
        or telemetry.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Latest telemetry "
                "has no location"
            ),
        )

    # -------------------------------------------------
    # Query ESA WorldCover
    # -------------------------------------------------

    try:
        context = (
            get_worldcover_context(
                latitude=(
                    telemetry.latitude
                ),
                longitude=(
                    telemetry.longitude
                ),
                radius_m=radius_m,
            )
        )

    except WorldCoverError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # -------------------------------------------------
    # Response
    # -------------------------------------------------

    return {
        "device_id": (
            device.device_id
        ),

        "latitude": (
            telemetry.latitude
        ),

        "longitude": (
            telemetry.longitude
        ),

        "radius_m": radius_m,

        **context,
    }


# =====================================================
# COMBINED ENVIRONMENTAL VULNERABILITY
# =====================================================

@router.get(
    "/device/{device_external_id}/vulnerability",
    response_model=EnvironmentalVulnerabilityResult,
)
def get_environmental_vulnerability(
    device_external_id: str,

    radius_m: int = Query(
        default=500,
        ge=100,
        le=2000,
    ),

    db: Session = Depends(get_db),
):
    # -------------------------------------------------
    # Find device
    # -------------------------------------------------

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

    # -------------------------------------------------
    # Get latest telemetry
    # -------------------------------------------------

    telemetry = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(1)
    )

    if telemetry is None:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found",
        )

    # -------------------------------------------------
    # Validate location
    # -------------------------------------------------

    if (
        telemetry.latitude is None
        or telemetry.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Latest telemetry "
                "has no location"
            ),
        )

    # -------------------------------------------------
    # Resolve serving cell
    # -------------------------------------------------

    cell_db_id = (
        telemetry.cell_id
        or device.current_cell_id
    )

    if cell_db_id is None:
        raise HTTPException(
            status_code=400,
            detail="No serving cell available",
        )

    # -------------------------------------------------
    # Resolve cell
    # -------------------------------------------------

    cell = db.get(
        Cell,
        cell_db_id,
    )

    if cell is None:
        raise HTTPException(
            status_code=404,
            detail="Cell not found",
        )

    # -------------------------------------------------
    # Resolve sector
    # -------------------------------------------------

    sector = db.get(
        Sector,
        cell.sector_id,
    )

    if sector is None:
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    # -------------------------------------------------
    # Resolve tower
    # -------------------------------------------------

    tower = db.get(
        Tower,
        sector.tower_id,
    )

    if tower is None:
        raise HTTPException(
            status_code=404,
            detail="Tower not found",
        )

    # =================================================
    # OSM ENVIRONMENT
    # =================================================

    try:
        osm_context = (
            fetch_osm_environment_context(
                latitude=(
                    telemetry.latitude
                ),
                longitude=(
                    telemetry.longitude
                ),
                radius_m=radius_m,
            )
        )

    except OSMContextError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # =================================================
    # ESA WORLDCOVER
    # =================================================

    try:
        worldcover = (
            get_worldcover_context(
                latitude=(
                    telemetry.latitude
                ),
                longitude=(
                    telemetry.longitude
                ),
                radius_m=radius_m,
            )
        )

    except WorldCoverError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    # =================================================
    # SPATIAL DISTANCE
    # =================================================

    spatial = calculate_spatial_metrics(
        db=db,

        device_latitude=(
            telemetry.latitude
        ),

        device_longitude=(
            telemetry.longitude
        ),

        tower_latitude=(
            tower.latitude
        ),

        tower_longitude=(
            tower.longitude
        ),
    )

    # =================================================
    # ELEVATION / DEM
    # =================================================

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
                    telemetry.latitude
                ),

                device_longitude=(
                    telemetry.longitude
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

    # =================================================
    # RADIO PROPAGATION
    # =================================================

    propagation = analyze_propagation(
        profile=(
            elevation["profile"]
        ),

        distance_m=(
            spatial["distance_m"]
        ),

        frequency_mhz=2350,

        tower_antenna_height_m=30,

        device_antenna_height_m=1.5,
    )

    # =================================================
    # ENVIRONMENTAL VULNERABILITY ENGINE
    # =================================================

    vulnerability = (
        calculate_environmental_vulnerability(
            osm_context=osm_context,
            worldcover=worldcover,
            propagation=propagation,
        )
    )

    # =================================================
    # FINAL RESPONSE
    # =================================================

    return {
        "device_id": (
            device.device_id
        ),

        "radius_m": radius_m,

        **vulnerability,

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

        "shrubland_pct": (
            worldcover[
                "shrubland_pct"
            ]
        ),

        "cropland_pct": (
            worldcover[
                "cropland_pct"
            ]
        ),

        "building_density_per_km2": (
            osm_context[
                "building_density_per_km2"
            ]
        ),

        "vegetation_context_level": (
            osm_context[
                "vegetation_context_level"
            ]
        ),

        "los_status": (
            propagation[
                "los_status"
            ]
        ),

        "propagation_risk": (
            propagation[
                "propagation_risk"
            ]
        ),
    }

