def score_rsrp(
    value: float,
) -> float:
    if value >= -80:
        return 100

    if value >= -90:
        return 85

    if value >= -100:
        return 65

    if value >= -110:
        return 40

    if value >= -120:
        return 20

    return 5


def score_sinr(
    value: float,
) -> float:
    if value >= 20:
        return 100

    if value >= 13:
        return 85

    if value >= 7:
        return 65

    if value >= 0:
        return 35

    return 10


def score_throughput(
    value: float,
) -> float:
    if value >= 50:
        return 100

    if value >= 30:
        return 85

    if value >= 15:
        return 60

    if value >= 5:
        return 35

    return 10


def score_latency(
    value: float,
) -> float:
    if value <= 30:
        return 100

    if value <= 50:
        return 85

    if value <= 80:
        return 65

    if value <= 150:
        return 35

    return 10


def score_packet_loss(
    value: float,
) -> float:
    if value <= 0.5:
        return 100

    if value <= 1:
        return 85

    if value <= 2:
        return 65

    if value <= 5:
        return 35

    return 10


def health_label(
    score: float,
) -> str:
    if score >= 80:
        return "GOOD"

    if score >= 60:
        return "FAIR"

    if score >= 40:
        return "POOR"

    return "CRITICAL"


def calculate_historical_health(
    historical: dict,
) -> dict:
    rsrp_score = score_rsrp(
        historical[
            "rsrp"
        ][
            "average"
        ]
    )

    sinr_score = score_sinr(
        historical[
            "sinr"
        ][
            "average"
        ]
    )

    throughput_score = (
        score_throughput(
            historical[
                "throughput"
            ][
                "average"
            ]
        )
    )

    latency_score = (
        score_latency(
            historical[
                "latency"
            ][
                "average"
            ]
        )
    )

    packet_loss_score = (
        score_packet_loss(
            historical[
                "packet_loss"
            ][
                "average"
            ]
        )
    )

    radio_health_score = (
        rsrp_score * 0.45
        + sinr_score * 0.55
    )

    network_health_score = (
        throughput_score * 0.40
        + latency_score * 0.35
        + packet_loss_score * 0.25
    )

    historical_health_score = (
        radio_health_score * 0.45
        + network_health_score * 0.55
    )

    historical_health_score = round(
        historical_health_score,
        2,
    )

    historical_health = health_label(
        historical_health_score
    )

    return {
        "historical_health_score":
            historical_health_score,

        "historical_health":
            historical_health,

        "persistent_poor_state":
            historical_health_score < 40,
    }