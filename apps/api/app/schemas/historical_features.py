from pydantic import BaseModel


class MetricTrend(BaseModel):
    average: float | None
    delta: float | None
    volatility: float | None
    trend: str


class HistoricalFeatureResult(BaseModel):
    device_id: str
    window_size: int

    rsrp: MetricTrend
    sinr: MetricTrend
    throughput: MetricTrend
    latency: MetricTrend
    packet_loss: MetricTrend

    overall_trend: str
    degrading_metrics: list[str]
    improving_metrics: list[str]

    historical_health_score: float
    historical_health: str

    persistent_poor_state: bool