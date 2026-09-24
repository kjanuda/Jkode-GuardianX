from datetime import datetime

from pydantic import BaseModel


class DashboardAlertItem(BaseModel):
    id: int

    device_id: str

    status: str
    severity: str

    risk_score: float
    primary_cause: str

    title: str

    occurrence_count: int

    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None


class DashboardSummary(BaseModel):
    total_devices: int

    active_alerts: int

    critical_alerts: int
    high_alerts: int

    devices_with_active_alerts: int

    latest_incidents: list[
        DashboardAlertItem
    ]


class DashboardDeviceOverview(BaseModel):
    device_id: str

    latest_telemetry_id: int
    latest_timestamp: datetime

    scenario: str | None

    risk_score: float
    risk_level: str

    current_radio_health: str
    current_network_health: str

    historical_health_score: float
    historical_health: str
    historical_trend: str

    persistent_poor_state: bool

    geo_vulnerability_score: float
    geo_vulnerability_level: str

    environmental_vulnerability_score: float
    environmental_vulnerability_level: str

    weather_context_score: float
    weather_context_level: str

    primary_cause: str

    alert_required: bool

    active_alert_count: int