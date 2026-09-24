from __future__ import annotations

from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)

from app.rca.fusion import (
    fuse_evidence,
)


NETWORK_DOMAIN_CAUSES = {
    "CONGESTION_OR_BACKHAUL",
    "COVERAGE_OR_PROPAGATION",
    "INTERFERENCE",
    "OUTAGE",
}

PROPAGATION_CHILDREN = {
    "TERRAIN_PROPAGATION_LIKELY",
    "VEGETATION_PROPAGATION_POSSIBLE",
    "WEATHER_STRESS_POSSIBLE",
}


def ranking_by_cause(
    fusion: dict,
) -> dict[str, dict]:
    return {
        item["cause"]: item
        for item in fusion["rankings"]
    }


def best_available(
    *,
    rankings: dict[str, dict],
    allowed: set[str],
) -> dict | None:
    candidates = [
        rankings[cause]
        for cause in allowed
        if cause in rankings
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item:
            item["confidence"],
    )


def evidence_by_key(
    evidence_items: list[RCAEvidence],
) -> dict[str, RCAEvidence]:
    return {
        item.evidence_key: item
        for item in evidence_items
    }


def build_hierarchical_rca(
    *,
    fusion: dict,
    evidence_items: list[RCAEvidence],
) -> dict:
    rankings = ranking_by_cause(
        fusion
    )

    evidence_map = evidence_by_key(
        evidence_items
    )

    device_result = rankings.get(
        "DEVICE_MODEL_OR_FIRMWARE"
    )

    best_network = best_available(
        rankings=rankings,
        allowed=NETWORK_DOMAIN_CAUSES,
    )

    # -----------------------------------
    # DEVICE-SPECIFIC INCIDENT
    # -----------------------------------

    if (
        device_result is not None
        and device_result[
            "confidence"
        ] >= 0.50
        and (
            best_network is None
            or device_result[
                "confidence"
            ]
            > best_network[
                "confidence"
            ]
        )
    ):
        domain = {
            "cause":
                "DEVICE_DOMAIN",

            "confidence":
                device_result[
                    "confidence"
                ],

            "confidence_percent":
                device_result[
                    "confidence_percent"
                ],
        }

        primary_root = {
            "cause":
                "DEVICE_MODEL_OR_FIRMWARE",

            "confidence":
                device_result[
                    "confidence"
                ],

            "confidence_percent":
                device_result[
                    "confidence_percent"
                ],

            "confidence_label":
                device_result[
                    "confidence_label"
                ],
        }

        contributors = []

    # -----------------------------------
    # NETWORK / CELL INCIDENT
    # -----------------------------------

    else:
        if best_network is None:
            domain = {
                "cause":
                    fusion[
                        "primary_cause"
                    ],

                "confidence":
                    fusion[
                        "primary_confidence"
                    ],

                "confidence_percent":
                    fusion[
                        "primary_confidence_percent"
                    ],
            }

            primary_root = dict(
                domain
            )

            contributors = []

        else:
            domain = {
                "cause":
                    best_network[
                        "cause"
                    ],

                "confidence":
                    best_network[
                        "confidence"
                    ],

                "confidence_percent":
                    best_network[
                        "confidence_percent"
                    ],
            }

            primary_root = {
                "cause":
                    best_network[
                        "cause"
                    ],

                "confidence":
                    best_network[
                        "confidence"
                    ],

                "confidence_percent":
                    best_network[
                        "confidence_percent"
                    ],

                "confidence_label":
                    best_network[
                        "confidence_label"
                    ],
            }

            contributors = []

            # Coverage is a domain-level diagnosis.
            # Try to find the physical cause beneath it.
            if (
                best_network["cause"]
                == "COVERAGE_OR_PROPAGATION"
            ):
                propagation_children = [
                    rankings[cause]
                    for cause
                    in PROPAGATION_CHILDREN
                    if cause in rankings
                ]

                propagation_children.sort(
                    key=lambda item:
                        item["confidence"],
                    reverse=True,
                )

                if propagation_children:
                    strongest = (
                        propagation_children[0]
                    )

                    # Only promote a physical
                    # root cause when evidence
                    # strength is meaningful.
                    if (
                        strongest[
                            "confidence"
                        ]
                        >= 0.50
                    ):
                        primary_root = {
                            "cause":
                                strongest[
                                    "cause"
                                ],

                            "confidence":
                                strongest[
                                    "confidence"
                                ],

                            "confidence_percent":
                                strongest[
                                    "confidence_percent"
                                ],

                            "confidence_label":
                                strongest[
                                    "confidence_label"
                                ],
                        }

                    for item in (
                        propagation_children
                    ):
                        if (
                            item["cause"]
                            == primary_root[
                                "cause"
                            ]
                        ):
                            continue

                        if (
                            item[
                                "confidence"
                            ]
                            >= 0.25
                        ):
                            contributors.append(
                                {
                                    "cause":
                                        item[
                                            "cause"
                                        ],

                                    "confidence":
                                        item[
                                            "confidence"
                                        ],

                                    "confidence_percent":
                                        item[
                                            "confidence_percent"
                                        ],

                                    "confidence_label":
                                        item[
                                            "confidence_label"
                                        ],
                                }
                            )

    historical = evidence_map.get(
        "CELL_HISTORICAL_CONTEXT"
    )

    weather = evidence_map.get(
        "CELL_WEATHER_CONTEXT"
    )

    model_pattern = evidence_map.get(
        "DEVICE_MODEL_PATTERN"
    )

    persistent = bool(
        historical
        and historical.gate_passed
        and "PERSISTENT_DEGRADATION"
        in (
            historical.supports_causes
            or []
        )
    )

    weather_causal = bool(
        weather
        and weather.gate_passed
        and "WEATHER_STRESS_POSSIBLE"
        in (
            weather.supports_causes
            or []
        )
    )

    device_specific = bool(
        model_pattern
        and (
            model_pattern.value_json
            or {}
        ).get("value")
        == "DEVICE_MODEL_SPECIFIC_PATTERN"
    )

    return {
        "engine_type":
            "HIERARCHICAL_RCA_V1",

        "incident_domain":
            domain,

        "primary_root_cause":
            primary_root,

        "contributing_factors":
            contributors,

        "conditions": {
            "persistent_degradation":
                persistent,

            "weather_causal_evidence":
                weather_causal,

            "device_specific_pattern":
                device_specific,
        },

        "flat_fusion":
            fusion,

        "explanation": (
            "Incident domain describes "
            "the failure family. "
            "Primary root cause is the "
            "strongest sufficiently "
            "supported causal explanation "
            "within that domain."
        ),
    }


def run_hierarchical_rca(
    *,
    db: Session,
    case_id: int,
) -> dict:
    case = db.get(
        RCACase,
        case_id,
    )

    if case is None:
        raise ValueError(
            "RCA case not found"
        )

    evidence_items = list(
        db.scalars(
            select(
                RCAEvidence
            )
            .where(
                RCAEvidence.case_id
                == case.id
            )
            .order_by(
                RCAEvidence.id.asc()
            )
        ).all()
    )

    if not evidence_items:
        raise ValueError(
            "RCA case has no evidence"
        )

    fusion = fuse_evidence(
        evidence_items
    )

    result = build_hierarchical_rca(
        fusion=fusion,
        evidence_items=evidence_items,
    )

    db.execute(
        delete(
            RCAPrediction
        ).where(
            RCAPrediction.case_id
            == case.id,

            RCAPrediction.engine_type
            == "HIERARCHICAL_RCA_V1",
        )
    )

    root = result[
        "primary_root_cause"
    ]

    prediction = RCAPrediction(
        case_id=case.id,

        engine_type=(
            "HIERARCHICAL_RCA_V1"
        ),

        primary_cause=(
            root["cause"]
        ),

        confidence=(
            root["confidence"]
        ),

        rank=1,

        output_json=result,

        verifier_status=(
            "HIERARCHICAL_NOT_VERIFIED"
        ),

        verifier_reason=None,
    )

    db.add(
        prediction
    )

    db.commit()

    return result