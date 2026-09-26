from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.agent.ollama import (
    AgentOllamaError,
)

from app.agent.service import (
    run_guardian_agent,
)

from app.db.session import (
    get_db,
)

from app.schemas.agent import (
    AgentQueryRequest,
    AgentQueryResponse,
)


router = APIRouter(
    prefix="/api/v1/agent",
    tags=["Agent"],
)


@router.post(
    "/query",
    response_model=AgentQueryResponse,
)
def query_guardian_agent(
    payload: AgentQueryRequest,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return run_guardian_agent(
            db=db,

            question=(
                payload.question
            ),

            case_id=(
                payload.case_id
            ),

            action_plan_id=(
                payload.action_plan_id
            ),

            device_id=(
                payload.device_id
            ),

            cell_id=(
                payload.cell_id
            ),
        )

    except ValueError as exc:
        message = str(
            exc
        )

        status_code = (
            404
            if "not found"
            in message.lower()
            else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc

    except AgentOllamaError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(
                exc
            ),
        ) from exc
