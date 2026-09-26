from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.actions.policy import evaluate_action_policy
from app.models.action import ActionPlan, utc_now


PROPOSED = "PROPOSED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
APPROVED_FOR_SIMULATION = "APPROVED_FOR_SIMULATION"
REJECTED = "REJECTED"
BLOCKED = "BLOCKED"

SIMULATED = "SIMULATED"
VERIFIED_SUCCESS = "VERIFIED_SUCCESS"
VERIFIED_FAILED = "VERIFIED_FAILED"
ROLLBACK_REQUIRED = "ROLLBACK_REQUIRED"

POST_REVIEW_STATES = {
    APPROVED_FOR_SIMULATION,
    REJECTED,
    SIMULATED,
    VERIFIED_SUCCESS,
    VERIFIED_FAILED,
    ROLLBACK_REQUIRED,
}


class ActionReviewError(ValueError):
    pass


def get_action_plan(
    *,
    db: Session,
    plan_id: int,
) -> ActionPlan:
    plan = db.get(
        ActionPlan,
        plan_id,
    )

    if plan is None:
        raise ActionReviewError(
            "Action plan not found"
        )

    return plan


def plan_review_to_dict(
    plan: ActionPlan,
    *,
    changed: bool,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "changed":
            changed,

        "id":
            plan.id,

        "rca_case_id":
            plan.rca_case_id,

        "status":
            plan.status,

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

        "review_reason":
            plan.review_reason,

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

        "policy":
            policy,
    }


def apply_policy_review(
    *,
    db: Session,
    plan_id: int,
) -> dict[str, Any]:
    plan = get_action_plan(
        db=db,
        plan_id=plan_id,
    )

    if plan.status in POST_REVIEW_STATES:
        raise ActionReviewError(
            f"Cannot re-evaluate post-review status: "
            f"{plan.status}"
        )

    policy = evaluate_action_policy(
        plan
    )

    decision = policy[
        "decision"
    ]

    if decision == "BLOCKED":
        new_status = BLOCKED

    elif decision == "REVIEW_REQUIRED":
        new_status = REVIEW_REQUIRED

    else:
        raise ActionReviewError(
            f"Unsupported policy decision: {decision}"
        )

    changed = (
        plan.status != new_status
    )

    if changed:
        now = utc_now()

        plan.status = (
            new_status
        )

        plan.status_updated_at = (
            now
        )

        if new_status == BLOCKED:
            plan.blocked_at = (
                now
            )

        else:
            # A previously policy-blocked plan can return
            # to review if fresh evidence later passes.
            plan.blocked_at = None

        try:
            db.commit()
            db.refresh(
                plan
            )

        except Exception:
            db.rollback()
            raise

    return plan_review_to_dict(
        plan,
        changed=changed,
        policy=policy,
    )


def approve_for_simulation(
    *,
    db: Session,
    plan_id: int,
    reviewer: str,
    reason: str | None = None,
) -> dict[str, Any]:
    reviewer = (
        reviewer
        or ""
    ).strip()

    if not reviewer:
        raise ActionReviewError(
            "Reviewer is required"
        )

    plan = get_action_plan(
        db=db,
        plan_id=plan_id,
    )

    # Safe retry / idempotency.
    if (
        plan.status
        == APPROVED_FOR_SIMULATION
    ):
        return plan_review_to_dict(
            plan,
            changed=False,
        )

    if plan.status != REVIEW_REQUIRED:
        raise ActionReviewError(
            "Action plan must be REVIEW_REQUIRED "
            "before simulation approval"
        )

    # Re-check policy at approval time.
    # Old approval eligibility must never be trusted.
    policy = evaluate_action_policy(
        plan
    )

    if (
        policy.get("decision")
        != "REVIEW_REQUIRED"
    ):
        raise ActionReviewError(
            "Action plan no longer passes safety policy"
        )

    now = utc_now()

    plan.status = (
        APPROVED_FOR_SIMULATION
    )

    plan.reviewed_by = (
        reviewer
    )

    plan.reviewed_at = (
        now
    )

    plan.review_reason = (
        reason.strip()
        if reason
        else None
    )

    plan.approved_for_simulation_at = (
        now
    )

    plan.rejected_at = None
    plan.blocked_at = None

    plan.status_updated_at = (
        now
    )

    # Hard V1 invariants.
    plan.execution_mode = (
        "ADVISORY"
    )

    plan.requires_human_approval = (
        True
    )

    plan.auto_eligible = (
        False
    )

    try:
        db.commit()
        db.refresh(
            plan
        )

    except Exception:
        db.rollback()
        raise

    return plan_review_to_dict(
        plan,
        changed=True,
        policy=policy,
    )


def reject_action_plan(
    *,
    db: Session,
    plan_id: int,
    reviewer: str,
    reason: str,
) -> dict[str, Any]:
    reviewer = (
        reviewer
        or ""
    ).strip()

    reason = (
        reason
        or ""
    ).strip()

    if not reviewer:
        raise ActionReviewError(
            "Reviewer is required"
        )

    if not reason:
        raise ActionReviewError(
            "Rejection reason is required"
        )

    plan = get_action_plan(
        db=db,
        plan_id=plan_id,
    )

    if plan.status == REJECTED:
        return plan_review_to_dict(
            plan,
            changed=False,
        )

    if plan.status != REVIEW_REQUIRED:
        raise ActionReviewError(
            "Only REVIEW_REQUIRED plans can be rejected"
        )

    now = utc_now()

    plan.status = (
        REJECTED
    )

    plan.reviewed_by = (
        reviewer
    )

    plan.reviewed_at = (
        now
    )

    plan.review_reason = (
        reason
    )

    plan.rejected_at = (
        now
    )

    plan.approved_for_simulation_at = None
    plan.blocked_at = None

    plan.status_updated_at = (
        now
    )

    try:
        db.commit()
        db.refresh(
            plan
        )

    except Exception:
        db.rollback()
        raise

    return plan_review_to_dict(
        plan,
        changed=True,
    )
