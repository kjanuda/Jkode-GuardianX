
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.geo.calculations import (
    calculate_azimuth_difference,
    calculate_spatial_metrics,
    classify_sector_alignment,
)

from app.geo.elevation import (
    ElevationServiceError,
    build_elevation_context,
)

from app.models import (
    Cell,
    Device,
    Sector,
    Telemetry,
    Tower,
)

from app.schemas.geo import (
    ElevationContextResult,
    GeoContextResult,
)


router = APIRouter(
    prefix="/api/v1/geo",
    tags=["Geo"],
)


# ============================================================
# GEO CONTEXT
# ============================================================

@router.get(
    "/device/{device_external_id}",
    response_model=GeoContextResult,
)
def get_device_geo_context(
    device_external_id: str,
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Find device
    # ---------------------------------------------------------
    device = db.scalar(
        select(Device).where(
            Device.device_id == device_external_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    # ---------------------------------------------------------
    # 2. Get latest telemetry
    # ---------------------------------------------------------
    telemetry = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id == device.id
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

    # ---------------------------------------------------------
    # 3. Validate telemetry location
    # ---------------------------------------------------------
    if (
        telemetry.latitude is None
        or telemetry.longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Latest telemetry has no location",
        )

    # ---------------------------------------------------------
    # 4. Resolve serving cell
    # ---------------------------------------------------------
    cell_db_id = (
        telemetry.cell_id
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

    # ---------------------------------------------------------
    # 5. Resolve sector
    # ---------------------------------------------------------
    sector = db.get(
        Sector,
        cell.sector_id,
    )

    if sector is None:
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    # ---------------------------------------------------------
    # 6. Resolve tower
    # ---------------------------------------------------------
    tower = db.get(
        Tower,
        sector.tower_id,
    )

    if tower is None:
        raise HTTPException(
            status_code=404,
            detail="Tower not found",
        )

    # ---------------------------------------------------------
    # 7. Calculate spatial metrics
    # ---------------------------------------------------------
    spatial = calculate_spatial_metrics(
        db=db,
        device_latitude=telemetry.latitude,
        device_longitude=telemetry.longitude,
        tower_latitude=tower.latitude,
        tower_longitude=tower.longitude,
    )

    # ---------------------------------------------------------
    # 8. Calculate azimuth difference
    # ---------------------------------------------------------
    azimuth_difference = (
        calculate_azimuth_difference(
            bearing_deg=spatial["bearing_deg"],
            sector_azimuth_deg=sector.azimuth_deg,
        )
    )

    # ---------------------------------------------------------
    # 9. Classify sector alignment
    # ---------------------------------------------------------
    alignment = classify_sector_alignment(
        azimuth_difference
    )

    # ---------------------------------------------------------
    # 10. Return Geo context
    # ---------------------------------------------------------
    return {
        "device_id": device.device_id,
        "telemetry_id": telemetry.id,

        "cell_id": cell.cell_id,
        "sector_code": sector.sector_code,
        "tower_code": tower.tower_code,

        "device_latitude": telemetry.latitude,
        "device_longitude": telemetry.longitude,

        "tower_latitude": tower.latitude,
        "tower_longitude": tower.longitude,

        "distance_m": spatial["distance_m"],
        "distance_km": spatial["distance_km"],

        "bearing_deg": spatial["bearing_deg"],
        "sector_azimuth_deg": sector.azimuth_deg,

        "azimuth_difference_deg": azimuth_difference,
        "sector_alignment": alignment,
    }


# ============================================================
# ELEVATION CONTEXT
# ============================================================

@router.get(
    "/device/{device_external_id}/elevation",
    response_model=ElevationContextResult,
)
def get_device_elevation_context(
    device_external_id: str,
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. Find device
    # ---------------------------------------------------------
    device = db.scalar(
        select(Device).where(
            Device.device_id == device_external_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    # ---------------------------------------------------------
    # 2. Get latest telemetry
    # ---------------------------------------------------------
    telemetry = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id == device.id
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

    # ---------------------------------------------------------
    # 3. Validate telemetry location
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # 4. Resolve serving cell
    # ---------------------------------------------------------
    cell_db_id = (
        telemetry.cell_id
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

    # ---------------------------------------------------------
    # 5. Resolve sector
    # ---------------------------------------------------------
    sector = db.get(
        Sector,
        cell.sector_id,
    )

    if sector is None:
        raise HTTPException(
            status_code=404,
            detail="Sector not found",
        )

    # ---------------------------------------------------------
    # 6. Resolve tower
    # ---------------------------------------------------------
    tower = db.get(
        Tower,
        sector.tower_id,
    )

    if tower is None:
        raise HTTPException(
            status_code=404,
            detail="Tower not found",
        )

    # ---------------------------------------------------------
    # 7. Calculate spatial metrics
    # ---------------------------------------------------------
    spatial = calculate_spatial_metrics(
        db=db,
        device_latitude=telemetry.latitude,
        device_longitude=telemetry.longitude,
        tower_latitude=tower.latitude,
        tower_longitude=tower.longitude,
    )

    # ---------------------------------------------------------
    # 8. Build elevation context
    # ---------------------------------------------------------
    try:
        elevation = build_elevation_context(
            tower_latitude=tower.latitude,
            tower_longitude=tower.longitude,
            device_latitude=telemetry.latitude,
            device_longitude=telemetry.longitude,
            distance_m=spatial["distance_m"],
            sample_count=11,
        )

    except ElevationServiceError as exc:
        return JSONResponse(
            status_code=502,
            content={
                "detail": str(exc),
            },
        )

    # ---------------------------------------------------------
    # 9. Return elevation context
    # ---------------------------------------------------------
    return {
        "device_id": device.device_id,
        "tower_code": tower.tower_code,
        "distance_km": spatial["distance_km"],
        **elevation,
    }

