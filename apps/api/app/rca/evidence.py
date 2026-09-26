import re

from datetime import datetime

from app.models.telemetry import Telemetry


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def evidence(
    *,
    key: str,
    source: str,
    category: str,
    metric: str,
    value,
    unit: str | None = None,
    supports: list[str] | None = None,
    contradicts: list[str] | None = None,
    support_score: float = 0.0,
    reliability: float = 1.0,
    freshness: float = 1.0,
    specificity: float = 0.5,
    gate_passed: bool | None = None,
    observed_at: datetime | None = None,
    context: dict | None = None,
) -> dict:
    return {
        "evidence_key": key,
        "source": source,
        "category": category,
        "metric": metric,
        "value_json": {
            "value": value,
        },
        "unit": unit,
        "supports_causes": supports or [],
        "contradicts_causes": contradicts or [],
        "support_score": round(clamp01(support_score), 4),
        "reliability_score": round(clamp01(reliability), 4),
        "freshness_score": round(clamp01(freshness), 4),
        "specificity_score": round(clamp01(specificity), 4),
        "gate_passed": gate_passed,
        "observed_at": observed_at,
        "context_json": context or {},
    }


def build_telemetry_evidence(telemetry: Telemetry) -> list[dict]:
    items: list[dict] = []

    # ----------------------------------
    # RSRP
    # ----------------------------------

    rsrp_support = 0.1

    if telemetry.rsrp is not None:
        if telemetry.rsrp < -120:
            rsrp_support = 0.95
        elif telemetry.rsrp < -110:
            rsrp_support = 0.80
        elif telemetry.rsrp < -100:
            rsrp_support = 0.45

        items.append(
            evidence(
                key="RF_RSRP",
                source="TELEMETRY",
                category="RADIO",
                metric="rsrp",
                value=telemetry.rsrp,
                unit="dBm",
                supports=["COVERAGE_OR_PROPAGATION"],
                support_score=rsrp_support,
                reliability=0.95,
                freshness=1.0,
                specificity=0.75,
                observed_at=telemetry.timestamp,
            )
        )

    # ----------------------------------
    # RSRQ
    # ----------------------------------

    if telemetry.rsrq is not None:
        rsrq_support = 0.1

        if telemetry.rsrq <= -16:
            rsrq_support = 0.85
        elif telemetry.rsrq <= -13:
            rsrq_support = 0.60

        items.append(
            evidence(
                key="RF_RSRQ",
                source="TELEMETRY",
                category="RADIO",
                metric="rsrq",
                value=telemetry.rsrq,
                unit="dB",
                supports=["INTERFERENCE"],
                support_score=rsrq_support,
                reliability=0.95,
                freshness=1.0,
                specificity=0.65,
                observed_at=telemetry.timestamp,
            )
        )

    # ----------------------------------
    # SINR
    # ----------------------------------

    if telemetry.sinr is not None:
        sinr_support = 0.1

        if telemetry.sinr < 0:
            sinr_support = 0.95
        elif telemetry.sinr < 7:
            sinr_support = 0.75
        elif telemetry.sinr < 13:
            sinr_support = 0.40

        items.append(
            evidence(
                key="RF_SINR",
                source="TELEMETRY",
                category="RADIO",
                metric="sinr",
                value=telemetry.sinr,
                unit="dB",
                supports=[
                    "INTERFERENCE",
                    "COVERAGE_OR_PROPAGATION",
                ],
                support_score=sinr_support,
                reliability=0.95,
                freshness=1.0,
                specificity=0.55,
                observed_at=telemetry.timestamp,
            )
        )

    # ----------------------------------
    # Throughput
    # ----------------------------------

    if telemetry.download_mbps is not None:
        throughput_support = 0.1

        if telemetry.download_mbps < 5:
            throughput_support = 0.90
        elif telemetry.download_mbps < 15:
            throughput_support = 0.70
        elif telemetry.download_mbps < 30:
            throughput_support = 0.40

        items.append(
            evidence(
                key="NET_DL_THROUGHPUT",
                source="TELEMETRY",
                category="NETWORK",
                metric="download_mbps",
                value=telemetry.download_mbps,
                unit="Mbps",
                supports=[
                    "CONGESTION_OR_BACKHAUL",
                    "SERVICE_DEGRADATION",
                ],
                support_score=throughput_support,
                reliability=0.95,
                freshness=1.0,
                specificity=0.55,
                observed_at=telemetry.timestamp,
            )
        )

    # ----------------------------------
    # Latency
    # ----------------------------------

    if telemetry.latency_ms is not None:
        latency_support = 0.1

        if telemetry.latency_ms > 150:
            latency_support = 0.90
        elif telemetry.latency_ms > 80:
            latency_support = 0.65
        elif telemetry.latency_ms > 50:
            latency_support = 0.35

        items.append(
            evidence(
                key="NET_LATENCY",
                source="TELEMETRY",
                category="NETWORK",
                metric="latency_ms",
                value=telemetry.latency_ms,
                unit="ms",
                supports=[
                    "CONGESTION_OR_BACKHAUL",
                    "SERVICE_DEGRADATION",
                ],
                support_score=latency_support,
                reliability=0.95,
                freshness=1.0,
                specificity=0.50,
                observed_at=telemetry.timestamp,
            )
        )

    # ----------------------------------
    # Packet loss
    # ----------------------------------

    if telemetry.packet_loss is not None:
        loss_support = 0.1

        if telemetry.packet_loss > 5:
            loss_support = 0.90
        elif telemetry.packet_loss > 2:
            loss_support = 0.65
        elif telemetry.packet_loss > 1:
            loss_support = 0.35

        items.append(
            evidence(
                key="NET_PACKET_LOSS",
                source="TELEMETRY",
                category="NETWORK",
                metric="packet_loss",
                value=telemetry.packet_loss,
                unit="percent",
                supports=["SERVICE_DEGRADATION"],
                support_score=loss_support,
                reliability=0.95,
                freshness=1.0,
                specificity=0.45,
                observed_at=telemetry.timestamp,
            )
        )

    return items


# ==========================================================
# Context Evidence Builder
# ==========================================================


def build_context_evidence(
    risk: dict,
    observed_at: datetime | None,
) -> list[dict]:
    items: list[dict] = []

    # ----------------------------------
    # Historical health
    # ----------------------------------

    history_score = risk["historical_health_score"]

    items.append(
        evidence(
            key="HISTORICAL_HEALTH",
            source="HISTORICAL_ENGINE",
            category="HISTORY",
            metric="historical_health_score",
            value=history_score,
            supports=(
                ["PERSISTENT_DEGRADATION"] if history_score < 40 else []
            ),
            contradicts=(
                ["PERSISTENT_DEGRADATION"] if history_score >= 80 else []
            ),
            support_score=(0.90 if history_score < 40 else 0.10),
            reliability=0.90,
            freshness=0.90,
            specificity=0.60,
            observed_at=observed_at,
            context={
                "health": risk["historical_health"],
                "trend": risk["historical_trend"],
                "persistent_poor_state": risk["persistent_poor_state"],
            },
        )
    )

    # ----------------------------------
    # LOS / terrain
    # ----------------------------------

    los_blocked = risk["los_status"] == "BLOCKED"

    items.append(
        evidence(
            key="GEO_LOS_STATUS",
            source="PROPAGATION_ENGINE",
            category="GEO",
            metric="los_status",
            value=risk["los_status"],
            supports=(
                ["TERRAIN_PROPAGATION_LIKELY"] if los_blocked else []
            ),
            contradicts=(
                ["TERRAIN_PROPAGATION_LIKELY"] if not los_blocked else []
            ),
            support_score=(0.95 if los_blocked else 0.10),
            reliability=0.92,
            freshness=0.95,
            specificity=0.90,
            gate_passed=los_blocked,
            observed_at=observed_at,
            context={
                "propagation_risk": risk["propagation_risk"],
                "geo_vulnerability": risk["geo_vulnerability_score"],
            },
        )
    )

    # ----------------------------------
    # Environment
    # ----------------------------------

    environment_available = risk["environment_context_available"]

    environment_type = risk["environment_type"]

    vegetation_heavy = (
        environment_available and environment_type == "VEGETATION_HEAVY"
    )

    items.append(
        evidence(
            key="ENVIRONMENT_CONTEXT",
            source="WORLDCOVER_OSM",
            category="ENVIRONMENT",
            metric="environment_type",
            value=environment_type,
            supports=(
                ["VEGETATION_PROPAGATION_POSSIBLE"]
                if vegetation_heavy
                else []
            ),
            support_score=(0.80 if vegetation_heavy else 0.10),
            reliability=(0.85 if environment_available else 0.0),
            freshness=0.65,
            specificity=0.70,
            gate_passed=environment_available,
            observed_at=observed_at,
            context={
                "environmental_vulnerability": risk[
                    "environmental_vulnerability_score"
                ],
                "clutter_vulnerability": risk[
                    "clutter_vulnerability_score"
                ],
            },
        )
    )

    # ----------------------------------
    # Weather
    # ----------------------------------

    weather_available = risk["weather_context_available"]

    weather_score = risk["weather_context_score"]

    strong_weather = weather_available and weather_score >= 25

    items.append(
        evidence(
            key="WEATHER_CONTEXT",
            source="WEATHER_SERVICE",
            category="WEATHER",
            metric="weather_context_score",
            value=weather_score,
            supports=(
                ["WEATHER_STRESS_POSSIBLE"] if strong_weather else []
            ),
            contradicts=(
                ["WEATHER_STRESS_POSSIBLE"]
                if (weather_available and weather_score < 10)
                else []
            ),
            support_score=(
                min(weather_score / 100, 1.0) if weather_available else 0.0
            ),
            reliability=(0.85 if weather_available else 0.0),
            freshness=(1.0 if weather_available else 0.0),
            specificity=0.60,
            gate_passed=strong_weather,
            observed_at=observed_at,
            context={
                "level": risk["weather_context_level"],
                "factors": risk["weather_factors"],
            },
        )
    )

    # ----------------------------------
    # Final risk context
    # ----------------------------------

    items.append(
        evidence(
            key="SYSTEM_RISK",
            source="RISK_ENGINE",
            category="SYSTEM",
            metric="risk_score",
            value=risk["risk_score"],
            supports=(
                ["SERVICE_DEGRADATION"] if risk["alert_required"] else []
            ),
            contradicts=(
                ["SERVICE_DEGRADATION"]
                if not risk["alert_required"]
                else []
            ),
            support_score=(risk["risk_score"] / 100),
            reliability=0.80,
            freshness=1.0,
            specificity=0.35,
            observed_at=observed_at,
            context={
                "risk_level": risk["risk_level"],
                "likely_causes": risk["likely_causes"],
                "reasons": risk["reasons"],
            },
        )
    )

    return items


# ==========================================================
# Population Evidence Builder
# ==========================================================


def safe_evidence_key(value: str) -> str:
    value = value.upper()

    value = re.sub(r"[^A-Z0-9]+", "_", value)

    return value.strip("_")


def build_population_evidence(population: dict) -> list[dict]:
    items: list[dict] = []

    affected_ratio = float(population["affected_ratio"])

    population_status = population["population_status"]

    sample_quality = population["sample_quality"]

    model_pattern = population["device_model_pattern"]

    likely_scope = population["likely_scope"]

    cohorts = population["model_cohorts"]

    observed_at = population["window_end"]

    # ----------------------------------
    # Population-wide affected ratio
    # ----------------------------------

    population_supports = []
    population_contradicts = []

    if (
        population_status == "WIDESPREAD_DEGRADATION"
        and model_pattern != "DEVICE_MODEL_SPECIFIC_PATTERN"
    ):
        population_supports.append("CELL_OR_NETWORK")

        population_contradicts.append("DEVICE_MODEL_OR_FIRMWARE")

    elif (
        population_status == "PARTIAL_DEGRADATION"
        and model_pattern != "DEVICE_MODEL_SPECIFIC_PATTERN"
    ):
        population_supports.append("CELL_OR_NETWORK")

    items.append(
        evidence(
            key="POPULATION_AFFECTED_RATIO",
            source="POPULATION_CORRELATION",
            category="POPULATION",
            metric="affected_ratio",
            value=affected_ratio,
            unit="ratio",
            supports=population_supports,
            contradicts=population_contradicts,
            support_score=affected_ratio,
            reliability=(0.95 if sample_quality == "STRONG" else 0.75),
            freshness=1.0,
            specificity=0.85,
            observed_at=observed_at,
            context={
                "total_devices": population["total_devices"],
                "affected_devices": population["affected_devices"],
                "healthy_devices": population["healthy_devices"],
                "population_status": population_status,
            },
        )
    )

    # ----------------------------------
    # Device model cohorts
    # ----------------------------------

    for cohort in cohorts:
        cohort_key = cohort["cohort_key"]

        cohort_ratio = float(cohort["affected_ratio"])

        cohort_supports = []

        if (
            model_pattern == "DEVICE_MODEL_SPECIFIC_PATTERN"
            and cohort_ratio >= 0.50
        ):
            cohort_supports.append("DEVICE_MODEL_OR_FIRMWARE")

        items.append(
            evidence(
                key="DEVICE_COHORT_" + safe_evidence_key(cohort_key),
                source="POPULATION_CORRELATION",
                category="DEVICE_COHORT",
                metric="affected_ratio",
                value=cohort_ratio,
                unit="ratio",
                supports=cohort_supports,
                support_score=cohort_ratio,
                reliability=(0.95 if sample_quality == "STRONG" else 0.75),
                freshness=1.0,
                specificity=0.90,
                observed_at=observed_at,
                context={
                    "cohort_key": cohort_key,
                    "total_devices": cohort["total_devices"],
                    "affected_devices": cohort["affected_devices"],
                    "healthy_devices": cohort["healthy_devices"],
                },
            )
        )

    # ----------------------------------
    # Device-model pattern evidence
    # ----------------------------------

    supports = []
    contradicts = []

    model_support_score = 0.10

    model_context = {"pattern": model_pattern}

    if model_pattern == "DEVICE_MODEL_SPECIFIC_PATTERN" and cohorts:
        candidate = max(
            cohorts,
            key=lambda item: item["affected_ratio"],
        )

        candidate_ratio = float(candidate["affected_ratio"])

        other_total = sum(
            item["total_devices"]
            for item in cohorts
            if item["cohort_key"] != candidate["cohort_key"]
        )

        other_affected = sum(
            item["affected_devices"]
            for item in cohorts
            if item["cohort_key"] != candidate["cohort_key"]
        )

        control_ratio = other_affected / other_total if other_total else 0.0

        separation = max(0.0, candidate_ratio - control_ratio)

        model_support_score = candidate_ratio * 0.60 + separation * 0.40

        supports.append("DEVICE_MODEL_OR_FIRMWARE")

        # One device model failing selectively means network-side
        # hypotheses must not be promoted blindly.
        contradicts.extend(
            [
                "CELL_OR_NETWORK",
                "CONGESTION_OR_BACKHAUL",
                "COVERAGE_OR_PROPAGATION",
                "INTERFERENCE",
                "OUTAGE",
            ]
        )

        model_context.update(
            {
                "candidate_model": candidate["cohort_key"],
                "candidate_ratio": round(candidate_ratio, 4),
                "control_ratio": round(control_ratio, 4),
                "separation": round(separation, 4),
            }
        )

    elif model_pattern == "NO_MODEL_SPECIFIC_PATTERN" and len(cohorts) >= 2:
        supports.append("CELL_OR_NETWORK")

        contradicts.append("DEVICE_MODEL_OR_FIRMWARE")

        model_support_score = min(0.90, 0.50 + affected_ratio * 0.50)

    items.append(
        evidence(
            key="DEVICE_MODEL_PATTERN",
            source="POPULATION_CORRELATION",
            category="DEVICE_COHORT",
            metric="device_model_pattern",
            value=model_pattern,
            supports=supports,
            contradicts=contradicts,
            support_score=model_support_score,
            reliability=(0.95 if sample_quality == "STRONG" else 0.70),
            freshness=1.0,
            specificity=0.95,
            observed_at=observed_at,
            context=model_context,
        )
    )

    # ----------------------------------
    # Data / sample quality
    # ----------------------------------

    quality_score = {
        "INSUFFICIENT": 0.20,
        "LOW": 0.45,
        "MODERATE": 0.70,
        "STRONG": 0.95,
    }.get(sample_quality, 0.50)

    items.append(
        evidence(
            key="POPULATION_SAMPLE_QUALITY",
            source="POPULATION_CORRELATION",
            category="DATA_QUALITY",
            metric="sample_quality",
            value=sample_quality,
            supports=[],
            contradicts=[],
            support_score=0.0,
            reliability=quality_score,
            freshness=1.0,
            specificity=0.50,
            observed_at=observed_at,
            context={
                "total_devices": population["total_devices"],
                "likely_scope": likely_scope,
            },
        )
    )

    return items


# ==========================================================
# Cross-Layer Evidence Builder
# ==========================================================


def build_cross_layer_evidence(
    *,
    population: dict,
    cross_layer: dict,
) -> list[dict]:
    items: list[dict] = []

    observed_at = population["window_end"]

    sample_quality = population["sample_quality"]

    model_pattern = population["device_model_pattern"]

    population_status = population["population_status"]

    strong_population = population_status in {
        "WIDESPREAD_DEGRADATION",
        "PARTIAL_DEGRADATION",
    }

    model_specific = model_pattern == "DEVICE_MODEL_SPECIFIC_PATTERN"

    reliability = 0.95 if sample_quality == "STRONG" else 0.75

    # Network infrastructure hypotheses
    # should not be promoted when one
    # device model is selectively failing.
    network_gate = strong_population and not model_specific

    # ----------------------------------
    # Congestion / backhaul
    # ----------------------------------

    congestion_ratio = float(cross_layer["congestion_signature_ratio"])

    items.append(
        evidence(
            key="CELL_CONGESTION_SIGNATURE",
            source="CELL_CROSS_LAYER_ANALYZER",
            category="NETWORK_PATTERN",
            metric="congestion_signature_ratio",
            value=congestion_ratio,
            unit="ratio",
            supports=(
                ["CONGESTION_OR_BACKHAUL"]
                if (network_gate and congestion_ratio >= 0.50)
                else []
            ),
            support_score=congestion_ratio,
            reliability=reliability,
            freshness=1.0,
            specificity=0.95,
            gate_passed=network_gate,
            observed_at=observed_at,
            context={
                "radio_healthy_ratio": cross_layer["radio_healthy_ratio"],
                "network_bad_ratio": cross_layer["network_bad_ratio"],
                "mean_download_mbps": cross_layer["mean_download_mbps"],
                "mean_latency_ms": cross_layer["mean_latency_ms"],
                "mean_packet_loss": cross_layer["mean_packet_loss"],
            },
        )
    )

    # ----------------------------------
    # Coverage / propagation
    # ----------------------------------

    coverage_ratio = float(cross_layer["coverage_signature_ratio"])

    items.append(
        evidence(
            key="CELL_COVERAGE_SIGNATURE",
            source="CELL_CROSS_LAYER_ANALYZER",
            category="RADIO_PATTERN",
            metric="coverage_signature_ratio",
            value=coverage_ratio,
            unit="ratio",
            supports=(
                ["COVERAGE_OR_PROPAGATION"]
                if (network_gate and coverage_ratio >= 0.50)
                else []
            ),
            support_score=coverage_ratio,
            reliability=reliability,
            freshness=1.0,
            specificity=0.90,
            gate_passed=network_gate,
            observed_at=observed_at,
            context={
                "mean_rsrp": cross_layer["mean_rsrp"],
                "mean_sinr": cross_layer["mean_sinr"],
            },
        )
    )

    # ----------------------------------
    # Interference
    # ----------------------------------

    interference_ratio = float(cross_layer["interference_signature_ratio"])

    items.append(
        evidence(
            key="CELL_INTERFERENCE_SIGNATURE",
            source="CELL_CROSS_LAYER_ANALYZER",
            category="RADIO_PATTERN",
            metric="interference_signature_ratio",
            value=interference_ratio,
            unit="ratio",
            supports=(
                ["INTERFERENCE"]
                if (network_gate and interference_ratio >= 0.50)
                else []
            ),
            support_score=interference_ratio,
            reliability=reliability,
            freshness=1.0,
            specificity=0.90,
            gate_passed=network_gate,
            observed_at=observed_at,
            context={
                "mean_rsrp": cross_layer["mean_rsrp"],
                "mean_rsrq": cross_layer["mean_rsrq"],
                "mean_sinr": cross_layer["mean_sinr"],
            },
        )
    )

    # ----------------------------------
    # Outage
    # ----------------------------------

    outage_ratio = float(cross_layer["outage_signature_ratio"])

    items.append(
        evidence(
            key="CELL_OUTAGE_SIGNATURE",
            source="CELL_CROSS_LAYER_ANALYZER",
            category="NETWORK_PATTERN",
            metric="outage_signature_ratio",
            value=outage_ratio,
            unit="ratio",
            supports=(
                ["OUTAGE"]
                if (network_gate and outage_ratio >= 0.60)
                else []
            ),
            support_score=outage_ratio,
            reliability=reliability,
            freshness=1.0,
            specificity=0.98,
            gate_passed=network_gate,
            observed_at=observed_at,
            context={
                "mean_download_mbps": cross_layer["mean_download_mbps"],
                "mean_packet_loss": cross_layer["mean_packet_loss"],
            },
        )
    )

    return items


# ==========================================================
# Cell Contextual Evidence Builder
# ==========================================================


def build_cell_context_evidence(
    *,
    population: dict,
    cross_layer: dict,
    cell_context: dict,
) -> list[dict]:
    items: list[dict] = []

    observed_at = population["window_end"]

    context_available = cell_context["context_available"]

    successful_devices = int(cell_context["successful_devices"])

    model_specific = (
        population["device_model_pattern"] == "DEVICE_MODEL_SPECIFIC_PATTERN"
    )

    coverage_ratio = float(cross_layer["coverage_signature_ratio"])

    radio_bad_ratio = max(
        0.0,
        1.0 - float(cross_layer["radio_healthy_ratio"]),
    )

    # ----------------------------------
    # Reliability based on representative
    # context sample size.
    # ----------------------------------

    if successful_devices >= 3:
        context_reliability = 0.90
    elif successful_devices == 2:
        context_reliability = 0.80
    elif successful_devices == 1:
        context_reliability = 0.65
    else:
        context_reliability = 0.0

    # ==================================================
    # TERRAIN / LOS
    # ==================================================

    blocked_ratio = float(cell_context["los_blocked_ratio"])

    propagation_high_ratio = float(cell_context["propagation_high_ratio"])

    # ----------------------------------
    # Fresnel v2 geometry (optional)
    #
    # Older cell_context payloads may not carry these
    # keys; in that case v2_available is False and the
    # gate behaves exactly like the legacy one.
    # ----------------------------------

    fresnel_available_ratio = float(
        cell_context.get(
            "fresnel_v2_available_ratio",
            0.0,
        )
        or 0.0
    )

    mean_fresnel_occupancy = float(
        cell_context.get(
            "mean_fresnel_occupancy_pct",
            0.0,
        )
        or 0.0
    )

    mean_los_blocked_pct = float(
        cell_context.get(
            "mean_los_blocked_pct",
            0.0,
        )
        or 0.0
    )

    mean_fresnel_intrusion = float(
        cell_context.get(
            "mean_max_fresnel_intrusion_m",
            0.0,
        )
        or 0.0
    )

    v2_available = fresnel_available_ratio >= 0.50

    v2_geometry_support = (
        mean_los_blocked_pct >= 20.0
        or mean_fresnel_occupancy >= 30.0
        or mean_fresnel_intrusion >= 5.0
    )

    # Legacy terrain says blocked
    # AND, when v2 is available, the geometry must
    # also support it. This lets v2 stop a binary
    # false positive from the legacy LOS flag.
    terrain_gate = (
        context_available
        and not model_specific
        and coverage_ratio >= 0.50
        and blocked_ratio >= 0.50
        and (
            not v2_available
            or v2_geometry_support
        )
    )

    # Deliberately unchanged: LOS/DEM evidence and
    # Fresnel-v2 evidence both derive from the same DEM
    # geometry, so adding v2 into the score would count
    # one source twice and inflate confidence.
    # Revisit when calibration data is available.
    terrain_strength = blocked_ratio * 0.65 + propagation_high_ratio * 0.35

    terrain_contradicts = []

    if context_available and coverage_ratio >= 0.50 and blocked_ratio <= 0.20:
        terrain_contradicts.append("TERRAIN_PROPAGATION_LIKELY")

    items.append(
        evidence(
            key="CELL_TERRAIN_CONTEXT",
            source="CELL_CONTEXT_ANALYZER",
            category="GEO",
            metric="los_blocked_ratio",
            value=blocked_ratio,
            unit="ratio",
            supports=(
                ["TERRAIN_PROPAGATION_LIKELY"] if terrain_gate else []
            ),
            contradicts=terrain_contradicts,
            support_score=terrain_strength,
            reliability=context_reliability,
            freshness=0.95,
            specificity=0.95,
            gate_passed=terrain_gate,
            observed_at=observed_at,
            context={
                "coverage_signature_ratio": coverage_ratio,
                "propagation_high_ratio": propagation_high_ratio,
                "mean_geo_vulnerability": cell_context[
                    "mean_geo_vulnerability"
                ],
                "sampled_devices": cell_context["sampled_devices"],
                "successful_devices": successful_devices,
                "fresnel_v2_available_ratio": fresnel_available_ratio,
                "mean_los_blocked_pct": cell_context.get(
                    "mean_los_blocked_pct"
                ),
                "mean_fresnel_occupancy_pct": cell_context.get(
                    "mean_fresnel_occupancy_pct"
                ),
                "mean_minimum_clearance_ratio": cell_context.get(
                    "mean_minimum_clearance_ratio"
                ),
                "mean_max_fresnel_intrusion_m": cell_context.get(
                    "mean_max_fresnel_intrusion_m"
                ),
                "worst_fresnel_obstruction": cell_context.get(
                    "worst_fresnel_obstruction"
                ),
            },
        )
    )

    # ==================================================
    # VEGETATION / CLUTTER
    # ==================================================

    vegetation_ratio = float(cell_context["vegetation_heavy_ratio"])

    environment_high_ratio = float(cell_context["environment_high_ratio"])

    vegetation_gate = (
        context_available
        and not model_specific
        and coverage_ratio >= 0.50
        and vegetation_ratio >= 0.50
    )

    vegetation_strength = (
        vegetation_ratio * 0.65 + environment_high_ratio * 0.35
    )

    items.append(
        evidence(
            key="CELL_VEGETATION_CONTEXT",
            source="CELL_CONTEXT_ANALYZER",
            category="ENVIRONMENT",
            metric="vegetation_heavy_ratio",
            value=vegetation_ratio,
            unit="ratio",
            supports=(
                ["VEGETATION_PROPAGATION_POSSIBLE"]
                if vegetation_gate
                else []
            ),
            support_score=vegetation_strength,
            reliability=context_reliability,
            # WorldCover is static context,
            # not real-time telemetry.
            freshness=0.70,
            specificity=0.80,
            gate_passed=vegetation_gate,
            observed_at=observed_at,
            context={
                "coverage_signature_ratio": coverage_ratio,
                "environment_high_ratio": environment_high_ratio,
                "mean_environmental_vulnerability": cell_context[
                    "mean_environmental_vulnerability"
                ],
            },
        )
    )

    # ==================================================
    # WEATHER
    # ==================================================

    weather_ratio = float(cell_context["weather_elevated_ratio"])

    mean_weather = cell_context["mean_weather_score"]

    weather_gate = (
        context_available
        and not model_specific
        and radio_bad_ratio >= 0.50
        and weather_ratio >= 0.50
    )

    normalized_weather = min(1.0, float(mean_weather or 0.0) / 50.0)

    weather_strength = weather_ratio * 0.60 + normalized_weather * 0.40

    items.append(
        evidence(
            key="CELL_WEATHER_CONTEXT",
            source="CELL_CONTEXT_ANALYZER",
            category="WEATHER",
            metric="weather_elevated_ratio",
            value=weather_ratio,
            unit="ratio",
            supports=(
                ["WEATHER_STRESS_POSSIBLE"] if weather_gate else []
            ),
            support_score=weather_strength,
            reliability=context_reliability * 0.90,
            freshness=1.0,
            specificity=0.70,
            gate_passed=weather_gate,
            observed_at=observed_at,
            context={
                "radio_bad_ratio": round(radio_bad_ratio, 4),
                "mean_weather_score": mean_weather,
            },
        )
    )

    # ==================================================
    # HISTORICAL PERSISTENCE
    # ==================================================

    historical_poor_ratio = float(cell_context["historical_poor_ratio"])

    historical_gate = context_available and historical_poor_ratio >= 0.50

    items.append(
        evidence(
            key="CELL_HISTORICAL_CONTEXT",
            source="CELL_CONTEXT_ANALYZER",
            category="HISTORY",
            metric="historical_poor_ratio",
            value=historical_poor_ratio,
            unit="ratio",
            # This is condition evidence,
            # not a physical root cause.
            supports=(
                ["PERSISTENT_DEGRADATION"] if historical_gate else []
            ),
            support_score=historical_poor_ratio,
            reliability=context_reliability,
            freshness=0.90,
            specificity=0.60,
            gate_passed=historical_gate,
            observed_at=observed_at,
            context={
                "mean_historical_health": cell_context[
                    "mean_historical_health"
                ],
            },
        )
    )

    return items