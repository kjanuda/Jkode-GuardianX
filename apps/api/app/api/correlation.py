from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

import traceback

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.correlation.population import (
    analyze_cell_population,
)

from app.db.session import get_db

from app.models import (
    Cell,
    Device,
    DeviceProfile,
)

from app.schemas.correlation import (
    DeviceProfileInput,
    DeviceProfileResult,
    PopulationCorrelationResult,
)


router = APIRouter(
    prefix="/api/v1/correlation",
    tags=["Correlation"],
)


@router.put(
    "/device/{device_external_id}/profile",
    response_model=DeviceProfileResult,
)
def upsert_device_profile(
    device_external_id: str,
    payload: DeviceProfileInput,
    db: Session = Depends(get_db),
):
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

    profile = db.scalar(
        select(DeviceProfile).where(
            DeviceProfile.device_id == device.id
        )
    )

    values = payload.model_dump()

    if profile is None:
        profile = DeviceProfile(
            device_id=device.id,
            **values,
        )

        db.add(profile)

    else:
        for key, value in values.items():
            setattr(
                profile,
                key,
                value,
            )

    db.commit()

    db.refresh(profile)

    return {
        "device_id": device.device_id,
        "manufacturer": profile.manufacturer,
        "model_name": profile.model_name,
        "os_name": profile.os_name,
        "os_version": profile.os_version,
        "firmware_version": profile.firmware_version,
        "modem_version": profile.modem_version,
    }


@router.get(
    "/cell/{cell_external_id}",
    response_model=PopulationCorrelationResult,
)
def get_cell_population_correlation(
    cell_external_id: str,
    window_minutes: int = Query(
        default=10,
        ge=1,
        le=120,
    ),
    db: Session = Depends(get_db),
):
    cell = db.scalar(
        select(Cell).where(
            Cell.cell_id == cell_external_id
        )
    )

    if cell is None:
        raise HTTPException(
            status_code=404,
            detail="Cell not found",
        )

    try:
        return analyze_cell_population(
            db=db,
            cell_id=cell.id,
            cell_external_id=cell.cell_id,
            window_minutes=window_minutes,
        )

    except Exception as exc:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=(
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
        )