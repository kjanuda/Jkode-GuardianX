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

from app.services.alert_lifecycle import (
    ACTIVE_ALERT_STATUSES,
    ACKNOWLEDGED,
    MITIGATING,
    REOPENED,
    RESOLVED,
    InvalidAlertTransition,
    transition_alert,
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
            Alert.status.in_(ACTIVE_ALERT_STATUSES)
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


# =====================================================
# ALERT LIFECYCLE TRANSITIONS
# =====================================================

def get_alert_or_404(
    alert_id: int,
    db: Session,
) -> Alert:
    alert = db.get(
        Alert,
        alert_id,
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


def apply_alert_transition(
    alert: Alert,
    target_status: str,
    db: Session,
) -> Alert:
    try:
        transition_alert(
            alert,
            target_status,
        )

        db.commit()

        db.refresh(
            alert
        )

        return alert

    except InvalidAlertTransition as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


# =====================================================
# ACKNOWLEDGE ALERT
# =====================================================

@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertRead,
)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = get_alert_or_404(
        alert_id,
        db,
    )

    return apply_alert_transition(
        alert,
        ACKNOWLEDGED,
        db,
    )


# =====================================================
# START ALERT MITIGATION
# =====================================================

@router.post(
    "/{alert_id}/mitigate",
    response_model=AlertRead,
)
def start_alert_mitigation(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = get_alert_or_404(
        alert_id,
        db,
    )

    return apply_alert_transition(
        alert,
        MITIGATING,
        db,
    )


# =====================================================
# RESOLVE ALERT
# =====================================================

@router.post(
    "/{alert_id}/resolve",
    response_model=AlertRead,
)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = get_alert_or_404(
        alert_id,
        db,
    )

    return apply_alert_transition(
        alert,
        RESOLVED,
        db,
    )


# =====================================================
# REOPEN ALERT
# =====================================================

@router.post(
    "/{alert_id}/reopen",
    response_model=AlertRead,
)
def reopen_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = get_alert_or_404(
        alert_id,
        db,
    )

    return apply_alert_transition(
        alert,
        REOPENED,
        db,
    )

