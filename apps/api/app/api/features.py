from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.engine import calculate_features
from app.features.historical import calculate_historical_features
from app.features.historical_health import (
    calculate_historical_health,
)
from app.models import Device, Telemetry
from app.schemas.features import FeatureResult
from app.schemas.historical_features import HistoricalFeatureResult


router = APIRouter(
    prefix="/api/v1/features",
    tags=["Features"],
)


@router.get(
    "/device/{device_external_id}",
    response_model=FeatureResult,
)
def get_device_features(
    device_external_id: str,
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

    features = calculate_features(
        telemetry
    )

    return {
        "device_id": device.device_id,
        **features,
    }


@router.get(
    "/device/{device_external_id}/history",
    response_model=HistoricalFeatureResult,
)
def get_device_historical_features(
    device_external_id: str,
    limit: int = Query(
        default=10,
        ge=2,
        le=100,
    ),
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

    records = db.scalars(
        select(Telemetry)
        .where(
            Telemetry.device_id == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(limit)
    ).all()

    if len(records) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least two telemetry records "
                "are required for historical analysis"
            ),
        )

    # Database query returns newest -> oldest.
    # Historical trend calculations need oldest -> newest.
    records = list(reversed(records))

    historical = calculate_historical_features(
        records
    )

    historical_health = calculate_historical_health(
        historical
    )

    return {
        "device_id": device.device_id,
        "window_size": len(records),
        **historical,
        **historical_health,
    }