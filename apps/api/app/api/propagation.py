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

from app.geo.propagation import (
    analyze_propagation,
)

from app.models import (
    Cell,
    Device,
    Sector,
    Telemetry,
    Tower,
)

from app.schemas.propagation import (
    PropagationResult,
)


router = APIRouter(
    prefix="/api/v1/propagation",
    tags=["Propagation"],
)


@router.get(
    "/device/{device_external_id}",
    response_model=PropagationResult,
)
def get_device_propagation(
    device_external_id: str,

    frequency_mhz: float = Query(
        default=2350,
        gt=100,
        le=100000,
    ),

    tower_antenna_height_m: float = Query(
        default=30,
        ge=1,
        le=200,
    ),

    device_antenna_height_m: float = Query(
        default=1.5,
        ge=0.1,
        le=50,
    ),

    sample_count: int = Query(
        default=31,
        ge=5,
        le=100,
    ),

    db: Session = Depends(get_db),
):
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

    if (
        telemetry.latitude is None
        or telemetry.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Latest telemetry has "
                "no location"
            ),
        )

    cell_db_id = (
        telemetry.cell_id
        or device.current_cell_id
    )

    if cell_db_id is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "No serving cell available"
            ),
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

    sector = db.get(
        Sector,
        cell.sector_id,
    )

    if sector is None:
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    tower = db.get(
        Tower,
        sector.tower_id,
    )

    if tower is None:
        raise HTTPException(
            status_code=404,
            detail="Tower not found",
        )

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
                sample_count=(
                    sample_count
                ),
            )
        )

    except ElevationServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    propagation = analyze_propagation(
        profile=elevation["profile"],

        distance_m=(
            spatial["distance_m"]
        ),

        frequency_mhz=(
            frequency_mhz
        ),

        tower_antenna_height_m=(
            tower_antenna_height_m
        ),

        device_antenna_height_m=(
            device_antenna_height_m
        ),
    )

    return {
        "device_id":
            device.device_id,

        "cell_id":
            cell.cell_id,

        "tower_code":
            tower.tower_code,

        "frequency_mhz":
            frequency_mhz,

        "distance_km":
            spatial["distance_km"],

        **propagation,
    }