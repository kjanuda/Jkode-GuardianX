from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Telemetry

from app.correlation.population import (
    is_affected,
    select_latest_per_device,
)


def ratio(
    count: int,
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    return count / total


def mean(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return sum(values) / len(values)


def is_radio_healthy(
    row: Telemetry,
) -> bool:
    rsrp_ok = (
        row.rsrp is None
        or row.rsrp >= -100
    )

    rsrq_ok = (
        row.rsrq is None
        or row.rsrq > -13
    )

    sinr_ok = (
        row.sinr is None
        or row.sinr >= 13
    )

    return (
        rsrp_ok
        and rsrq_ok
        and sinr_ok
    )


def has_network_degradation(
    row: Telemetry,
) -> bool:
    if (
        row.download_mbps is not None
        and row.download_mbps < 15
    ):
        return True

    if (
        row.latency_ms is not None
        and row.latency_ms > 80
    ):
        return True

    if (
        row.packet_loss is not None
        and row.packet_loss > 2
    ):
        return True

    return False


def has_coverage_signature(
    row: Telemetry,
) -> bool:
    weak_rsrp = (
        row.rsrp is not None
        and row.rsrp < -105
    )

    low_sinr = (
        row.sinr is not None
        and row.sinr < 7
    )

    return (
        weak_rsrp
        and low_sinr
    )


def has_interference_signature(
    row: Telemetry,
) -> bool:
    usable_rsrp = (
        row.rsrp is not None
        and row.rsrp >= -100
    )

    bad_quality = (
        (
            row.rsrq is not None
            and row.rsrq <= -13
        )
        or
        (
            row.sinr is not None
            and row.sinr < 7
        )
    )

    return (
        usable_rsrp
        and bad_quality
    )


def has_outage_signature(
    row: Telemetry,
) -> bool:
    severe_throughput = (
        row.download_mbps is not None
        and row.download_mbps < 1
    )

    severe_loss = (
        row.packet_loss is not None
        and row.packet_loss >= 50
    )

    return (
        severe_throughput
        and severe_loss
    )


def analyze_cell_cross_layers(
    *,
    db: Session,
    cell_id: int,
    window_start: datetime,
    window_end: datetime,
    population: dict,
) -> dict:
    rows = list(
        db.scalars(
            select(Telemetry)
            .where(
                Telemetry.cell_id
                == cell_id,

                Telemetry.timestamp
                >= window_start,

                Telemetry.timestamp
                <= window_end,
            )
            .order_by(
                Telemetry.timestamp.desc(),
                Telemetry.id.desc(),
            )
        ).all()
    )

    latest_rows = (
        select_latest_per_device(
            rows
        )
    )

    affected_rows = [
        row
        for row in latest_rows
        if is_affected(row)
    ]

    affected_total = len(
        affected_rows
    )

    if affected_total == 0:
        return {
            "affected_devices": 0,

            "radio_healthy_ratio": 0.0,
            "network_bad_ratio": 0.0,

            "coverage_signature_ratio": 0.0,
            "interference_signature_ratio": 0.0,
            "congestion_signature_ratio": 0.0,
            "outage_signature_ratio": 0.0,

            "mean_rsrp": None,
            "mean_rsrq": None,
            "mean_sinr": None,

            "mean_download_mbps": None,
            "mean_latency_ms": None,
            "mean_packet_loss": None,
        }

    radio_healthy_count = sum(
        1
        for row in affected_rows
        if is_radio_healthy(row)
    )

    network_bad_count = sum(
        1
        for row in affected_rows
        if has_network_degradation(row)
    )

    coverage_count = sum(
        1
        for row in affected_rows
        if has_coverage_signature(row)
    )

    interference_count = sum(
        1
        for row in affected_rows
        if has_interference_signature(row)
    )

    outage_count = sum(
        1
        for row in affected_rows
        if has_outage_signature(row)
    )

    # Congestion/backhaul is mutually exclusive
    # with the severe outage signature.
    #
    # Healthy radio + degraded network
    #     + outage signature -> OUTAGE
    #     + no outage        -> CONGESTION
    congestion_count = sum(
        1
        for row in affected_rows
        if (
            is_radio_healthy(row)
            and has_network_degradation(row)
            and not has_outage_signature(row)
        )
    )

    rsrp_values = [
        float(row.rsrp)
        for row in affected_rows
        if row.rsrp is not None
    ]

    rsrq_values = [
        float(row.rsrq)
        for row in affected_rows
        if row.rsrq is not None
    ]

    sinr_values = [
        float(row.sinr)
        for row in affected_rows
        if row.sinr is not None
    ]

    download_values = [
        float(row.download_mbps)
        for row in affected_rows
        if row.download_mbps is not None
    ]

    latency_values = [
        float(row.latency_ms)
        for row in affected_rows
        if row.latency_ms is not None
    ]

    loss_values = [
        float(row.packet_loss)
        for row in affected_rows
        if row.packet_loss is not None
    ]

    return {
        "affected_devices":
            affected_total,

        "radio_healthy_ratio":
            round(
                ratio(
                    radio_healthy_count,
                    affected_total,
                ),
                4,
            ),

        "network_bad_ratio":
            round(
                ratio(
                    network_bad_count,
                    affected_total,
                ),
                4,
            ),

        "coverage_signature_ratio":
            round(
                ratio(
                    coverage_count,
                    affected_total,
                ),
                4,
            ),

        "interference_signature_ratio":
            round(
                ratio(
                    interference_count,
                    affected_total,
                ),
                4,
            ),

        "congestion_signature_ratio":
            round(
                ratio(
                    congestion_count,
                    affected_total,
                ),
                4,
            ),

        "outage_signature_ratio":
            round(
                ratio(
                    outage_count,
                    affected_total,
                ),
                4,
            ),

        "mean_rsrp":
            (
                round(
                    mean(rsrp_values),
                    2,
                )
                if rsrp_values
                else None
            ),

        "mean_rsrq":
            (
                round(
                    mean(rsrq_values),
                    2,
                )
                if rsrq_values
                else None
            ),

        "mean_sinr":
            (
                round(
                    mean(sinr_values),
                    2,
                )
                if sinr_values
                else None
            ),

        "mean_download_mbps":
            (
                round(
                    mean(download_values),
                    2,
                )
                if download_values
                else None
            ),

        "mean_latency_ms":
            (
                round(
                    mean(latency_values),
                    2,
                )
                if latency_values
                else None
            ),

        "mean_packet_loss":
            (
                round(
                    mean(loss_values),
                    2,
                )
                if loss_values
                else None
            ),
    }