from statistics import mean, pstdev


def clean_values(values):
    return [
        float(value)
        for value in values
        if value is not None
    ]


def calculate_metric(
    values,
    degrade_threshold,
    improve_threshold,
    higher_is_better=True,
):
    values = clean_values(values)

    if not values:
        return {
            "average": None,
            "delta": None,
            "volatility": None,
            "trend": "UNKNOWN",
        }

    metric_average = mean(values)

    if len(values) == 1:
        return {
            "average": round(metric_average, 2),
            "delta": 0,
            "volatility": 0,
            "trend": "STABLE",
        }

    oldest = values[0]
    latest = values[-1]

    delta = latest - oldest

    volatility = pstdev(values)

    if higher_is_better:
        if delta <= -degrade_threshold:
            trend = "DEGRADING"

        elif delta >= improve_threshold:
            trend = "IMPROVING"

        else:
            trend = "STABLE"

    else:
        # Used for metrics such as latency and packet loss,
        # where increasing values mean poorer performance.

        if delta >= degrade_threshold:
            trend = "DEGRADING"

        elif delta <= -improve_threshold:
            trend = "IMPROVING"

        else:
            trend = "STABLE"

    return {
        "average": round(metric_average, 2),
        "delta": round(delta, 2),
        "volatility": round(volatility, 2),
        "trend": trend,
    }


def calculate_historical_features(records):
    if not records:
        return None

    rsrp = calculate_metric(
        [record.rsrp for record in records],
        degrade_threshold=5,
        improve_threshold=5,
        higher_is_better=True,
    )

    sinr = calculate_metric(
        [record.sinr for record in records],
        degrade_threshold=3,
        improve_threshold=3,
        higher_is_better=True,
    )

    throughput = calculate_metric(
        [record.download_mbps for record in records],
        degrade_threshold=10,
        improve_threshold=10,
        higher_is_better=True,
    )

    latency = calculate_metric(
        [record.latency_ms for record in records],
        degrade_threshold=20,
        improve_threshold=20,
        higher_is_better=False,
    )

    packet_loss = calculate_metric(
        [record.packet_loss for record in records],
        degrade_threshold=1,
        improve_threshold=1,
        higher_is_better=False,
    )

    metrics = {
        "rsrp": rsrp,
        "sinr": sinr,
        "throughput": throughput,
        "latency": latency,
        "packet_loss": packet_loss,
    }

    degrading_metrics = [
        name
        for name, result in metrics.items()
        if result["trend"] == "DEGRADING"
    ]

    improving_metrics = [
        name
        for name, result in metrics.items()
        if result["trend"] == "IMPROVING"
    ]

    if len(degrading_metrics) >= 3:
        overall_trend = "DEGRADING"

    elif len(improving_metrics) >= 3:
        overall_trend = "IMPROVING"

    else:
        overall_trend = "STABLE"

    return {
        **metrics,
        "overall_trend": overall_trend,
        "degrading_metrics": degrading_metrics,
        "improving_metrics": improving_metrics,
    }