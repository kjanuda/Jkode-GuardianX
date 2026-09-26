from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.actions.lifecycle import (
    ActionLifecycleError,
    synchronize_action_lifecycle,
)
from app.actions.planner import (
    ActionPlannerError,
    build_action_plan,
)
from app.actions.review import (
    ActionReviewError,
    apply_policy_review,
    approve_for_simulation,
    reject_action_plan,
)
from app.actions.simulator import (
    ActionSimulationError,
    run_action_simulation,
)
from app.actions.verification import (
    ActionVerificationError,
    verify_action_simulation,
)
from app.db.session import get_db
from app.models.action import ActionPlan
from app.models.action_simulation import (
    ActionSimulation,
)
from app.models.action_verification import (
    ActionVerification,
)
from app.schemas.action import (
    ActionApprovalRequest,
    ActionRejectionRequest,
)


router = APIRouter(
    prefix="/api/v1/actions",
    tags=["Actions"],
)


def action_plan_to_dict(
    plan: ActionPlan,
) -> dict[str, Any]:
    return {
        "id":
            plan.id,

        "action_uuid":
            plan.action_uuid,

        "rca_case_id":
            plan.rca_case_id,

        "alert_id":
            plan.alert_id,

        "device_id":
            plan.device_id,

        "source_primary_cause":
            plan.source_primary_cause,

        "source_confidence":
            plan.source_confidence,

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

        "title":
            plan.title,

        "description":
            plan.description,

        "rationale":
            plan.rationale,

        "status":
            plan.status,

        "execution_mode":
            plan.execution_mode,

        "safety_gate_status":
            plan.safety_gate_status,

        "requires_human_approval":
            plan.requires_human_approval,

        "auto_eligible":
            plan.auto_eligible,

        "risk_level":
            plan.risk_level,

        "blast_radius":
            plan.blast_radius,

        "verification_required":
            plan.verification_required,

        "rollback_required":
            plan.rollback_required,

        "parameters_json":
            plan.parameters_json,

        "preconditions_json":
            plan.preconditions_json,

        "safety_checks_json":
            plan.safety_checks_json,

        "verification_plan_json":
            plan.verification_plan_json,

        "rollback_plan_json":
            plan.rollback_plan_json,

        "reviewed_by":
            plan.reviewed_by,

        "review_reason":
            plan.review_reason,

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

        "rejected_at":
            (
                plan.rejected_at.isoformat()
                if plan.rejected_at
                else None
            ),

        "blocked_at":
            (
                plan.blocked_at.isoformat()
                if plan.blocked_at
                else None
            ),

        "status_updated_at":
            (
                plan.status_updated_at.isoformat()
                if plan.status_updated_at
                else None
            ),

        "planner_version":
            plan.planner_version,

        "schema_version":
            plan.schema_version,

        "created_at":
            (
                plan.created_at.isoformat()
                if plan.created_at
                else None
            ),

        "updated_at":
            (
                plan.updated_at.isoformat()
                if plan.updated_at
                else None
            ),
    }


def raise_service_error(
    exc: Exception,
) -> None:
    message = str(exc)

    if "not found" in message.lower():
        raise HTTPException(
            status_code=404,
            detail=message,
        ) from exc

    raise HTTPException(
        status_code=409,
        detail=message,
    ) from exc


@router.get(
    "/{plan_id}",
)
def get_action_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    plan = db.get(
        ActionPlan,
        plan_id,
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Action plan not found",
        )

    latest_simulation = db.scalar(
        select(
            ActionSimulation
        )
        .where(
            ActionSimulation.action_plan_id
            == plan.id
        )
        .order_by(
            ActionSimulation.attempt.desc(),
            ActionSimulation.id.desc(),
        )
        .limit(1)
    )

    latest_verification = None

    if latest_simulation is not None:
        latest_verification = db.scalar(
            select(
                ActionVerification
            ).where(
                ActionVerification.simulation_id
                == latest_simulation.id
            )
        )

    result = action_plan_to_dict(
        plan
    )

    result["latest_simulation"] = (
        {
            "id":
                latest_simulation.id,

            "attempt":
                latest_simulation.attempt,

            "status":
                latest_simulation.status,

            "simulation_mode":
                latest_simulation.simulation_mode,

            "verification_ready":
                latest_simulation.verification_ready,

            "rollback_ready":
                latest_simulation.rollback_ready,

            "execution_allowed":
                latest_simulation.execution_allowed,
        }
        if latest_simulation
        else None
    )

    result["latest_verification"] = (
        {
            "id":
                latest_verification.id,

            "status":
                latest_verification.status,

            "rollback_decision":
                latest_verification.rollback_decision,

            "execution_allowed":
                latest_verification.execution_allowed,

            "integrity_valid":
                (
                    latest_verification.result_json
                    or {}
                ).get(
                    "integrity_valid"
                ),
        }
        if latest_verification
        else None
    )

    return result


@router.post(
    "/plan/{case_id}",
)
def create_or_refresh_action_plan(
    case_id: int,
    db: Session = Depends(get_db),
):
    try:
        return build_action_plan(
            db=db,
            case_id=case_id,
        )

    except ActionPlannerError as exc:
        raise_service_error(
            exc
        )


@router.post(
    "/{plan_id}/policy-review",
)
def review_action_policy(
    plan_id: int,
    db: Session = Depends(get_db),
):
    try:
        return apply_policy_review(
            db=db,
            plan_id=plan_id,
        )

    except ActionReviewError as exc:
        raise_service_error(
            exc
        )


@router.post(
    "/{plan_id}/approve-simulation",
)
def approve_action_simulation(
    plan_id: int,
    payload: ActionApprovalRequest,
    db: Session = Depends(get_db),
):
    try:
        return approve_for_simulation(
            db=db,
            plan_id=plan_id,
            reviewer=payload.reviewer,
            reason=payload.reason,
        )

    except ActionReviewError as exc:
        raise_service_error(
            exc
        )


@router.post(
    "/{plan_id}/reject",
)
def reject_action(
    plan_id: int,
    payload: ActionRejectionRequest,
    db: Session = Depends(get_db),
):
    try:
        return reject_action_plan(
            db=db,
            plan_id=plan_id,
            reviewer=payload.reviewer,
            reason=payload.reason,
        )

    except ActionReviewError as exc:
        raise_service_error(
            exc
        )


@router.post(
    "/{plan_id}/simulate",
)
def simulate_action(
    plan_id: int,
    db: Session = Depends(get_db),
):
    try:
        return run_action_simulation(
            db=db,
            plan_id=plan_id,
        )

    except ActionSimulationError as exc:
        raise_service_error(
            exc
        )


@router.post(
    "/simulations/{simulation_id}/verify",
)
def verify_simulation(
    simulation_id: int,
    db: Session = Depends(get_db),
):
    try:
        return verify_action_simulation(
            db=db,
            simulation_id=simulation_id,
        )

    except ActionVerificationError as exc:
        raise_service_error(
            exc
        )


@router.post(
    "/{plan_id}/sync-lifecycle",
)
def sync_action_lifecycle(
    plan_id: int,
    db: Session = Depends(get_db),
):
    try:
        return synchronize_action_lifecycle(
            db=db,
            plan_id=plan_id,
        )

    except ActionLifecycleError as exc:
        raise_service_error(
            exc
        )
