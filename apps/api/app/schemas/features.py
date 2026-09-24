from pydantic import BaseModel


class FeatureResult(BaseModel):
    device_id: str

    radio_score: float
    network_score: float

    rsrp_score: float
    rsrq_score: float
    sinr_score: float

    throughput_score: float
    latency_score: float
    packet_loss_score: float

    radio_health: str
    network_health: str