from pydantic import BaseModel


class RiskComponents(BaseModel):
    radio_risk: float
    network_risk: float
    historical_risk: float

    geo_vulnerability: float
    clutter_vulnerability: float

    weather_context: float

    geo_influence: float
    clutter_influence: float
    weather_influence: float

    structural_influence: float
    contextual_influence: float


class RiskResult(BaseModel):
    device_id: str

    risk_score: float
    risk_level: str

    geo_vulnerability_score: float
    geo_vulnerability_level: str

    environmental_vulnerability_score: float
    environmental_vulnerability_level: str

    clutter_vulnerability_score: float
    environment_type: str

    environment_context_available: bool

    weather_context_available: bool
    weather_context_score: float
    weather_context_level: str
    weather_factors: list[str]

    components: RiskComponents

    current_radio_health: str
    current_network_health: str
    historical_trend: str

    historical_health_score: float
    historical_health: str
    persistent_poor_state: bool

    propagation_risk: str
    los_status: str

    likely_causes: list[str]
    reasons: list[str]

    alert_required: bool