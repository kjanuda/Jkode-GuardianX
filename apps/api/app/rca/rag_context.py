from __future__ import annotations

from typing import Any


# ============================================================
# LLM RELEVANT EVIDENCE
# ============================================================

LLM_RELEVANT_EVIDENCE_KEYS = {
    "POPULATION_AFFECTED_RATIO",
    "DEVICE_MODEL_PATTERN",

    "CELL_CONGESTION_SIGNATURE",
    "CELL_COVERAGE_SIGNATURE",
    "CELL_INTERFERENCE_SIGNATURE",
    "CELL_OUTAGE_SIGNATURE",

    "CELL_TERRAIN_CONTEXT",
    "CELL_VEGETATION_CONTEXT",
    "CELL_WEATHER_CONTEXT",
    "CELL_HISTORICAL_CONTEXT",
}


# ============================================================
# ALLOWED LLM CONTEXT FIELDS
# ============================================================

LLM_CONTEXT_FIELDS = {
    "POPULATION_AFFECTED_RATIO": {
        "total_devices",
        "affected_devices",
        "healthy_devices",
        "population_status",
    },

    "DEVICE_MODEL_PATTERN": {
        "pattern",
    },

    "CELL_CONGESTION_SIGNATURE": {
        "mean_latency_ms",
        "mean_packet_loss",
        "network_bad_ratio",
        "mean_download_mbps",
        "radio_healthy_ratio",
    },

    "CELL_COVERAGE_SIGNATURE": {
        "mean_rsrp",
        "mean_sinr",
    },

    "CELL_INTERFERENCE_SIGNATURE": {
        "mean_rsrp",
        "mean_rsrq",
        "mean_sinr",
    },

    "CELL_OUTAGE_SIGNATURE": {
        "mean_packet_loss",
        "mean_download_mbps",
    },

    "CELL_TERRAIN_CONTEXT": {
        "sampled_devices",
        "successful_devices",
        "mean_los_blocked_pct",
        "mean_geo_vulnerability",
        "propagation_high_ratio",
        "coverage_signature_ratio",
        "fresnel_v2_available_ratio",
        "mean_fresnel_occupancy_pct",
        "mean_max_fresnel_intrusion_m",
        "mean_minimum_clearance_ratio",
    },

    "CELL_VEGETATION_CONTEXT": {
        "environment_high_ratio",
        "coverage_signature_ratio",
        "mean_environmental_vulnerability",
    },

    "CELL_WEATHER_CONTEXT": {
        "radio_bad_ratio",
        "mean_weather_score",
    },

    "CELL_HISTORICAL_CONTEXT": {
        "mean_historical_health",
    },
}


# ============================================================
# CANONICAL EVIDENCE PACKET
# ============================================================

def build_rag_evidence_packet(
    *,
    case_id: int,
    evidence_items: list,
) -> dict[str, Any]:
    """
    Build the canonical Guardian X RCA evidence packet.

    This packet preserves the complete evidence required
    by deterministic Rules / ML / RCA verification.

    The LLM should NOT receive the complete packet directly.

    The canonical packet preserves:

        - source provenance
        - evidence identity
        - measurement/value data
        - units
        - observation time
        - structured context
        - causal support
        - causal contradiction
        - evidence quality scores
        - evidence gate state

    The packet is informational only.

    Final RCA acceptance must be performed by the
    deterministic proposal verifier.
    """

    evidence: list[dict[str, Any]] = []

    for item in evidence_items:
        evidence.append(
            {
                # -----------------------------------------
                # Identity / provenance
                # -----------------------------------------

                "evidence_id":
                    item.id,

                "evidence_key":
                    item.evidence_key,

                "source":
                    item.source,

                "category":
                    item.category,

                "metric":
                    item.metric,

                # -----------------------------------------
                # Actual observed value
                # -----------------------------------------

                "value":
                    item.value_json,

                "unit":
                    item.unit,

                "observed_at":
                    (
                        item.observed_at.isoformat()
                        if item.observed_at
                        else None
                    ),

                # -----------------------------------------
                # Structured measurement context
                # -----------------------------------------

                "context":
                    item.context_json
                    or {},

                # -----------------------------------------
                # Causal relationship metadata
                # -----------------------------------------

                "supports_causes":
                    item.supports_causes
                    or [],

                "contradicts_causes":
                    item.contradicts_causes
                    or [],

                # -----------------------------------------
                # Evidence quality
                # -----------------------------------------

                "support_score":
                    float(
                        item.support_score
                        or 0.0
                    ),

                "reliability_score":
                    float(
                        item.reliability_score
                        or 0.0
                    ),

                "freshness_score":
                    float(
                        item.freshness_score
                        or 0.0
                    ),

                "specificity_score":
                    float(
                        item.specificity_score
                        or 0.0
                    ),

                # -----------------------------------------
                # Evidence gate
                # -----------------------------------------

                "gate_passed":
                    item.gate_passed,
            }
        )

    return {
        "schema_version":
            "RCA_EVIDENCE_PACKET_V1",

        "case_id":
            case_id,

        "evidence_count":
            len(
                evidence
            ),

        "evidence":
            evidence,

        # ---------------------------------------------
        # Reasoning contract
        # ---------------------------------------------

        "instruction": (
            "Use only the supplied evidence. "
            "Do not invent measurements, timestamps, "
            "locations, metrics, or causal facts. "
            "Any proposed root cause must reference "
            "one or more supporting evidence IDs. "
            "Evidence IDs must correspond to supplied "
            "evidence records. "
            "Treat supports_causes and "
            "contradicts_causes as structured evidence "
            "metadata, not as permission to ignore the "
            "actual observed values. "
            "Do not treat reasoning_summary as evidence. "
            "Final proposal acceptance is determined "
            "by the RCA proposal verifier."
        ),
    }


# ============================================================
# COMPACT LLM PACKET
# ============================================================

def build_compact_llm_packet(
    *,
    evidence_packet: dict[str, Any],
) -> dict[str, Any]:
    """
    Reduce the canonical evidence packet to the
    information required by the local LLM.

    The complete canonical evidence packet remains
    available to the deterministic verifier.

    The LLM receives only:

        - relevant evidence IDs
        - relevant evidence keys
        - category
        - observed value
        - causal metadata
        - evidence quality scores
        - gate state
        - selected decision-relevant context fields

    Large raw context objects such as detailed
    Fresnel obstruction geometry are intentionally
    excluded from the LLM packet.
    """

    compact_evidence: list[dict[str, Any]] = []

    for item in evidence_packet.get(
        "evidence",
        [],
    ):
        evidence_key = item.get(
            "evidence_key"
        )

        # ---------------------------------------------
        # Only expose evidence relevant to LLM RCA
        # reasoning.
        # ---------------------------------------------

        if (
            evidence_key
            not in LLM_RELEVANT_EVIDENCE_KEYS
        ):
            continue

        full_context = (
            item.get(
                "context"
            )
            or {}
        )

        allowed_fields = (
            LLM_CONTEXT_FIELDS.get(
                evidence_key,
                set(),
            )
        )

        # ---------------------------------------------
        # Keep only explicitly approved context fields.
        # ---------------------------------------------

        context_summary = {
            key: value
            for key, value
            in full_context.items()
            if key in allowed_fields
        }

        compact_evidence.append(
            {
                # -------------------------------------
                # Evidence identity
                # -------------------------------------

                "evidence_id":
                    item.get(
                        "evidence_id"
                    ),

                "evidence_key":
                    evidence_key,

                "category":
                    item.get(
                        "category"
                    ),

                # -------------------------------------
                # Observed value
                # -------------------------------------

                "value":
                    item.get(
                        "value"
                    ),

                # -------------------------------------
                # Causal metadata
                # -------------------------------------

                "supports_causes":
                    item.get(
                        "supports_causes"
                    )
                    or [],

                "contradicts_causes":
                    item.get(
                        "contradicts_causes"
                    )
                    or [],

                # -------------------------------------
                # Evidence quality
                # -------------------------------------

                "support_score":
                    item.get(
                        "support_score"
                    ),

                "reliability_score":
                    item.get(
                        "reliability_score"
                    ),

                "freshness_score":
                    item.get(
                        "freshness_score"
                    ),

                "specificity_score":
                    item.get(
                        "specificity_score"
                    ),

                # -------------------------------------
                # Evidence gate
                # -------------------------------------

                "gate_passed":
                    item.get(
                        "gate_passed"
                    ),

                # -------------------------------------
                # Decision-relevant context only
                # -------------------------------------

                "context":
                    context_summary,
            }
        )

    return {
        "schema_version":
            "RCA_LLM_EVIDENCE_PACKET_V1",

        "case_id":
            evidence_packet[
                "case_id"
            ],

        "evidence_count":
            len(
                compact_evidence
            ),

        "evidence":
            compact_evidence,

        # ---------------------------------------------
        # LLM reasoning contract
        # ---------------------------------------------

        "rules": [
            (
                "Use only supplied evidence."
            ),

            (
                "Never invent evidence IDs."
            ),

            (
                "Never invent measurements."
            ),

            (
                "Never invent timestamps."
            ),

            (
                "Never invent locations."
            ),

            (
                "Never invent network conditions."
            ),

            (
                "gate_passed=false evidence "
                "cannot support a cause."
            ),

            (
                "Every cited evidence ID must "
                "support the cited cause."
            ),

            (
                "Do not treat reasoning_summary "
                "as evidence."
            ),

            (
                "Use the observed value together "
                "with supports_causes and "
                "contradicts_causes."
            ),

            (
                "Prefer specific supported causes "
                "over vague domain-level causes."
            ),

            (
                "The deterministic RCA verifier "
                "has final authority."
            ),
        ],
    }