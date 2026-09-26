from __future__ import annotations

from copy import deepcopy
from typing import Any


ACTION_CATALOG_VERSION = "ACTION_CATALOG_V1"


ACTION_CATALOG: dict[str, dict[str, Any]] = {

    # =================================================
    # NETWORK DOMAIN
    # =================================================

    "CONGESTION_OR_BACKHAUL": {
        "action_code":
            "REVIEW_CAPACITY_AND_TRAFFIC_STEERING",

        "action_type":
            "NETWORK_OPTIMIZATION",

        "title":
            "Review Capacity and Traffic Steering",

        "description": (
            "Review cell load, backhaul utilization, "
            "traffic distribution, and available "
            "capacity before proposing any network "
            "configuration change."
        ),

        "rationale": (
            "Verified congestion or backhaul evidence "
            "indicates that degraded service may be "
            "related to resource saturation or "
            "transport limitations."
        ),

        "risk_level":
            "MEDIUM",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Confirm congestion evidence is current",
            "Validate serving-cell and backhaul health",
            "Confirm no active outage explains the degradation",
        ],

        "safety_checks": {
            "redundancy_check_required": True,
            "capacity_check_required": True,
            "customer_impact_review_required": True,
        },

        "verification_plan": [
            "Compare affected-device ratio before and after intervention",
            "Verify download throughput improvement",
            "Verify latency and packet-loss recovery",
            "Confirm neighboring cells remain healthy",
        ],

        "rollback_plan": [
            "Restore previous traffic-steering policy",
            "Restore previous capacity-related configuration",
            "Re-run telemetry and RCA verification",
        ],
    },


    "INTERFERENCE": {
        "action_code":
            "INVESTIGATE_INTERFERENCE_SOURCE",

        "action_type":
            "RF_OPTIMIZATION",

        "title":
            "Investigate and Mitigate RF Interference",

        "description": (
            "Investigate RF interference indicators "
            "and identify the likely interfering source "
            "before considering RF optimization."
        ),

        "rationale": (
            "Verified interference evidence indicates "
            "radio degradation that may not be explained "
            "by coverage weakness alone."
        ),

        "risk_level":
            "MEDIUM",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Validate current SINR and RSRQ degradation",
            "Check neighboring-cell RF conditions",
            "Rule out active outage and congestion dominance",
        ],

        "safety_checks": {
            "rf_change_review_required": True,
            "neighbor_impact_check_required": True,
            "spectrum_validation_required": True,
        },

        "verification_plan": [
            "Verify SINR improvement",
            "Verify RSRQ improvement",
            "Confirm affected-device ratio decreases",
            "Confirm neighboring-cell KPIs do not regress",
        ],

        "rollback_plan": [
            "Restore previous RF configuration",
            "Re-check serving and neighboring cells",
            "Re-run deterministic RCA",
        ],
    },


    "OUTAGE": {
        "action_code":
            "ESCALATE_OUTAGE_RECOVERY",

        "action_type":
            "SERVICE_RECOVERY",

        "title":
            "Escalate Outage Recovery",

        "description": (
            "Escalate the verified service outage for "
            "controlled recovery and infrastructure "
            "health validation."
        ),

        "rationale": (
            "Verified outage evidence indicates loss "
            "or severe degradation of network service."
        ),

        "risk_level":
            "HIGH",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Confirm outage evidence is current",
            "Validate affected network scope",
            "Check redundancy and fallback availability",
        ],

        "safety_checks": {
            "redundancy_check_required": True,
            "dependency_check_required": True,
            "human_approval_required": True,
        },

        "verification_plan": [
            "Verify service restoration",
            "Verify device reconnect success",
            "Verify throughput and latency recovery",
            "Confirm no secondary outage is introduced",
        ],

        "rollback_plan": [
            "Return to previous known-good configuration where applicable",
            "Escalate to network operations if recovery fails",
            "Preserve incident evidence for further RCA",
        ],
    },


    "CELL_OR_NETWORK": {
        "action_code":
            "INVESTIGATE_CELL_OR_NETWORK",

        "action_type":
            "NETWORK_INVESTIGATION",

        "title":
            "Investigate Cell or Network Condition",

        "description": (
            "Perform additional network-layer checks "
            "before selecting a specific remediation."
        ),

        "rationale": (
            "The deterministic RCA identifies a network "
            "domain issue but does not yet support a "
            "more specific remediation path."
        ),

        "risk_level":
            "MEDIUM",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Collect current cell KPIs",
            "Check outage, congestion, and interference evidence",
        ],

        "safety_checks": {
            "additional_diagnosis_required": True,
            "configuration_change_allowed": False,
        },

        "verification_plan": [
            "Re-run evidence fusion",
            "Re-run hierarchical RCA",
            "Require a more specific verified cause",
        ],

        "rollback_plan": [
            "No configuration change should be executed at this stage",
        ],
    },


    # =================================================
    # DEVICE DOMAIN
    # =================================================

    "DEVICE_MODEL_OR_FIRMWARE": {
        "action_code":
            "ISOLATE_DEVICE_COHORT_AND_REVIEW_FIRMWARE",

        "action_type":
            "DEVICE_REMEDIATION",

        "title":
            "Review Device Model or Firmware Cohort",

        "description": (
            "Identify the affected device-model or "
            "firmware cohort and validate whether the "
            "issue is isolated to that population."
        ),

        "rationale": (
            "Verified device-specific evidence indicates "
            "that degradation is concentrated in a "
            "specific device or firmware cohort."
        ),

        "risk_level":
            "MEDIUM",

        "blast_radius":
            "DEVICE_GROUP",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Confirm healthy comparison devices exist",
            "Validate device-model concentration",
            "Verify network-wide degradation is absent",
        ],

        "safety_checks": {
            "device_cohort_validation_required": True,
            "mass_update_allowed": False,
            "human_approval_required": True,
        },

        "verification_plan": [
            "Compare affected cohort against healthy devices",
            "Verify radio and network KPIs after remediation",
            "Confirm unaffected device models remain stable",
        ],

        "rollback_plan": [
            "Restore previous known-good device configuration",
            "Stop cohort remediation if degradation increases",
        ],
    },


    # =================================================
    # PROPAGATION DOMAIN
    # =================================================

    "COVERAGE_OR_PROPAGATION": {
        "action_code":
            "REVIEW_COVERAGE_AND_RF_DESIGN",

        "action_type":
            "RF_ENGINEERING",

        "title":
            "Review Coverage and RF Design",

        "description": (
            "Review serving-cell coverage, propagation "
            "conditions, and RF design before proposing "
            "physical or configuration changes."
        ),

        "rationale": (
            "Verified coverage or propagation evidence "
            "indicates persistent RF weakness without "
            "sufficient evidence for a more specific "
            "terrain-related diagnosis."
        ),

        "risk_level":
            "MEDIUM",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Confirm persistent radio degradation",
            "Check serving and neighboring cell coverage",
            "Validate current geo evidence",
        ],

        "safety_checks": {
            "rf_engineering_review_required": True,
            "neighbor_impact_check_required": True,
            "physical_change_allowed": False,
        },

        "verification_plan": [
            "Verify RSRP and SINR improvement",
            "Verify affected-device ratio decreases",
            "Confirm neighboring-cell performance remains stable",
        ],

        "rollback_plan": [
            "Restore prior RF configuration if changed",
            "Re-run geographic and RF evidence analysis",
        ],
    },


    "TERRAIN_PROPAGATION_LIKELY": {
        "action_code":
            "REVIEW_TERRAIN_AWARE_COVERAGE",

        "action_type":
            "RF_ENGINEERING",

        "title":
            "Review Terrain-Aware Coverage",

        "description": (
            "Review terrain obstruction, line-of-sight, "
            "Fresnel clearance, and serving-cell design "
            "before selecting a coverage intervention."
        ),

        "rationale": (
            "Verified terrain-aware evidence indicates "
            "that propagation obstruction is a likely "
            "driver of persistent radio degradation."
        ),

        "risk_level":
            "MEDIUM",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Confirm terrain evidence passes quality gates",
            "Confirm current RF degradation remains present",
            "Validate serving-cell geometry",
        ],

        "safety_checks": {
            "terrain_evidence_required": True,
            "rf_engineering_review_required": True,
            "physical_change_allowed": False,
        },

        "verification_plan": [
            "Recalculate LOS and Fresnel metrics",
            "Verify RSRP and SINR after intervention",
            "Verify affected-device ratio improves",
            "Confirm neighboring coverage is not degraded",
        ],

        "rollback_plan": [
            "Restore previous RF settings if modified",
            "Re-run terrain-aware propagation analysis",
        ],
    },


    "VEGETATION_PROPAGATION_POSSIBLE": {
        "action_code":
            "REVIEW_ENVIRONMENTAL_PROPAGATION",

        "action_type":
            "RF_INVESTIGATION",

        "title":
            "Review Environmental Propagation Conditions",

        "description": (
            "Review environmental propagation evidence "
            "before considering any RF remediation."
        ),

        "rationale": (
            "Environmental evidence may contribute to "
            "propagation degradation but requires "
            "additional confirmation."
        ),

        "risk_level":
            "LOW",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Validate vegetation evidence freshness",
            "Confirm current RF degradation",
        ],

        "safety_checks": {
            "additional_evidence_required": True,
            "configuration_change_allowed": False,
        },

        "verification_plan": [
            "Re-check propagation evidence",
            "Compare current and historical RF performance",
        ],

        "rollback_plan": [
            "No automatic network change should be executed",
        ],
    },


    "WEATHER_STRESS_POSSIBLE": {
        "action_code":
            "MONITOR_WEATHER_AND_LINK_QUALITY",

        "action_type":
            "MONITORING",

        "title":
            "Monitor Weather and Link Quality",

        "description": (
            "Monitor current weather and RF/network "
            "conditions while preserving the distinction "
            "between correlation and verified causation."
        ),

        "rationale": (
            "Weather stress may contribute to degradation "
            "but should not independently trigger network "
            "configuration changes."
        ),

        "risk_level":
            "LOW",

        "blast_radius":
            "CELL",

        "preconditions": [
            "Confirm deterministic RCA remains VERIFIED",
            "Validate current weather evidence",
        ],

        "safety_checks": {
            "configuration_change_allowed": False,
            "monitoring_only": True,
        },

        "verification_plan": [
            "Track RF metrics as weather conditions change",
            "Re-run deterministic RCA when evidence changes",
        ],

        "rollback_plan": [
            "No network configuration change is performed",
        ],
    },


    # =================================================
    # FALLBACK
    # =================================================

    "UNKNOWN": {
        "action_code":
            "NO_AUTOMATED_REMEDIATION",

        "action_type":
            "HUMAN_INVESTIGATION",

        "title":
            "Human Investigation Required",

        "description": (
            "No specific remediation should be selected "
            "because the verified root cause is not "
            "sufficiently specific."
        ),

        "rationale": (
            "Guardian X does not have enough verified "
            "evidence to select a safe remediation path."
        ),

        "risk_level":
            "HIGH",

        "blast_radius":
            "UNKNOWN",

        "preconditions": [
            "Collect additional evidence",
            "Re-run deterministic RCA",
        ],

        "safety_checks": {
            "configuration_change_allowed": False,
            "human_review_required": True,
        },

        "verification_plan": [
            "Obtain a specific verified root cause",
        ],

        "rollback_plan": [
            "No automated action is permitted",
        ],
    },
}


def get_action_template(
    primary_cause: str,
) -> dict[str, Any]:
    cause = (
        primary_cause
        or "UNKNOWN"
    )

    template = ACTION_CATALOG.get(
        cause,
        ACTION_CATALOG["UNKNOWN"],
    )

    return deepcopy(
        template
    )
