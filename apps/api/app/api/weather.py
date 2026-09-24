from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.models import (
    Device,
    Telemetry,
)

from app.schemas.weather import (
    WeatherContextResult,
)

from app.services.weather import (
    WeatherServiceError,
    fetch_current_weather,
)


router = APIRouter(
    prefix="/api/v1/weather",
    tags=["Weather"],
)


@router.get(
    "/device/{device_external_id}",
    response_model=WeatherContextResult,
)
def get_device_weather(
    device_external_id: str,
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
                "Latest telemetry "
                "has no location"
            ),
        )

    try:
        weather = fetch_current_weather(
            latitude=(
                telemetry.latitude
            ),
            longitude=(
                telemetry.longitude
            ),
        )

    except WeatherServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    return {
        "device_id":
            device.device_id,

        "latitude":
            telemetry.latitude,

        "longitude":
            telemetry.longitude,

        **weather,
    }