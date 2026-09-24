from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Cell, Device, Telemetry
from app.schemas.telemetry import (
    TelemetryCreate,
    TelemetryRead,
)


router = APIRouter(
    prefix="/api/v1/telemetry",
    tags=["Telemetry"],
)


@router.post(
    "",
    response_model=TelemetryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_telemetry(
    payload: TelemetryCreate,
    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.device_id == payload.device_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    cell_db_id = device.current_cell_id

    if payload.cell_id:
        cell = db.scalar(
            select(Cell).where(
                Cell.cell_id == payload.cell_id
            )
        )

        if cell is None:
            raise HTTPException(
                status_code=404,
                detail="Cell not found",
            )

        cell_db_id = cell.id

        # Update device's current serving cell
        device.current_cell_id = cell.id

    record = Telemetry(
        device_id=device.id,
        cell_id=cell_db_id,
        scenario=payload.scenario,
        timestamp=payload.timestamp or datetime.now(timezone.utc),

        rsrp=payload.radio.rsrp,
        rsrq=payload.radio.rsrq,
        rssi=payload.radio.rssi,
        sinr=payload.radio.sinr,
        cqi=payload.radio.cqi,
        mcs=payload.radio.mcs,

        download_mbps=payload.network.download_mbps,
        upload_mbps=payload.network.upload_mbps,
        latency_ms=payload.network.latency_ms,
        jitter_ms=payload.network.jitter_ms,
        packet_loss=payload.network.packet_loss,

        latitude=payload.geo.latitude,
        longitude=payload.geo.longitude,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get(
    "/device/{device_external_id}",
    response_model=list[TelemetryRead],
)
def get_device_telemetry(
    device_external_id: str,
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
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

    query = (
        select(Telemetry)
        .where(
            Telemetry.device_id == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(limit)
    )

    return db.scalars(query).all()


@router.get(
    "/device/{device_external_id}/latest",
    response_model=TelemetryRead,
)
def get_latest_device_telemetry(
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

    record = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id == device.id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(1)
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found",
        )

    return record