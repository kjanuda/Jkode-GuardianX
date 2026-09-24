from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class AlertRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    device_id: int

    fingerprint: str
    status: str

    severity: str
    risk_score: float

    primary_cause: str

    title: str
    summary: str

    occurrence_count: int

    first_seen_at: datetime
    last_seen_at: datetime

    resolved_at: datetime | None


class AlertEvaluationResult(BaseModel):
    action: str

    risk_score: float
    risk_level: str

    resolved_count: int = 0

    alert: AlertRead | None = None