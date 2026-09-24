from datetime import datetime

from pydantic import BaseModel


class DeviceProfileInput(BaseModel):
    manufacturer: str | None = None
    model_name: str | None = None

    os_name: str | None = None
    os_version: str | None = None

    firmware_version: str | None = None
    modem_version: str | None = None


class DeviceProfileResult(
    DeviceProfileInput
):
    device_id: str


class CohortResult(BaseModel):
    cohort_type: str
    cohort_key: str

    total_devices: int
    affected_devices: int

    affected_ratio: float

    healthy_devices: int


class PopulationCorrelationResult(BaseModel):
    scope_type: str
    scope_ref: str

    window_minutes: int

    window_start: datetime
    window_end: datetime

    total_devices: int

    affected_devices: int
    healthy_devices: int

    affected_ratio: float

    population_status: str

    sample_quality: str

    model_cohorts: list[
        CohortResult
    ]

    device_model_pattern: str

    likely_scope: str

    evidence: list[str]