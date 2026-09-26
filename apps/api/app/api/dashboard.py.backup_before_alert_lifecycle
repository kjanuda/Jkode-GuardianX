from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import (
    distinct,
    func,
    select,
)

from sqlalchemy.orm import Session

from app.api.risk import (
    get_device_risk,
)

from app.db.session import (
    get_db,
)

from app.models import (
    Alert,
    Device,
    Telemetry,
)

from app.schemas.dashboard import (
    DashboardAlertItem,
    DashboardDeviceOverview,
    DashboardSummary,
)


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


# ----------------------------------------------------
# Dashboard summary
# ----------------------------------------------------


@router.get(
    "/summary",
    response_model=DashboardSummary,
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
):
    total_devices = (
        db.scalar(
            select(
                func.count(
                    Device.id
                )
            )
        )
        or 0
    )

    active_alerts = (
        db.scalar(
            select(
                func.count(
                    Alert.id
                )
            ).where(
                Alert.status == "OPEN"
            )
        )
        or 0
    )

    critical_alerts = (
        db.scalar(
            select(
                func.count(
                    Alert.id
                )
            ).where(
                Alert.status == "OPEN",
                Alert.severity
                == "CRITICAL",
            )
        )
        or 0
    )

    high_alerts = (
        db.scalar(
            select(
                func.count(
                    Alert.id
                )
            ).where(
                Alert.status == "OPEN",
                Alert.severity
                == "HIGH",
            )
        )
        or 0
    )

    devices_with_active_alerts = (
        db.scalar(
            select(
                func.count(
                    distinct(
                        Alert.device_id
                    )
                )
            ).where(
                Alert.status == "OPEN"
            )
        )
        or 0
    )

    latest_rows = db.execute(
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
        .limit(10)
    ).all()

    latest_incidents = [
        {
            "id":
                alert.id,

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
        ) in latest_rows
    ]

    return {
        "total_devices":
            total_devices,

        "active_alerts":
            active_alerts,

        "critical_alerts":
            critical_alerts,

        "high_alerts":
            high_alerts,

        "devices_with_active_alerts":
            devices_with_active_alerts,

        "latest_incidents":
            latest_incidents,
    }


# ----------------------------------------------------
# Per-device dashboard overview
# ----------------------------------------------------


@router.get(
    "/device/{device_external_id}",
    response_model=DashboardDeviceOverview,
)
def get_dashboard_device(
    device_external_id: str,
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

    latest = db.scalar(
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device.id
        )
        .order_by(
            Telemetry.timestamp.desc(),
            Telemetry.id.desc(),
        )
        .limit(1)
    )

    if latest is None:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found",
        )

    risk = get_device_risk(
        device_external_id=(
            device_external_id
        ),
        history_limit=10,
        db=db,
    )

    active_alert_count = (
        db.scalar(
            select(
                func.count(
                    Alert.id
                )
            ).where(
                Alert.device_id
                == device.id,

                Alert.status
                == "OPEN",
            )
        )
        or 0
    )

    causes = risk.get(
        "likely_causes",
        [],
    )

    primary_cause = (
        causes[0]
        if causes
        else "UNKNOWN"
    )

    return {
        "device_id":
            device.device_id,

        "latest_telemetry_id":
            latest.id,

        "latest_timestamp":
            latest.timestamp,

        "scenario":
            latest.scenario,

        "risk_score":
            risk[
                "risk_score"
            ],

        "risk_level":
            risk[
                "risk_level"
            ],

        "current_radio_health":
            risk[
                "current_radio_health"
            ],

        "current_network_health":
            risk[
                "current_network_health"
            ],

        "historical_health_score":
            risk[
                "historical_health_score"
            ],

        "historical_health":
            risk[
                "historical_health"
            ],

        "historical_trend":
            risk[
                "historical_trend"
            ],

        "persistent_poor_state":
            risk[
                "persistent_poor_state"
            ],

        "geo_vulnerability_score":
            risk[
                "geo_vulnerability_score"
            ],

        "geo_vulnerability_level":
            risk[
                "geo_vulnerability_level"
            ],

        "environmental_vulnerability_score":
            risk[
                "environmental_vulnerability_score"
            ],

        "environmental_vulnerability_level":
            risk[
                "environmental_vulnerability_level"
            ],

        "weather_context_score":
            risk[
                "weather_context_score"
            ],

        "weather_context_level":
            risk[
                "weather_context_level"
            ],

        "primary_cause":
            primary_cause,

        "alert_required":
            risk[
                "alert_required"
            ],

        "active_alert_count":
            active_alert_count,
    }