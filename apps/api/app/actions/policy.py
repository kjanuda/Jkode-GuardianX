from __future__ import annotations

from typing import Any

from app.models.action import ActionPlan


POLICY_VERSION = "ACTION_SAFETY_POLICY_V1"


BLOCKED_ACTION_CODES = {
    "NO_AUTOMATED_REMEDIATION",
}


def evaluate_action_policy(
    plan: ActionPlan,
) -> dict[str, Any]:
    reasons: list[str] = []

    checks = (
        plan.safety_checks_json
        or {}
    )

    params = (
        plan.parameters_json
        or {}
    )

    # ---------------------------------------------
    # Deterministic RCA authority
    # ---------------------------------------------

    if (
        plan.source_verifier_status
        != "VERIFIED"
    ):
        reasons.append(
            "DETERMINISTIC_RCA_NOT_VERIFIED"
        )

    if (
        checks.get(
            "deterministic_rca_verified"
        )
        is not True
    ):
        reasons.append(
            "DETERMINISTIC_VERIFICATION_FLAG_MISSING"
        )

    # ---------------------------------------------
    # Consensus / freshness gate
    # ---------------------------------------------

    if (
        plan.safety_gate_status
        != "ELIGIBLE_FOR_POLICY_REVIEW"
    ):
        reasons.append(
            "ACTION_NOT_ELIGIBLE_FOR_POLICY_REVIEW"
        )

    if (
        checks.get(
            "consensus_policy_review_eligible"
        )
        is not True
    ):
        reasons.append(
            "CONSENSUS_POLICY_GATE_NOT_PASSED"
        )

    if (
        params.get(
            "consensus_status"
        )
        != "AGREEMENT"
    ):
        reasons.append(
            "CONSENSUS_NOT_IN_AGREEMENT"
        )

    if (
        params.get(
            "consensus_action_gate"
        )
        != "ELIGIBLE_FOR_POLICY_REVIEW"
    ):
        reasons.append(
            "CONSENSUS_ACTION_GATE_BLOCKED"
        )

    # ---------------------------------------------
    # Explicit no-remediation actions
    # ---------------------------------------------

    if (
        plan.action_code
        in BLOCKED_ACTION_CODES
    ):
        reasons.append(
            "ACTION_CODE_NOT_REMEDIATION_ELIGIBLE"
        )

    # ---------------------------------------------
    # V1 execution safety invariants
    # ---------------------------------------------

    if plan.execution_mode != "ADVISORY":
        reasons.append(
            "UNSUPPORTED_EXECUTION_MODE"
        )

    if plan.requires_human_approval is not True:
        reasons.append(
            "HUMAN_APPROVAL_MUST_BE_REQUIRED"
        )

    if plan.auto_eligible is not False:
        reasons.append(
            "AUTO_EXECUTION_MUST_REMAIN_DISABLED"
        )

    if (
        checks.get(
            "execution_allowed"
        )
        is not False
    ):
        reasons.append(
            "EXECUTION_MUST_REMAIN_DISABLED"
        )

    if (
        checks.get(
            "auto_execution_allowed"
        )
        is not False
    ):
        reasons.append(
            "AUTO_EXECUTION_FLAG_MUST_BE_FALSE"
        )

    # ---------------------------------------------
    # Risk / blast-radius validation
    # ---------------------------------------------

    allowed_risk_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    if (
        plan.risk_level
        not in allowed_risk_levels
    ):
        reasons.append(
            "INVALID_OR_UNKNOWN_RISK_LEVEL"
        )

    allowed_blast_radius = {
        "DEVICE",
        "DEVICE_GROUP",
        "CELL",
    }

    if (
        plan.blast_radius
        not in allowed_blast_radius
    ):
        reasons.append(
            "UNSUPPORTED_BLAST_RADIUS"
        )

    # ---------------------------------------------
    # Final V1 decision
    # ---------------------------------------------

    reasons = list(
        dict.fromkeys(
            reasons
        )
    )

    if reasons:
        decision = "BLOCKED"
        review_required = False
        simulation_eligible = False

    else:
        decision = "REVIEW_REQUIRED"
        review_required = True

        # Human approval is required before this
        # can ever become simulation-eligible.
        simulation_eligible = False

    return {
        "policy_version":
            POLICY_VERSION,

        "action_plan_id":
            plan.id,

        "decision":
            decision,

        "reasons":
            reasons,

        "human_review_required":
            review_required,

        "simulation_eligible":
            simulation_eligible,

        "execution_allowed":
            False,

        "auto_execution_allowed":
            False,
    }
