from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.action import ActionPlan, utc_now
from app.models.action_simulation import ActionSimulation


SIMULATOR_VERSION = "ACTION_SIMULATOR_V1"
SIMULATION_SCHEMA_VERSION = "ACTION_SIMULATION_V1"

APPROVED_FOR_SIMULATION = "APPROVED_FOR_SIMULATION"

PASSED = "PASSED"
FAILED = "FAILED"


class ActionSimulationError(ValueError):
    pass


def simulation_to_dict(
    simulation: ActionSimulation,
) -> dict[str, Any]:
    return {
        "id":
            simulation.id,

        "simulation_uuid":
            simulation.simulation_uuid,

        "action_plan_id":
            simulation.action_plan_id,

        "attempt":
            simulation.attempt,

        "status":
            simulation.status,

        "simulation_mode":
            simulation.simulation_mode,

        "checks_json":
            simulation.checks_json,

        "result_json":
            simulation.result_json,

        "failure_reasons_json":
            simulation.failure_reasons_json,

        "verification_ready":
            simulation.verification_ready,

        "rollback_ready":
            simulation.rollback_ready,

        "execution_allowed":
            simulation.execution_allowed,

        "started_at":
            (
                simulation.started_at.isoformat()
                if simulation.started_at
                else None
            ),

        "finished_at":
            (
                simulation.finished_at.isoformat()
                if simulation.finished_at
                else None
            ),
    }


def next_attempt_number(
    *,
    db: Session,
    action_plan_id: int,
) -> int:
    current = db.scalar(
        select(
            func.max(
                ActionSimulation.attempt
            )
        ).where(
            ActionSimulation.action_plan_id
            == action_plan_id
        )
    )

    return int(
        current or 0
    ) + 1


def build_simulation_checks(
    plan: ActionPlan,
) -> tuple[
    dict[str, bool],
    list[str],
]:
    failures: list[str] = []

    parameters = (
        plan.parameters_json
        or {}
    )

    safety_checks = (
        plan.safety_checks_json
        or {}
    )

    preconditions = (
        plan.preconditions_json
        or []
    )

    verification_plan = (
        plan.verification_plan_json
        or []
    )

    rollback_plan = (
        plan.rollback_plan_json
        or []
    )

    checks = {
        "approved_for_simulation":
            (
                plan.status
                == APPROVED_FOR_SIMULATION
            ),

        "human_review_recorded":
            (
                bool(plan.reviewed_by)
                and plan.reviewed_at is not None
                and plan.approved_for_simulation_at
                is not None
            ),

        "deterministic_rca_verified":
            (
                plan.source_verifier_status
                == "VERIFIED"
                and safety_checks.get(
                    "deterministic_rca_verified"
                )
                is True
            ),

        "consensus_agreement":
            (
                parameters.get(
                    "consensus_status"
                )
                == "AGREEMENT"
            ),

        "consensus_policy_gate":
            (
                parameters.get(
                    "consensus_action_gate"
                )
                == "ELIGIBLE_FOR_POLICY_REVIEW"
                and safety_checks.get(
                    "consensus_policy_review_eligible"
                )
                is True
            ),

        "advisory_execution_mode":
            (
                plan.execution_mode
                == "ADVISORY"
            ),

        "auto_execution_disabled":
            (
                plan.auto_eligible
                is False
                and safety_checks.get(
                    "auto_execution_allowed"
                )
                is False
            ),

        "real_execution_disabled":
            (
                safety_checks.get(
                    "execution_allowed"
                )
                is False
            ),

        "human_approval_required":
            (
                plan.requires_human_approval
                is True
            ),

        "preconditions_defined":
            bool(
                preconditions
            ),

        "verification_plan_defined":
            (
                plan.verification_required
                is True
                and bool(
                    verification_plan
                )
            ),

        "rollback_plan_defined":
            (
                plan.rollback_required
                is True
                and bool(
                    rollback_plan
                )
            ),

        "action_is_specific":
            (
                bool(plan.action_code)
                and plan.action_code
                != "NO_AUTOMATED_REMEDIATION"
            ),
    }

    reason_map = {
        "approved_for_simulation":
            "ACTION_NOT_APPROVED_FOR_SIMULATION",

        "human_review_recorded":
            "HUMAN_REVIEW_AUDIT_MISSING",

        "deterministic_rca_verified":
            "DETERMINISTIC_RCA_NOT_VERIFIED",

        "consensus_agreement":
            "CONSENSUS_NOT_IN_AGREEMENT",

        "consensus_policy_gate":
            "CONSENSUS_POLICY_GATE_NOT_PASSED",

        "advisory_execution_mode":
            "UNSUPPORTED_EXECUTION_MODE",

        "auto_execution_disabled":
            "AUTO_EXECUTION_NOT_DISABLED",

        "real_execution_disabled":
            "REAL_EXECUTION_NOT_DISABLED",

        "human_approval_required":
            "HUMAN_APPROVAL_INVARIANT_FAILED",

        "preconditions_defined":
            "PRECONDITIONS_NOT_DEFINED",

        "verification_plan_defined":
            "VERIFICATION_PLAN_NOT_READY",

        "rollback_plan_defined":
            "ROLLBACK_PLAN_NOT_READY",

        "action_is_specific":
            "ACTION_NOT_SPECIFIC_ENOUGH",
    }

    for key, passed in checks.items():
        if not passed:
            failures.append(
                reason_map[key]
            )

    return (
        checks,
        failures,
    )


def run_action_simulation(
    *,
    db: Session,
    plan_id: int,
) -> dict[str, Any]:
    plan = db.get(
        ActionPlan,
        plan_id,
    )

    if plan is None:
        raise ActionSimulationError(
            "Action plan not found"
        )

    # Hard entry gate.
    # Blocked/rejected/review-only plans do not even
    # receive a simulation run.
    if (
        plan.status
        != APPROVED_FOR_SIMULATION
    ):
        raise ActionSimulationError(
            "Action plan must be "
            "APPROVED_FOR_SIMULATION"
        )

    attempt = next_attempt_number(
        db=db,
        action_plan_id=plan.id,
    )

    started_at = utc_now()

    simulation = ActionSimulation(
        action_plan_id=
            plan.id,

        attempt=
            attempt,

        status=
            "RUNNING",

        simulation_mode=
            "DRY_RUN",

        simulator_version=
            SIMULATOR_VERSION,

        schema_version=
            SIMULATION_SCHEMA_VERSION,

        input_snapshot_json={
            "action_plan_id":
                plan.id,

            "action_uuid":
                plan.action_uuid,

            "rca_case_id":
                plan.rca_case_id,

            "source_primary_cause":
                plan.source_primary_cause,

            "source_verifier_status":
                plan.source_verifier_status,

            "action_code":
                plan.action_code,

            "action_type":
                plan.action_type,

            "target_type":
                plan.target_type,

            "target_ref":
                plan.target_ref,

            "risk_level":
                plan.risk_level,

            "blast_radius":
                plan.blast_radius,

            "execution_mode":
                plan.execution_mode,

            "safety_gate_status":
                plan.safety_gate_status,

            "reviewed_by":
                plan.reviewed_by,

            "approved_for_simulation_at":
                (
                    plan.approved_for_simulation_at.isoformat()
                    if plan.approved_for_simulation_at
                    else None
                ),
        },

        checks_json={},

        result_json={
            "phase":
                "STARTED",

            "real_network_change_performed":
                False,
        },

        failure_reasons_json=[],

        verification_ready=False,

        rollback_ready=False,

        execution_allowed=False,

        notes=(
            "Guardian X V1 deterministic dry-run. "
            "No OSS, NMS, RAN, transport, device, "
            "or production configuration command "
            "was executed."
        ),

        started_at=
            started_at,
    )

    try:
        db.add(
            simulation
        )

        db.commit()

        db.refresh(
            simulation
        )

    except Exception:
        db.rollback()
        raise

    try:
        checks, failures = (
            build_simulation_checks(
                plan
            )
        )

        verification_ready = (
            checks[
                "verification_plan_defined"
            ]
        )

        rollback_ready = (
            checks[
                "rollback_plan_defined"
            ]
        )

        passed = (
            len(failures) == 0
        )

        simulation.status = (
            PASSED
            if passed
            else FAILED
        )

        simulation.checks_json = (
            checks
        )

        simulation.failure_reasons_json = (
            failures
        )

        simulation.verification_ready = (
            verification_ready
        )

        simulation.rollback_ready = (
            rollback_ready
        )

        # Critical V1 invariant:
        # even a successful dry-run never permits
        # real network execution.
        simulation.execution_allowed = (
            False
        )

        simulation.result_json = {
            "simulation_passed":
                passed,

            "verification_ready":
                verification_ready,

            "rollback_ready":
                rollback_ready,

            "real_network_change_performed":
                False,

            "execution_allowed":
                False,

            "message":
                (
                    "Dry-run safety simulation passed."
                    if passed
                    else
                    "Dry-run safety simulation failed."
                ),
        }

        simulation.finished_at = (
            utc_now()
        )

        db.commit()

        db.refresh(
            simulation
        )

    except Exception:
        db.rollback()
        raise

    return simulation_to_dict(
        simulation
    )
