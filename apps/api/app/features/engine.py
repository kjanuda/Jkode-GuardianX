from app.features.scoring import (
    health_label,
    score_latency,
    score_packet_loss,
    score_rsrp,
    score_rsrq,
    score_sinr,
    score_throughput,
)


def calculate_features(telemetry):
    rsrp_score = score_rsrp(
        telemetry.rsrp
    )

    rsrq_score = score_rsrq(
        telemetry.rsrq
    )

    sinr_score = score_sinr(
        telemetry.sinr
    )

    throughput_score = score_throughput(
        telemetry.download_mbps
    )

    latency_score = score_latency(
        telemetry.latency_ms
    )

    packet_loss_score = score_packet_loss(
        telemetry.packet_loss
    )

    # Radio score
    radio_score = (
        rsrp_score * 0.30
        + rsrq_score * 0.25
        + sinr_score * 0.45
    )

    # Network score
    network_score = (
        throughput_score * 0.40
        + latency_score * 0.35
        + packet_loss_score * 0.25
    )

    return {
        "radio_score": round(
            radio_score,
            2,
        ),

        "network_score": round(
            network_score,
            2,
        ),

        "rsrp_score": rsrp_score,
        "rsrq_score": rsrq_score,
        "sinr_score": sinr_score,

        "throughput_score": throughput_score,
        "latency_score": latency_score,
        "packet_loss_score": packet_loss_score,

        "radio_health": health_label(
            radio_score
        ),

        "network_health": health_label(
            network_score
        ),
    }