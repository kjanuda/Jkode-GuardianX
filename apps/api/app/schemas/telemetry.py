from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RadioTelemetry(BaseModel):
    rsrp: float | None = Field(
        default=None,
        ge=-160,
        le=-20,
    )

    rsrq: float | None = Field(
        default=None,
        ge=-40,
        le=0,
    )

    rssi: float | None = Field(
        default=None,
        ge=-160,
        le=0,
    )

    sinr: float | None = Field(
        default=None,
        ge=-30,
        le=60,
    )

    cqi: int | None = Field(
        default=None,
        ge=0,
        le=15,
    )

    mcs: int | None = Field(
        default=None,
        ge=0,
        le=31,
    )


class NetworkTelemetry(BaseModel):
    download_mbps: float | None = Field(
        default=None,
        ge=0,
    )

    upload_mbps: float | None = Field(
        default=None,
        ge=0,
    )

    latency_ms: float | None = Field(
        default=None,
        ge=0,
    )

    jitter_ms: float | None = Field(
        default=None,
        ge=0,
    )

    packet_loss: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class GeoTelemetry(BaseModel):
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class TelemetryCreate(BaseModel):
    device_id: str
    cell_id: str | None = None
    scenario: str | None = None

    timestamp: datetime | None = None

    radio: RadioTelemetry
    network: NetworkTelemetry
    geo: GeoTelemetry


class TelemetryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    device_id: int
    cell_id: int | None
    scenario: str | None

    timestamp: datetime

    rsrp: float | None
    rsrq: float | None
    rssi: float | None
    sinr: float | None
    cqi: int | None
    mcs: int | None

    download_mbps: float | None
    upload_mbps: float | None
    latency_ms: float | None
    jitter_ms: float | None
    packet_loss: float | None

    latitude: float | None
    longitude: float | None