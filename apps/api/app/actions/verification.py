from __future__ import annotations

import hashlib
import json

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.action import ActionPlan
from app.models.action_simulation import ActionSimulation
from app.models.action_verification import (
    ActionVerification,
    utc_now,
)


VERIFIER_VERSION = "ACTION_VERIFIER_V1"
SCHEMA_VERSION = "ACTION_VERIFICATION_V1"

FINGERPRINT_VERSION = (
    "ACTION_VERIFICATION_SOURCE_SHA256_V1"
)

VERIFIED = "VERIFIED"
FAILED = "FAILED"

NOT_REQUIRED_NO_CHANGE = (
    "NOT_REQUIRED_NO_CHANGE"
)

ROLLBACK_REQUIRED = (
    "ROLLBACK_REQUIRED"
)

ROLLBACK_REQUIRED_NOT_READY = (
    "ROLLBACK_REQUIRED_NOT_READY"
)

ROLLBACK_STATE_UNKNOWN = (
    "ROLLBACK_STATE_UNKNOWN"
)


class ActionVerificationError(ValueError):
    pass


def build_verification_source_snapshot(
    *,
    simulation: ActionSimulation,
    plan: ActionPlan,
) -> dict[str, Any]:
    return {
        "simulation": {
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

            "simulator_version":
                simulation.simulator_version,

            "schema_version":
                simulation.schema_version,

            "input_snapshot_json":
                simulation.input_snapshot_json
                or {},

            "checks_json":
                simulation.checks_json
                or {},

            "result_json":
                simulation.result_json
                or {},

            "failure_reasons_json":
                simulation.failure_reasons_json
                or [],

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
        },

        # Only safety-critical plan fields are sealed.
        # Lifecycle status is intentionally excluded,
        # because VERIFIED_SUCCESS etc. may legitimately
        # change after successful verification.
        "action_plan": {
            "id":
                plan.id,

            "action_uuid":
                plan.action_uuid,

            "source_primary_cause":
                plan.source_primary_cause,

            "source_verifier_status":
                plan.source_verifier_status,

            "action_code":
                plan.action_code,

            "execution_mode":
                plan.execution_mode,

            "safety_gate_status":
                plan.safety_gate_status,

            "requires_human_approval":
                plan.requires_human_approval,

            "auto_eligible":
                plan.auto_eligible,

            "reviewed_by":
                plan.reviewed_by,

            "reviewed_at":
                (
                    plan.reviewed_at.isoformat()
                    if plan.reviewed_at
                    else None
                ),

            "approved_for_simulation_at":
                (
                    plan.approved_for_simulation_at.isoformat()
                    if plan.approved_for_simulation_at
                    else None
                ),
        },
    }


def compute_verification_source_fingerprint(
    *,
    simulation: ActionSimulation,
    plan: ActionPlan,
) -> str:
    snapshot = build_verification_source_snapshot(
        simulation=simulation,
        plan=plan,
    )

    canonical = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def verification_to_dict(
    verification: ActionVerification,
    *,
    changed: bool,
) -> dict[str, Any]:
    return {
        "changed":
            changed,

        "id":
            verification.id,

        "verification_uuid":
            verification.verification_uuid,

        "simulation_id":
            verification.simulation_id,

        "status":
            verification.status,

        "verification_type":
            verification.verification_type,

        "checks_json":
            verification.checks_json,

        "result_json":
            verification.result_json,

        "failure_reasons_json":
            verification.failure_reasons_json,

        "rollback_decision":
            verification.rollback_decision,

        "execution_allowed":
            verification.execution_allowed,

        "verified_at":
            (
                verification.verified_at.isoformat()
                if verification.verified_at
                else None
            ),
    }


def determine_rollback_decision(
    simulation: ActionSimulation,
) -> str:
    result = (
        simulation.result_json
        or {}
    )

    real_change = result.get(
        "real_network_change_performed"
    )

    if real_change is False:
        return NOT_REQUIRED_NO_CHANGE

    if (
        real_change is True
        and simulation.rollback_ready
        is True
    ):
        return ROLLBACK_REQUIRED

    if (
        real_change is True
        and simulation.rollback_ready
        is not True
    ):
        return ROLLBACK_REQUIRED_NOT_READY

    return ROLLBACK_STATE_UNKNOWN


def build_verification_checks(
    *,
    simulation: ActionSimulation,
    plan: ActionPlan,
) -> tuple[
    dict[str, bool],
    list[str],
]:
    failures: list[str] = []

    result = (
        simulation.result_json
        or {}
    )

    simulation_checks = (
        simulation.checks_json
        or {}
    )

    snapshot = (
        simulation.input_snapshot_json
        or {}
    )

    checks = {
        "simulation_passed":
            simulation.status
            == "PASSED",

        "dry_run_mode":
            simulation.simulation_mode
            == "DRY_RUN",

        "simulation_finished":
            (
                simulation.started_at
                is not None
                and simulation.finished_at
                is not None
            ),

        "simulation_failure_list_empty":
            (
                simulation.failure_reasons_json
                == []
            ),

        "simulation_checks_present":
            bool(
                simulation_checks
            ),

        "simulation_checks_all_passed":
            (
                bool(simulation_checks)
                and all(
                    value is True
                    for value
                    in simulation_checks.values()
                )
            ),

        "verification_ready":
            simulation.verification_ready
            is True,

        "rollback_ready":
            simulation.rollback_ready
            is True,

        "simulation_execution_disabled":
            simulation.execution_allowed
            is False,

        "result_simulation_passed":
            result.get(
                "simulation_passed"
            )
            is True,

        "result_verification_ready":
            result.get(
                "verification_ready"
            )
            is True,

        "result_rollback_ready":
            result.get(
                "rollback_ready"
            )
            is True,

        "result_execution_disabled":
            result.get(
                "execution_allowed"
            )
            is False,

        "no_real_network_change":
            result.get(
                "real_network_change_performed"
            )
            is False,

        "action_plan_binding":
            (
                simulation.action_plan_id
                == plan.id
                and snapshot.get(
                    "action_plan_id"
                )
                == plan.id
            ),

        "action_uuid_binding":
            snapshot.get(
                "action_uuid"
            )
            == plan.action_uuid,

        "plan_still_advisory":
            plan.execution_mode
            == "ADVISORY",

        "plan_auto_execution_disabled":
            plan.auto_eligible
            is False,

        "human_approval_invariant":
            plan.requires_human_approval
            is True,
    }

    reason_map = {
        "simulation_passed":
            "SIMULATION_NOT_PASSED",

        "dry_run_mode":
            "SIMULATION_NOT_DRY_RUN",

        "simulation_finished":
            "SIMULATION_NOT_FINISHED",

        "simulation_failure_list_empty":
            "SIMULATION_HAS_FAILURE_REASONS",

        "simulation_checks_present":
            "SIMULATION_CHECKS_MISSING",

        "simulation_checks_all_passed":
            "SIMULATION_CHECKS_NOT_ALL_PASSED",

        "verification_ready":
            "SIMULATION_NOT_VERIFICATION_READY",

        "rollback_ready":
            "ROLLBACK_PLAN_NOT_READY",

        "simulation_execution_disabled":
            "SIMULATION_EXECUTION_NOT_DISABLED",

        "result_simulation_passed":
            "SIMULATION_RESULT_NOT_PASSED",

        "result_verification_ready":
            "RESULT_NOT_VERIFICATION_READY",

        "result_rollback_ready":
            "RESULT_ROLLBACK_NOT_READY",

        "result_execution_disabled":
            "RESULT_EXECUTION_NOT_DISABLED",

        "no_real_network_change":
            "REAL_NETWORK_CHANGE_DETECTED",

        "action_plan_binding":
            "ACTION_PLAN_BINDING_MISMATCH",

        "action_uuid_binding":
            "ACTION_UUID_BINDING_MISMATCH",

        "plan_still_advisory":
            "PLAN_NOT_ADVISORY",

        "plan_auto_execution_disabled":
            "PLAN_AUTO_EXECUTION_ENABLED",

        "human_approval_invariant":
            "HUMAN_APPROVAL_INVARIANT_FAILED",
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


def verify_action_simulation(
    *,
    db: Session,
    simulation_id: int,
) -> dict[str, Any]:
    simulation = db.get(
        ActionSimulation,
        simulation_id,
    )

    if simulation is None:
        raise ActionVerificationError(
            "Action simulation not found"
        )

    plan = db.get(
        ActionPlan,
        simulation.action_plan_id,
    )

    if plan is None:
        raise ActionVerificationError(
            "Action plan not found"
        )

    current_fingerprint = (
        compute_verification_source_fingerprint(
            simulation=simulation,
            plan=plan,
        )
    )

    existing = db.scalar(
        select(
            ActionVerification
        ).where(
            ActionVerification.simulation_id
            == simulation.id
        )
    )

    if existing is not None:
        existing_result = dict(
            existing.result_json
            or {}
        )

        stored_fingerprint = (
            existing_result.get(
                "source_fingerprint"
            )
        )

        # Existing V1 rows created before fingerprint
        # support are sealed once against their current
        # verified source state.
        if stored_fingerprint is None:
            existing_result[
                "source_fingerprint"
            ] = current_fingerprint

            existing_result[
                "fingerprint_version"
            ] = FINGERPRINT_VERSION

            existing_result[
                "integrity_valid"
            ] = True

            existing.result_json = (
                existing_result
            )

            try:
                db.commit()
                db.refresh(
                    existing
                )

            except Exception:
                db.rollback()
                raise

            return verification_to_dict(
                existing,
                changed=True,
            )

        if (
            stored_fingerprint
            != current_fingerprint
        ):
            reasons = list(
                existing.failure_reasons_json
                or []
            )

            reasons.append(
                "VERIFICATION_SOURCE_CHANGED_AFTER_VERIFICATION"
            )

            reasons = list(
                dict.fromkeys(
                    reasons
                )
            )

            existing.status = FAILED

            existing.failure_reasons_json = (
                reasons
            )

            existing.rollback_decision = (
                ROLLBACK_STATE_UNKNOWN
            )

            existing.execution_allowed = (
                False
            )

            existing_result[
                "verified"
            ] = False

            existing_result[
                "integrity_valid"
            ] = False

            existing_result[
                "current_source_fingerprint"
            ] = current_fingerprint

            existing_result[
                "execution_allowed"
            ] = False

            existing.result_json = (
                existing_result
            )

            existing.verified_at = (
                utc_now()
            )

            try:
                db.commit()
                db.refresh(
                    existing
                )

            except Exception:
                db.rollback()
                raise

            return verification_to_dict(
                existing,
                changed=True,
            )

        return verification_to_dict(
            existing,
            changed=False,
        )

    checks, failures = (
        build_verification_checks(
            simulation=simulation,
            plan=plan,
        )
    )

    rollback_decision = (
        determine_rollback_decision(
            simulation
        )
    )

    verified = (
        len(failures) == 0
        and rollback_decision
        == NOT_REQUIRED_NO_CHANGE
    )

    verification = ActionVerification(
        simulation_id=
            simulation.id,

        status=(
            VERIFIED
            if verified
            else FAILED
        ),

        verification_type=
            "SIMULATION_INTEGRITY",

        verifier_version=
            VERIFIER_VERSION,

        schema_version=
            SCHEMA_VERSION,

        checks_json=
            checks,

        result_json={
            "verified":
                verified,

            "source_fingerprint":
                current_fingerprint,

            "fingerprint_version":
                FINGERPRINT_VERSION,

            "integrity_valid":
                True,

            "simulation_status":
                simulation.status,

            "simulation_mode":
                simulation.simulation_mode,

            "rollback_decision":
                rollback_decision,

            "real_network_change_performed":
                (
                    simulation.result_json
                    or {}
                ).get(
                    "real_network_change_performed"
                ),

            "execution_allowed":
                False,
        },

        failure_reasons_json=
            failures,

        rollback_decision=
            rollback_decision,

        # Hard Guardian X V1 invariant.
        execution_allowed=False,

        notes=(
            "Deterministic verification of "
            "Guardian X dry-run simulation. "
            "Verification does not authorize "
            "real telecom execution."
        ),

        verified_at=
            utc_now(),
    )

    try:
        db.add(
            verification
        )

        db.commit()

        db.refresh(
            verification
        )

    except Exception:
        db.rollback()
        raise

    return verification_to_dict(
        verification,
        changed=True,
    )
