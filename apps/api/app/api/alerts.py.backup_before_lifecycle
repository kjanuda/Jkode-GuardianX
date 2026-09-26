
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.risk import (
    get_device_risk,
)

from app.db.session import get_db

from app.models import (
    Alert,
    Device,
)

from app.schemas.alert import (
    AlertEvaluationResult,
    AlertRead,
)

from app.schemas.dashboard import (
    DashboardAlertItem,
)

from app.services.alerts import (
    evaluate_alert,
)


router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["Alerts"],
)


# =====================================================
# ACTIVE ALERTS
# =====================================================

@router.get(
    "/active",
    response_model=list[
        DashboardAlertItem
    ],
)
def get_active_alerts(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(
            Alert,
            Device.device_id,
        )
        .join(
            Device,
            Alert.device_id
            == Device.id,
        )
        .where(
            Alert.status == "OPEN"
        )
        .order_by(
            Alert.last_seen_at.desc()
        )
        .limit(limit)
    ).all()

    return [
        {
            "id": alert.id,

            "device_id":
                external_device_id,

            "status":
                alert.status,

            "severity":
                alert.severity,

            "risk_score":
                alert.risk_score,

            "primary_cause":
                alert.primary_cause,

            "title":
                alert.title,

            "occurrence_count":
                alert.occurrence_count,

            "first_seen_at":
                alert.first_seen_at,

            "last_seen_at":
                alert.last_seen_at,

            "resolved_at":
                alert.resolved_at,
        }
        for (
            alert,
            external_device_id,
        ) in rows
    ]


# =====================================================
# ALERT HISTORY
# =====================================================

@router.get(
    "/history",
    response_model=list[
        DashboardAlertItem
    ],
)
def get_alert_history(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(
            Alert,
            Device.device_id,
        )
        .join(
            Device,
            Alert.device_id
            == Device.id,
        )
        .order_by(
            Alert.last_seen_at.desc()
        )
        .limit(limit)
    ).all()

    return [
        {
            "id": alert.id,

            "device_id":
                external_device_id,

            "status":
                alert.status,

            "severity":
                alert.severity,

            "risk_score":
                alert.risk_score,

            "primary_cause":
                alert.primary_cause,

            "title":
                alert.title,

            "occurrence_count":
                alert.occurrence_count,

            "first_seen_at":
                alert.first_seen_at,

            "last_seen_at":
                alert.last_seen_at,

            "resolved_at":
                alert.resolved_at,
        }
        for (
            alert,
            external_device_id,
        ) in rows
    ]


# =====================================================
# EVALUATE DEVICE ALERT
# =====================================================

@router.post(
    "/device/{device_external_id}/evaluate",
    response_model=AlertEvaluationResult,
)
def evaluate_device_alert(
    device_external_id: str,

    history_limit: int = Query(
        default=10,
        ge=2,
        le=100,
    ),

    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.device_id
            == device_external_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    risk = get_device_risk(
        device_external_id=(
            device_external_id
        ),
        history_limit=(
            history_limit
        ),
        db=db,
    )

    return evaluate_alert(
        db=db,
        device_id=device.id,
        risk=risk,
    )


# =====================================================
# DEVICE ALERTS
# =====================================================

@router.get(
    "/device/{device_external_id}",
    response_model=list[AlertRead],
)
def get_device_alerts(
    device_external_id: str,

    status: str | None = Query(
        default=None
    ),

    db: Session = Depends(get_db),
):
    device = db.scalar(
        select(Device).where(
            Device.device_id
            == device_external_id
        )
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    query = (
        select(Alert)
        .where(
            Alert.device_id
            == device.id
        )
        .order_by(
            Alert.last_seen_at.desc()
        )
    )

    if status is not None:
        query = query.where(
            Alert.status
            == status.upper()
        )

    return list(
        db.scalars(
            query
        ).all()
    )
