from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.actions.verification import (
    NOT_REQUIRED_NO_CHANGE,
    ROLLBACK_REQUIRED,
    ROLLBACK_REQUIRED_NOT_READY,
    ROLLBACK_STATE_UNKNOWN,
    verify_action_simulation,
)
from app.models.action import ActionPlan, utc_now
from app.models.action_simulation import ActionSimulation
from app.models.action_verification import ActionVerification


APPROVED_FOR_SIMULATION = "APPROVED_FOR_SIMULATION"
SIMULATED = "SIMULATED"
VERIFIED_SUCCESS = "VERIFIED_SUCCESS"
VERIFIED_FAILED = "VERIFIED_FAILED"
ROLLBACK_REQUIRED_STATUS = "ROLLBACK_REQUIRED"


class ActionLifecycleError(ValueError):
    pass


def lifecycle_to_dict(
    *,
    plan: ActionPlan,
    changed: bool,
    reason: str,
    simulation: ActionSimulation | None = None,
    verification: ActionVerification | None = None,
) -> dict[str, Any]:
    return {
        "changed":
            changed,

        "action_plan_id":
            plan.id,

        "status":
            plan.status,

        "reason":
            reason,

        "simulation_id":
            (
                simulation.id
                if simulation
                else None
            ),

        "simulation_status":
            (
                simulation.status
                if simulation
                else None
            ),

        "verification_id":
            (
                verification.id
                if verification
                else None
            ),

        "verification_status":
            (
                verification.status
                if verification
                else None
            ),

        "rollback_decision":
            (
                verification.rollback_decision
                if verification
                else None
            ),

        "execution_mode":
            plan.execution_mode,

        "auto_eligible":
            plan.auto_eligible,

        "status_updated_at":
            (
                plan.status_updated_at.isoformat()
                if plan.status_updated_at
                else None
            ),
    }


def latest_simulation(
    *,
    db: Session,
    plan_id: int,
) -> ActionSimulation | None:
    return db.scalar(
        select(
            ActionSimulation
        )
        .where(
            ActionSimulation.action_plan_id
            == plan_id
        )
        .order_by(
            ActionSimulation.attempt.desc(),
            ActionSimulation.id.desc(),
        )
        .limit(1)
    )


def set_plan_status(
    *,
    db: Session,
    plan: ActionPlan,
    new_status: str,
) -> bool:
    if plan.status == new_status:
        return False

    plan.status = new_status
    plan.status_updated_at = utc_now()

    # Guardian X V1 hard safety invariants.
    plan.execution_mode = "ADVISORY"
    plan.requires_human_approval = True
    plan.auto_eligible = False

    db.commit()
    db.refresh(plan)

    return True


def synchronize_action_lifecycle(
    *,
    db: Session,
    plan_id: int,
) -> dict[str, Any]:
    plan = db.get(
        ActionPlan,
        plan_id,
    )

    if plan is None:
        raise ActionLifecycleError(
            "Action plan not found"
        )

    simulation = latest_simulation(
        db=db,
        plan_id=plan.id,
    )

    if simulation is None:
        return lifecycle_to_dict(
            plan=plan,
            changed=False,
            reason="NO_SIMULATION_AVAILABLE",
        )

    # -------------------------------------------------
    # Failed or incomplete simulation -> fail closed.
    # -------------------------------------------------

    if simulation.status != "PASSED":
        changed = set_plan_status(
            db=db,
            plan=plan,
            new_status=VERIFIED_FAILED,
        )

        return lifecycle_to_dict(
            plan=plan,
            changed=changed,
            reason="SIMULATION_NOT_PASSED",
            simulation=simulation,
        )

    # Simulation passed, but verification may not yet
    # exist. This is an intermediate lifecycle state.
    verification = db.scalar(
        select(
            ActionVerification
        ).where(
            ActionVerification.simulation_id
            == simulation.id
        )
    )

    if verification is None:
        changed = set_plan_status(
            db=db,
            plan=plan,
            new_status=SIMULATED,
        )

        return lifecycle_to_dict(
            plan=plan,
            changed=changed,
            reason="AWAITING_VERIFICATION",
            simulation=simulation,
        )

    # Re-run verification entry point before trusting
    # an old VERIFIED result. This also checks the
    # source fingerprint for post-verification tamper.
    verify_action_simulation(
        db=db,
        simulation_id=simulation.id,
    )

    db.refresh(
        verification
    )

    # -------------------------------------------------
    # Verified safe dry-run with no real change.
    # -------------------------------------------------

    if (
        verification.status == "VERIFIED"
        and verification.rollback_decision
        == NOT_REQUIRED_NO_CHANGE
        and verification.execution_allowed
        is False
        and (
            verification.result_json
            or {}
        ).get(
            "integrity_valid"
        )
        is True
    ):
        changed = set_plan_status(
            db=db,
            plan=plan,
            new_status=VERIFIED_SUCCESS,
        )

        return lifecycle_to_dict(
            plan=plan,
            changed=changed,
            reason="VERIFICATION_SUCCESS_NO_REAL_CHANGE",
            simulation=simulation,
            verification=verification,
        )

    # -------------------------------------------------
    # Any real/possible change requiring rollback.
    # -------------------------------------------------

    if verification.rollback_decision in {
        ROLLBACK_REQUIRED,
        ROLLBACK_REQUIRED_NOT_READY,
        ROLLBACK_STATE_UNKNOWN,
    }:
        changed = set_plan_status(
            db=db,
            plan=plan,
            new_status=ROLLBACK_REQUIRED_STATUS,
        )

        return lifecycle_to_dict(
            plan=plan,
            changed=changed,
            reason="ROLLBACK_REVIEW_REQUIRED",
            simulation=simulation,
            verification=verification,
        )

    # -------------------------------------------------
    # Everything else fails closed.
    # -------------------------------------------------

    changed = set_plan_status(
        db=db,
        plan=plan,
        new_status=VERIFIED_FAILED,
    )

    return lifecycle_to_dict(
        plan=plan,
        changed=changed,
        reason="VERIFICATION_FAILED_OR_UNSAFE",
        simulation=simulation,
        verification=verification,
    )
