def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(value, maximum))


def score_rsrp(rsrp: float | None) -> float:
    if rsrp is None:
        return 50

    if rsrp >= -80:
        return 100

    if rsrp >= -90:
        return 85

    if rsrp >= -100:
        return 65

    if rsrp >= -110:
        return 40

    if rsrp >= -120:
        return 20

    return 5


def score_rsrq(rsrq: float | None) -> float:
    if rsrq is None:
        return 50

    if rsrq >= -8:
        return 100

    if rsrq >= -10:
        return 85

    if rsrq >= -13:
        return 65

    if rsrq >= -16:
        return 40

    if rsrq >= -20:
        return 20

    return 5


def score_sinr(sinr: float | None) -> float:
    if sinr is None:
        return 50

    if sinr >= 20:
        return 100

    if sinr >= 13:
        return 85

    if sinr >= 7:
        return 65

    if sinr >= 0:
        return 35

    return 10


def score_throughput(download_mbps: float | None) -> float:
    if download_mbps is None:
        return 50

    if download_mbps >= 50:
        return 100

    if download_mbps >= 30:
        return 85

    if download_mbps >= 15:
        return 60

    if download_mbps >= 5:
        return 35

    return 10


def score_latency(latency_ms: float | None) -> float:
    if latency_ms is None:
        return 50

    if latency_ms <= 30:
        return 100

    if latency_ms <= 50:
        return 85

    if latency_ms <= 80:
        return 65

    if latency_ms <= 150:
        return 35

    return 10


def score_packet_loss(packet_loss: float | None) -> float:
    if packet_loss is None:
        return 50

    if packet_loss <= 0.5:
        return 100

    if packet_loss <= 1:
        return 85

    if packet_loss <= 2:
        return 65

    if packet_loss <= 5:
        return 35

    return 10


def health_label(score: float) -> str:
    if score >= 80:
        return "GOOD"

    if score >= 60:
        return "FAIR"

    if score >= 40:
        return "POOR"

    return "CRITICAL"