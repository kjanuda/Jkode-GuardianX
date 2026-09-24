def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def get_risk_level(
    score: float,
) -> str:
    if score < 25:
        return "LOW"

    if score < 50:
        return "MEDIUM"

    if score < 75:
        return "HIGH"

    return "CRITICAL"


def get_geo_vulnerability_level(
    score: float,
) -> str:
    if score < 30:
        return "LOW"

    if score < 60:
        return "MODERATE"

    return "HIGH"


def calculate_historical_risk(
    historical: dict,
) -> float:
    health_score = historical[
        "historical_health_score"
    ]

    trend = historical[
        "overall_trend"
    ]

    # Poor sustained health itself is risk.
    historical_risk = (
        100 - health_score
    )

    # Trend is a directional adjustment.
    if trend == "DEGRADING":
        historical_risk += 15

    elif trend == "IMPROVING":
        historical_risk -= 10

    return round(
        clamp(
            historical_risk
        ),
        2,
    )


def radio_supports_environmental_cause(
    telemetry,
    radio_score: float,
) -> bool:
    if radio_score >= 60:
        return False

    weak_rsrp = (
        telemetry.rsrp is not None
        and telemetry.rsrp < -105
    )

    weak_sinr = (
        telemetry.sinr is not None
        and telemetry.sinr < 10
    )

    poor_rsrq = (
        telemetry.rsrq is not None
        and telemetry.rsrq <= -13
    )

    return (
        weak_rsrp
        or weak_sinr
        or poor_rsrq
    )


def weather_supports_current_degradation(
    telemetry,
    radio_score: float,
    weather_context: dict,
) -> bool:
    if not weather_context["available"]:
        return False

    if radio_score >= 60:
        return False

    strong_weather = (
        weather_context[
            "precipitation_mm"
        ] >= 5
        or weather_context[
            "wind_gusts_kmh"
        ] >= 50
        or weather_context[
            "weather_context_score"
        ] >= 25
    )

    degraded_radio = (
        (
            telemetry.rsrp is not None
            and telemetry.rsrp < -105
        )
        or (
            telemetry.sinr is not None
            and telemetry.sinr < 7
        )
    )

    return (
        strong_weather
        and degraded_radio
    )


def detect_likely_causes(
    telemetry,
    current_features: dict,
    geo_context: dict,
    environment_context: dict,
    weather_context: dict,
) -> list[str]:
    causes = []

    radio_score = current_features[
        "radio_score"
    ]

    network_score = current_features[
        "network_score"
    ]

    # ------------------------------------------------
    # Outage
    # ------------------------------------------------

    if (
        radio_score < 30
        and network_score < 20
        and (
            (
                telemetry.packet_loss
                is not None
                and telemetry.packet_loss >= 50
            )
            or (
                telemetry.download_mbps
                is not None
                and telemetry.download_mbps < 1
            )
        )
    ):
        causes.append(
            "OUTAGE_LIKELY"
        )

    # ------------------------------------------------
    # Congestion / Backhaul
    # Good/usable RF + poor network
    # ------------------------------------------------

    if (
        radio_score >= 60
        and network_score < 45
    ):
        causes.append(
            "CONGESTION_OR_BACKHAUL"
        )

    # ------------------------------------------------
    # Interference
    # ------------------------------------------------

    if (
        telemetry.rsrp is not None
        and telemetry.rsrq is not None
        and telemetry.sinr is not None
        and telemetry.rsrp >= -100
        and telemetry.rsrq <= -13
        and telemetry.sinr < 7
    ):
        causes.append(
            "INTERFERENCE_LIKELY"
        )

    # ------------------------------------------------
    # Generic coverage / propagation problem
    # ------------------------------------------------

    if (
        telemetry.rsrp is not None
        and telemetry.sinr is not None
        and telemetry.rsrp < -110
        and telemetry.sinr < 7
    ):
        causes.append(
            "COVERAGE_OR_PROPAGATION"
        )

    environmental_rf_support = (
        radio_supports_environmental_cause(
            telemetry=telemetry,
            radio_score=radio_score,
        )
    )

    # ------------------------------------------------
    # Terrain attribution
    # ------------------------------------------------

    if (
        geo_context[
            "terrain_obstructed"
        ]
        and environmental_rf_support
    ):
        causes.append(
            "TERRAIN_PROPAGATION_LIKELY"
        )

    elif (
        geo_context[
            "fresnel_60_obstructed"
        ]
        and environmental_rf_support
    ):
        causes.append(
            "FRESNEL_OBSTRUCTION_POSSIBLE"
        )

    # ------------------------------------------------
    # Buildings / urban clutter
    # ------------------------------------------------

    if environment_context[
        "available"
    ]:
        built_environment_high = (
            environment_context[
                "built_up_pct"
            ]
            >= 25
            or environment_context[
                "building_density_per_km2"
            ]
            >= 200
        )

        if (
            built_environment_high
            and environmental_rf_support
            and (
                (
                    telemetry.sinr is not None
                    and telemetry.sinr < 10
                )
                or (
                    telemetry.rsrq is not None
                    and telemetry.rsrq <= -13
                )
            )
        ):
            causes.append(
                "BUILDING_CLUTTER_POSSIBLE"
            )

        # --------------------------------------------
        # Vegetation
        # --------------------------------------------

        dense_vegetation = (
            environment_context[
                "tree_cover_pct"
            ]
            >= 40
        )

        if (
            dense_vegetation
            and environmental_rf_support
            and (
                (
                    telemetry.rsrp is not None
                    and telemetry.rsrp < -100
                )
                or (
                    telemetry.sinr is not None
                    and telemetry.sinr < 10
                )
            )
        ):
            causes.append(
                "VEGETATION_PROPAGATION_POSSIBLE"
            )

    # ------------------------------------------------
    # Weather
    # ------------------------------------------------

    if weather_supports_current_degradation(
        telemetry=telemetry,
        radio_score=radio_score,
        weather_context=weather_context,
    ):
        causes.append(
            "WEATHER_STRESS_POSSIBLE"
        )

    # ------------------------------------------------
    # Fallback
    # ------------------------------------------------

    if not causes:
        if (
            radio_score >= 70
            and network_score >= 70
        ):
            causes.append(
                "NO_MAJOR_DEGRADATION"
            )

        else:
            causes.append(
                "GENERAL_DEGRADATION"
            )

    return causes


def build_reasons(
    telemetry,
    current_features: dict,
    historical: dict,
    geo_context: dict,
    environment_context: dict,
    weather_context: dict,
) -> list[str]:
    reasons = []

    radio_score = current_features[
        "radio_score"
    ]

    environmental_rf_support = (
        radio_supports_environmental_cause(
            telemetry=telemetry,
            radio_score=radio_score,
        )
    )

    # ------------------------------------------------
    # Current service evidence
    # ------------------------------------------------

    if radio_score < 40:
        reasons.append(
            "Current radio quality is poor"
        )

    if (
        current_features[
            "network_score"
        ]
        < 40
    ):
        reasons.append(
            "Current network performance is poor"
        )

    if (
        telemetry.rsrp is not None
        and telemetry.rsrp < -110
    ):
        reasons.append(
            f"Weak RSRP: "
            f"{telemetry.rsrp:.2f} dBm"
        )

    if (
        telemetry.sinr is not None
        and telemetry.sinr < 7
    ):
        reasons.append(
            f"Low SINR: "
            f"{telemetry.sinr:.2f} dB"
        )

    if (
        telemetry.latency_ms is not None
        and telemetry.latency_ms > 100
    ):
        reasons.append(
            f"High latency: "
            f"{telemetry.latency_ms:.2f} ms"
        )

    if (
        telemetry.packet_loss is not None
        and telemetry.packet_loss > 2
    ):
        reasons.append(
            f"Elevated packet loss: "
            f"{telemetry.packet_loss:.2f}%"
        )

    if (
        telemetry.download_mbps is not None
        and telemetry.download_mbps < 15
    ):
        reasons.append(
            f"Low download throughput: "
            f"{telemetry.download_mbps:.2f} Mbps"
        )

    # ------------------------------------------------
    # History
    # ------------------------------------------------

    if (
        historical[
            "overall_trend"
        ]
        == "DEGRADING"
    ):
        degrading = ", ".join(
            historical[
                "degrading_metrics"
            ]
        )

        reasons.append(
            "Historical trend is degrading"
            + (
                f" ({degrading})"
                if degrading
                else ""
            )
        )

    # ------------------------------------------------
    # Terrain
    # ------------------------------------------------

    if geo_context[
        "terrain_obstructed"
    ]:
        if environmental_rf_support:
            reasons.append(
                "Terrain obstruction is "
                "consistent with the current "
                "radio degradation"
            )

        else:
            reasons.append(
                "The location has a terrain "
                "obstruction, but current radio "
                "conditions remain relatively healthy"
            )

    elif geo_context[
        "fresnel_60_obstructed"
    ]:
        if environmental_rf_support:
            reasons.append(
                "Reduced Fresnel clearance is "
                "consistent with the current "
                "radio degradation"
            )

        else:
            reasons.append(
                "The location has reduced "
                "60% Fresnel-zone clearance"
            )

    # ------------------------------------------------
    # Distance / sector
    # ------------------------------------------------

    if (
        geo_context[
            "distance_km"
        ]
        >= 5
    ):
        reasons.append(
            f"Serving tower is "
            f"{geo_context['distance_km']:.2f} km away"
        )

    if (
        geo_context[
            "sector_alignment"
        ]
        == "OUTSIDE_MAIN_DIRECTION"
    ):
        reasons.append(
            "Device is outside the serving "
            "sector's main azimuth direction"
        )

    # ------------------------------------------------
    # Environmental evidence
    # ------------------------------------------------

    if environment_context[
        "available"
    ]:
        built_up_pct = (
            environment_context[
                "built_up_pct"
            ]
        )

        tree_cover_pct = (
            environment_context[
                "tree_cover_pct"
            ]
        )

        building_density = (
            environment_context[
                "building_density_per_km2"
            ]
        )

        if (
            built_up_pct >= 25
            or building_density >= 200
        ):
            if environmental_rf_support:
                reasons.append(
                    "Dense built-environment "
                    "context may contribute to "
                    "current RF degradation"
                )

            else:
                reasons.append(
                    "Dense built-environment "
                    "context exists, but current "
                    "RF evidence does not indicate "
                    "a building-related degradation"
                )

        if tree_cover_pct >= 40:
            if environmental_rf_support:
                reasons.append(
                    f"High tree-cover context "
                    f"({tree_cover_pct:.2f}%) may "
                    f"contribute to propagation loss"
                )

            else:
                reasons.append(
                    f"Tree cover is high "
                    f"({tree_cover_pct:.2f}%), but "
                    f"current RF conditions do not "
                    f"strongly support vegetation "
                    f"as the current cause"
                )

    # ------------------------------------------------
    # Weather context
    # ------------------------------------------------

    if weather_context[
        "available"
    ]:
        if weather_supports_current_degradation(
            telemetry=telemetry,
            radio_score=radio_score,
            weather_context=weather_context,
        ):
            reasons.append(
                "Elevated weather conditions "
                "may be contributing to the "
                "current RF degradation"
            )

        elif (
            weather_context[
                "weather_context_score"
            ]
            >= 10
        ):
            reasons.append(
                "Moderate weather stress is "
                "present, but current evidence "
                "does not strongly attribute the "
                "service degradation to weather"
            )

    if not reasons:
        reasons.append(
            "No significant degradation "
            "indicators detected"
        )

    return reasons


def calculate_risk(
    telemetry,
    current_features: dict,
    historical: dict,
    geo_context: dict,
    environment_context: dict,
    weather_context: dict,
) -> dict:
    # ------------------------------------------------
    # Current service components
    # ------------------------------------------------

    radio_risk = (
        100
        - current_features[
            "radio_score"
        ]
    )

    network_risk = (
        100
        - current_features[
            "network_score"
        ]
    )

    historical_risk = (
        calculate_historical_risk(
            historical
        )
    )

    # ------------------------------------------------
    # Structural vulnerability
    # ------------------------------------------------

    geo_vulnerability = (
        geo_context[
            "geo_vulnerability"
        ]
    )

    if environment_context[
        "available"
    ]:
        clutter_vulnerability = (
            environment_context[
                "clutter_vulnerability"
            ]
        )

        environmental_vulnerability = (
            environment_context[
                "environmental_vulnerability"
            ]
        )

        environmental_level = (
            environment_context[
                "environmental_vulnerability_level"
            ]
        )

    else:
        clutter_vulnerability = 0.0
        environmental_vulnerability = 0.0
        environmental_level = "UNAVAILABLE"

    if weather_context[
        "available"
    ]:
        weather_score = (
            weather_context[
                "weather_context_score"
            ]
        )

        weather_level = (
            weather_context[
                "weather_context_level"
            ]
        )

    else:
        weather_score = 0.0
        weather_level = "UNAVAILABLE"

    # ------------------------------------------------
    # Core current service risk
    #
    # Structural conditions are deliberately NOT
    # permanently included in this base score.
    # ------------------------------------------------

    base_risk = (
        radio_risk * 0.35
        + network_risk * 0.45
        + historical_risk * 0.20
    )

    # ------------------------------------------------
    # Geo influence
    # ------------------------------------------------

    geo_influence = 0.0

    if (
        geo_vulnerability >= 60
        and radio_risk >= 60
    ):
        geo_influence = min(
            15,
            geo_vulnerability * 0.15,
        )

    elif (
        geo_vulnerability >= 60
        and radio_risk >= 40
    ):
        geo_influence = min(
            10,
            geo_vulnerability * 0.10,
        )

    # ------------------------------------------------
    # Building / vegetation clutter influence
    # ------------------------------------------------

    clutter_influence = 0.0

    if environment_context[
        "available"
    ]:
        if (
            clutter_vulnerability >= 60
            and radio_risk >= 60
        ):
            clutter_influence = min(
                10,
                clutter_vulnerability * 0.10,
            )

        elif (
            clutter_vulnerability >= 60
            and radio_risk >= 40
        ):
            clutter_influence = min(
                6,
                clutter_vulnerability * 0.06,
            )

        elif (
            clutter_vulnerability >= 40
            and radio_risk >= 60
        ):
            clutter_influence = min(
                5,
                clutter_vulnerability * 0.05,
            )

    # Prevent environmental factors from
    # overwhelming measured current service data.
    structural_influence = min(
        20,
        geo_influence
        + clutter_influence,
    )

    # ------------------------------------------------
    # Dynamic weather influence
    #
    # Weather gets only a small influence and
    # only when measured radio conditions are bad.
    # ------------------------------------------------

    weather_influence = 0.0

    weather_supported = (
        weather_supports_current_degradation(
            telemetry=telemetry,
            radio_score=current_features[
                "radio_score"
            ],
            weather_context=weather_context,
        )
    )

    if weather_supported:
        if (
            weather_score >= 40
            and radio_risk >= 60
        ):
            weather_influence = 5.0

        elif (
            weather_score >= 25
            and radio_risk >= 60
        ):
            weather_influence = 3.0

        elif weather_score >= 25:
            weather_influence = 2.0

    contextual_influence = min(
        25,
        structural_influence
        + weather_influence,
    )

    risk_score = (
        base_risk
        + contextual_influence
    )

    # ------------------------------------------------
    # Current-service severity floors
    # ------------------------------------------------

    if (
        current_features[
            "network_health"
        ]
        == "CRITICAL"
        and network_risk >= 60
    ):
        risk_score = max(
            risk_score,
            50,
        )

    if (
        current_features[
            "radio_health"
        ]
        == "CRITICAL"
        and current_features[
            "network_health"
        ]
        == "CRITICAL"
    ):
        risk_score = max(
            risk_score,
            75,
        )

    risk_score = round(
        clamp(risk_score),
        2,
    )

    # ------------------------------------------------
    # Causes
    # ------------------------------------------------

    likely_causes = (
        detect_likely_causes(
            telemetry=telemetry,
            current_features=current_features,
            geo_context=geo_context,
            environment_context=(
                environment_context
            ),
            weather_context=weather_context,
        )
    )

    if (
        "OUTAGE_LIKELY"
        in likely_causes
    ):
        risk_score = max(
            risk_score,
            85,
        )

    risk_level = (
        get_risk_level(
            risk_score
        )
    )

    reasons = build_reasons(
        telemetry=telemetry,
        current_features=current_features,
        historical=historical,
        geo_context=geo_context,
        environment_context=(
            environment_context
        ),
        weather_context=weather_context,
    )

    return {
        "risk_score":
            round(
                risk_score,
                2,
            ),

        "risk_level":
            risk_level,

        "geo_vulnerability_score":
            round(
                geo_vulnerability,
                2,
            ),

        "geo_vulnerability_level":
            get_geo_vulnerability_level(
                geo_vulnerability
            ),

        "environmental_vulnerability_score":
            round(
                environmental_vulnerability,
                2,
            ),

        "environmental_vulnerability_level":
            environmental_level,

        "clutter_vulnerability_score":
            round(
                clutter_vulnerability,
                2,
            ),

        "environment_type":
            environment_context[
                "environment_type"
            ],

        "environment_context_available":
            environment_context[
                "available"
            ],

        "weather_context_available":
            weather_context[
                "available"
            ],

        "weather_context_score":
            round(
                weather_score,
                2,
            ),

        "weather_context_level":
            weather_level,

        "weather_factors":
            weather_context[
                "factors"
            ],

        "components": {
            "radio_risk":
                round(
                    radio_risk,
                    2,
                ),

            "network_risk":
                round(
                    network_risk,
                    2,
                ),

            "historical_risk":
                round(
                    historical_risk,
                    2,
                ),

            "geo_vulnerability":
                round(
                    geo_vulnerability,
                    2,
                ),

            "clutter_vulnerability":
                round(
                    clutter_vulnerability,
                    2,
                ),

            "weather_context":
                round(
                    weather_score,
                    2,
                ),

            "geo_influence":
                round(
                    geo_influence,
                    2,
                ),

            "clutter_influence":
                round(
                    clutter_influence,
                    2,
                ),

            "weather_influence":
                round(
                    weather_influence,
                    2,
                ),

            "structural_influence":
                round(
                    structural_influence,
                    2,
                ),

            "contextual_influence":
                round(
                    contextual_influence,
                    2,
                ),
        },

        "current_radio_health":
            current_features[
                "radio_health"
            ],

        "current_network_health":
            current_features[
                "network_health"
            ],

        "historical_trend":
            historical[
                "overall_trend"
            ],

        "historical_health_score":
            historical[
                "historical_health_score"
            ],

        "historical_health":
            historical[
                "historical_health"
            ],

        "persistent_poor_state":
            historical[
                "persistent_poor_state"
            ],

        "propagation_risk":
            geo_context[
                "propagation_risk"
            ],

        "los_status":
            geo_context[
                "los_status"
            ],

        "likely_causes":
            likely_causes,

        "reasons":
            reasons,

        "alert_required":
            risk_level
            in {
                "HIGH",
                "CRITICAL",
            },
    }