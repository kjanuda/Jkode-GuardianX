from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.feedback.candidates import (
    FeedbackCandidateError,
    build_feedback_candidate,
)
from app.feedback.quality import (
    ActionFeedbackQualityError,
    evaluate_feedback_quality,
)
from app.feedback.service import (
    ActionFeedbackError,
    create_feedback_revision,
    feedback_to_dict,
    submit_feedback,
    update_feedback_draft,
)
from app.models.action import ActionPlan
from app.models.action_feedback import (
    ActionFeedback,
)
from app.schemas.feedback import (
    FeedbackCreateRequest,
    FeedbackUpdateRequest,
)


router = APIRouter(
    prefix="/api/v1/feedback",
    tags=["Feedback"],
)


def raise_feedback_error(
    exc: Exception,
) -> None:
    message = str(
        exc
    )

    if (
        "not found"
        in message.lower()
    ):
        raise HTTPException(
            status_code=404,
            detail=message,
        ) from exc

    raise HTTPException(
        status_code=409,
        detail=message,
    ) from exc


@router.post(
    "/action/{action_plan_id}"
)
def create_action_feedback(
    action_plan_id: int,
    payload: FeedbackCreateRequest,
    db: Session = Depends(
        get_db
    ),
):
    try:
        return create_feedback_revision(
            db=db,
            action_plan_id=action_plan_id,
            reviewer=payload.reviewer,
        )

    except ActionFeedbackError as exc:
        raise_feedback_error(
            exc
        )


@router.get(
    "/action/{action_plan_id}"
)
def list_action_feedback(
    action_plan_id: int,
    db: Session = Depends(
        get_db
    ),
):
    plan = db.get(
        ActionPlan,
        action_plan_id,
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Action plan not found",
        )

    rows = list(
        db.scalars(
            select(
                ActionFeedback
            )
            .where(
                ActionFeedback.action_plan_id
                == action_plan_id
            )
            .order_by(
                ActionFeedback.revision.desc(),
                ActionFeedback.id.desc(),
            )
        ).all()
    )

    return {
        "action_plan_id":
            action_plan_id,

        "count":
            len(rows),

        "items": [
            feedback_to_dict(
                row
            )
            for row in rows
        ],
    }


@router.get(
    "/{feedback_id}"
)
def get_feedback(
    feedback_id: int,
    db: Session = Depends(
        get_db
    ),
):
    feedback = db.get(
        ActionFeedback,
        feedback_id,
    )

    if feedback is None:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found",
        )

    return feedback_to_dict(
        feedback
    )


@router.patch(
    "/{feedback_id}"
)
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdateRequest,
    db: Session = Depends(
        get_db
    ),
):
    updates = payload.model_dump(
        exclude_unset=True
    )

    try:
        return update_feedback_draft(
            db=db,
            feedback_id=feedback_id,
            updates=updates,
        )

    except ActionFeedbackError as exc:
        raise_feedback_error(
            exc
        )


@router.post(
    "/{feedback_id}/submit"
)
def submit_feedback_api(
    feedback_id: int,
    db: Session = Depends(
        get_db
    ),
):
    try:
        return submit_feedback(
            db=db,
            feedback_id=feedback_id,
        )

    except ActionFeedbackError as exc:
        raise_feedback_error(
            exc
        )


@router.post(
    "/{feedback_id}/quality"
)
def evaluate_feedback_quality_api(
    feedback_id: int,
    db: Session = Depends(
        get_db
    ),
):
    try:
        return evaluate_feedback_quality(
            db=db,
            feedback_id=feedback_id,
        )

    except ActionFeedbackQualityError as exc:
        raise_feedback_error(
            exc
        )


@router.post(
    "/{feedback_id}/candidate"
)
def build_feedback_candidate_api(
    feedback_id: int,
    db: Session = Depends(
        get_db
    ),
):
    try:
        return build_feedback_candidate(
            db=db,
            feedback_id=feedback_id,
        )

    except (
        FeedbackCandidateError,
        ActionFeedbackQualityError,
    ) as exc:
        raise_feedback_error(
            exc
        )
