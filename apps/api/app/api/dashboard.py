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


from app.services.alert_lifecycle import (
    ACTIVE_ALERT_STATUSES,
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
                Alert.status.in_(ACTIVE_ALERT_STATUSES)
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
                Alert.status.in_(ACTIVE_ALERT_STATUSES),
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
                Alert.status.in_(ACTIVE_ALERT_STATUSES),
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
                Alert.status.in_(ACTIVE_ALERT_STATUSES)
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

                Alert.status.in_(ACTIVE_ALERT_STATUSES),
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


# ====================================================
# STEP 38A DASHBOARD OVERVIEW V1
# ====================================================

from datetime import (
    datetime as _dashboard_datetime,
    timezone as _dashboard_timezone,
)

from sqlalchemy import (
    func as _dashboard_func,
    select as _dashboard_select,
)

from app.models.action import (
    ActionPlan as _DashboardActionPlan,
)

from app.models.action_feedback import (
    ActionFeedback as _DashboardActionFeedback,
)

from app.models.rca import (
    RCACase as _DashboardRCACase,
    RCAPrediction as _DashboardRCAPrediction,
)


_DASHBOARD_SCHEMA_VERSION = (
    "DASHBOARD_OVERVIEW_V1"
)


def _dashboard_count_by(
    db: Session,
    model,
    column,
) -> dict[str, int]:
    rows = db.execute(
        _dashboard_select(
            column,
            _dashboard_func.count(
                model.id
            ),
        )
        .group_by(
            column
        )
    ).all()

    result: dict[str, int] = {}

    for value, count in rows:
        key = (
            str(value)
            if value is not None
            else "UNKNOWN"
        )

        result[key] = int(
            count
            or 0
        )

    return result


@router.get(
    "/overview"
)
def get_dashboard_overview(
    db: Session = Depends(
        get_db
    ),
):
    # ------------------------------------------------
    # Reuse the already-tested dashboard summary.
    # ------------------------------------------------

    existing_summary = (
        get_dashboard_summary(
            db=db
        )
    )

    total_devices = int(
        existing_summary.get(
            "total_devices",
            0,
        )
        or 0
    )

    devices_with_active_alerts = int(
        existing_summary.get(
            "devices_with_active_alerts",
            0,
        )
        or 0
    )

    devices_without_active_alerts = max(
        0,
        total_devices
        - devices_with_active_alerts,
    )

    active_alert_ratio = (
        round(
            devices_with_active_alerts
            / total_devices,
            4,
        )
        if total_devices
        else 0.0
    )

    # ------------------------------------------------
    # Alerts
    # ------------------------------------------------

    alert_status_counts = (
        _dashboard_count_by(
            db,
            Alert,
            Alert.status,
        )
    )

    alert_severity_counts = (
        _dashboard_count_by(
            db,
            Alert,
            Alert.severity,
        )
    )

    total_alerts = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    Alert.id
                )
            )
        )
        or 0
    )

    # ------------------------------------------------
    # RCA
    # ------------------------------------------------

    total_rca_cases = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardRCACase.id
                )
            )
        )
        or 0
    )

    rca_status_counts = (
        _dashboard_count_by(
            db,
            _DashboardRCACase,
            _DashboardRCACase.status,
        )
    )

    prediction_engine_counts = (
        _dashboard_count_by(
            db,
            _DashboardRCAPrediction,
            _DashboardRCAPrediction.engine_type,
        )
    )

    verified_structured = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardRCAPrediction.id
                )
            )
            .where(
                _DashboardRCAPrediction.engine_type
                == "STRUCTURED_RCA_V1"
            )
            .where(
                _DashboardRCAPrediction.verifier_status
                == "VERIFIED"
            )
        )
        or 0
    )

    rejected_structured = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardRCAPrediction.id
                )
            )
            .where(
                _DashboardRCAPrediction.engine_type
                == "STRUCTURED_RCA_V1"
            )
            .where(
                _DashboardRCAPrediction.verifier_status
                == "REJECTED"
            )
        )
        or 0
    )

    # ------------------------------------------------
    # Actions
    # ------------------------------------------------

    total_action_plans = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardActionPlan.id
                )
            )
        )
        or 0
    )

    action_status_counts = (
        _dashboard_count_by(
            db,
            _DashboardActionPlan,
            _DashboardActionPlan.status,
        )
    )

    action_execution_modes = (
        _dashboard_count_by(
            db,
            _DashboardActionPlan,
            _DashboardActionPlan.execution_mode,
        )
    )

    auto_eligible_actions = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardActionPlan.id
                )
            )
            .where(
                _DashboardActionPlan.auto_eligible
                .is_(True)
            )
        )
        or 0
    )

    human_approval_actions = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardActionPlan.id
                )
            )
            .where(
                _DashboardActionPlan.requires_human_approval
                .is_(True)
            )
        )
        or 0
    )

    # ------------------------------------------------
    # Feedback
    # ------------------------------------------------

    total_feedback = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardActionFeedback.id
                )
            )
        )
        or 0
    )

    feedback_status_counts = (
        _dashboard_count_by(
            db,
            _DashboardActionFeedback,
            _DashboardActionFeedback.feedback_status,
        )
    )

    feedback_quality_counts = (
        _dashboard_count_by(
            db,
            _DashboardActionFeedback,
            _DashboardActionFeedback.quality_gate_status,
        )
    )

    training_eligible_feedback = int(
        db.scalar(
            _dashboard_select(
                _dashboard_func.count(
                    _DashboardActionFeedback.id
                )
            )
            .where(
                _DashboardActionFeedback.training_eligible
                .is_(True)
            )
        )
        or 0
    )

    # ------------------------------------------------
    # Safety snapshot
    #
    # This is descriptive state only.
    # It does NOT enable execution.
    # ------------------------------------------------

    safety = {
        "execution_mode":
            "ADVISORY",

        "real_network_execution_enabled":
            False,

        "auto_execution_enabled":
            False,

        "human_approval_required":
            True,

        "auto_eligible_action_count":
            auto_eligible_actions,

        "human_approval_action_count":
            human_approval_actions,
    }

    return {
        "schema_version":
            _DASHBOARD_SCHEMA_VERSION,

        "generated_at":
            _dashboard_datetime.now(
                _dashboard_timezone.utc
            ),

        "network":
            {
                "total_devices":
                    total_devices,

                "devices_with_active_alerts":
                    devices_with_active_alerts,

                "devices_without_active_alerts":
                    devices_without_active_alerts,

                "active_alert_device_ratio":
                    active_alert_ratio,
            },

        "alerts":
            {
                "total":
                    total_alerts,

                "active":
                    int(
                        existing_summary.get(
                            "active_alerts",
                            0,
                        )
                        or 0
                    ),

                "critical":
                    int(
                        existing_summary.get(
                            "critical_alerts",
                            0,
                        )
                        or 0
                    ),

                "high":
                    int(
                        existing_summary.get(
                            "high_alerts",
                            0,
                        )
                        or 0
                    ),

                "by_status":
                    alert_status_counts,

                "by_severity":
                    alert_severity_counts,
            },

        "rca":
            {
                "total_cases":
                    total_rca_cases,

                "by_status":
                    rca_status_counts,

                "predictions_by_engine":
                    prediction_engine_counts,

                "verified_structured_predictions":
                    verified_structured,

                "rejected_structured_predictions":
                    rejected_structured,
            },

        "actions":
            {
                "total":
                    total_action_plans,

                "by_status":
                    action_status_counts,

                "execution_modes":
                    action_execution_modes,

                "auto_eligible":
                    auto_eligible_actions,

                "requires_human_approval":
                    human_approval_actions,
            },

        "feedback":
            {
                "total":
                    total_feedback,

                "by_status":
                    feedback_status_counts,

                "quality_gates":
                    feedback_quality_counts,

                "training_eligible":
                    training_eligible_feedback,
            },

        "recent_incidents":
            existing_summary.get(
                "latest_incidents",
                [],
            ),

        "safety":
            safety,
    }


# ====================================================
# STEP 38A INCIDENT CHAIN V1
# ====================================================

from fastapi import (
    Query as _dashboard_Query,
)

from app.models.action_simulation import (
    ActionSimulation as _DashboardActionSimulation,
)

from app.models.action_verification import (
    ActionVerification as _DashboardActionVerification,
)


_DASHBOARD_INCIDENT_SCHEMA_VERSION = (
    "DASHBOARD_INCIDENT_CHAIN_V1"
)


@router.get(
    "/incidents"
)
def get_dashboard_incidents(
    limit: int = _dashboard_Query(
        default=25,
        ge=1,
        le=100,
    ),
    db: Session = Depends(
        get_db
    ),
):
    cases = list(
        db.scalars(
            _dashboard_select(
                _DashboardRCACase
            )
            .order_by(
                _DashboardRCACase.created_at.desc(),
                _DashboardRCACase.id.desc(),
            )
            .limit(
                limit
            )
        ).all()
    )

    items = []

    for case in cases:

        # --------------------------------------------
        # Alert
        # --------------------------------------------

        alert = None

        if case.alert_id is not None:
            alert = db.get(
                Alert,
                case.alert_id,
            )

        # --------------------------------------------
        # Device identity
        # --------------------------------------------

        device_internal_id = (
            case.device_id
        )

        if (
            device_internal_id is None
            and alert is not None
        ):
            device_internal_id = (
                alert.device_id
            )

        device = None

        if device_internal_id is not None:
            device = db.get(
                Device,
                device_internal_id,
            )

        external_device_id = (
            device.device_id
            if device is not None
            else None
        )

        # --------------------------------------------
        # Latest structured RCA
        # --------------------------------------------

        prediction = db.scalar(
            _dashboard_select(
                _DashboardRCAPrediction
            )
            .where(
                _DashboardRCAPrediction.case_id
                == case.id
            )
            .where(
                _DashboardRCAPrediction.engine_type
                == "STRUCTURED_RCA_V1"
            )
            .order_by(
                _DashboardRCAPrediction.created_at.desc(),
                _DashboardRCAPrediction.id.desc(),
            )
            .limit(
                1
            )
        )

        # --------------------------------------------
        # Latest action plan for this RCA case
        # --------------------------------------------

        action = db.scalar(
            _dashboard_select(
                _DashboardActionPlan
            )
            .where(
                _DashboardActionPlan.rca_case_id
                == case.id
            )
            .order_by(
                _DashboardActionPlan.id.desc()
            )
            .limit(
                1
            )
        )

        simulation = None
        verification = None
        feedback = None

        if action is not None:

            # ----------------------------------------
            # Latest simulation
            # ----------------------------------------

            simulation = db.scalar(
                _dashboard_select(
                    _DashboardActionSimulation
                )
                .where(
                    _DashboardActionSimulation.action_plan_id
                    == action.id
                )
                .order_by(
                    _DashboardActionSimulation.attempt.desc(),
                    _DashboardActionSimulation.id.desc(),
                )
                .limit(
                    1
                )
            )

            # ----------------------------------------
            # Verification bound to simulation
            # ----------------------------------------

            if simulation is not None:
                verification = db.scalar(
                    _dashboard_select(
                        _DashboardActionVerification
                    )
                    .where(
                        _DashboardActionVerification.simulation_id
                        == simulation.id
                    )
                    .order_by(
                        _DashboardActionVerification.id.desc()
                    )
                    .limit(
                        1
                    )
                )

            # ----------------------------------------
            # Latest operator feedback revision
            # ----------------------------------------

            feedback = db.scalar(
                _dashboard_select(
                    _DashboardActionFeedback
                )
                .where(
                    _DashboardActionFeedback.action_plan_id
                    == action.id
                )
                .order_by(
                    _DashboardActionFeedback.revision.desc(),
                    _DashboardActionFeedback.id.desc(),
                )
                .limit(
                    1
                )
            )

        # --------------------------------------------
        # Display cause / confidence
        # --------------------------------------------

        primary_cause = None
        confidence = None
        verifier_status = None

        if prediction is not None:
            primary_cause = (
                prediction.primary_cause
            )

            confidence = (
                prediction.confidence
            )

            verifier_status = (
                prediction.verifier_status
            )

        if (
            primary_cause is None
            and action is not None
        ):
            primary_cause = (
                action.source_primary_cause
            )

            confidence = (
                action.source_confidence
            )

            verifier_status = (
                action.source_verifier_status
            )

        if primary_cause is None:
            primary_cause = (
                case.baseline_primary_cause
                or "UNKNOWN"
            )

        # --------------------------------------------
        # Risk fallbacks
        # --------------------------------------------

        risk_score = (
            case.risk_score
        )

        risk_level = (
            case.risk_level
        )

        if (
            risk_score is None
            and alert is not None
        ):
            risk_score = (
                alert.risk_score
            )

        # --------------------------------------------
        # Incident lifecycle display status
        # --------------------------------------------

        incident_status = (
            alert.status
            if alert is not None
            else case.status
        )

        items.append(
            {
                "incident_id":
                    f"RCA-{case.id}",

                "case":
                    {
                        "id":
                            case.id,

                        "uuid":
                            case.case_uuid,

                        "status":
                            case.status,

                        "scope_type":
                            case.scope_type,

                        "scope_ref":
                            case.scope_ref,

                        "trigger_type":
                            case.trigger_type,

                        "created_at":
                            case.created_at,

                        "updated_at":
                            case.updated_at,
                    },

                "incident_status":
                    incident_status,

                "device":
                    {
                        "internal_id":
                            device_internal_id,

                        "external_id":
                            external_device_id,
                    },

                "risk":
                    {
                        "score":
                            risk_score,

                        "level":
                            risk_level,

                        "severity":
                            (
                                alert.severity
                                if alert is not None
                                else None
                            ),
                    },

                "alert":
                    (
                        {
                            "id":
                                alert.id,

                            "status":
                                alert.status,

                            "title":
                                alert.title,

                            "summary":
                                alert.summary,

                            "severity":
                                alert.severity,

                            "risk_score":
                                alert.risk_score,

                            "primary_cause":
                                alert.primary_cause,

                            "occurrence_count":
                                alert.occurrence_count,

                            "reopened_count":
                                alert.reopened_count,

                            "first_seen_at":
                                alert.first_seen_at,

                            "last_seen_at":
                                alert.last_seen_at,

                            "resolved_at":
                                alert.resolved_at,
                        }

                        if alert is not None
                        else None
                    ),

                "diagnosis":
                    {
                        "prediction_id":
                            (
                                prediction.id
                                if prediction is not None
                                else None
                            ),

                        "engine":
                            (
                                prediction.engine_type
                                if prediction is not None
                                else None
                            ),

                        "primary_cause":
                            primary_cause,

                        "confidence":
                            confidence,

                        "verifier_status":
                            verifier_status,

                        "verified":
                            (
                                verifier_status
                                == "VERIFIED"
                            ),
                    },

                "action":
                    (
                        {
                            "id":
                                action.id,

                            "uuid":
                                action.action_uuid,

                            "status":
                                action.status,

                            "action_code":
                                action.action_code,

                            "action_type":
                                action.action_type,

                            "title":
                                action.title,

                            "target_type":
                                action.target_type,

                            "target_ref":
                                action.target_ref,

                            "risk_level":
                                action.risk_level,

                            "blast_radius":
                                action.blast_radius,

                            "execution_mode":
                                action.execution_mode,

                            "safety_gate_status":
                                action.safety_gate_status,

                            "requires_human_approval":
                                action.requires_human_approval,

                            "auto_eligible":
                                action.auto_eligible,

                            "reviewed_by":
                                action.reviewed_by,

                            "reviewed_at":
                                action.reviewed_at,
                        }

                        if action is not None
                        else None
                    ),

                "simulation":
                    (
                        {
                            "id":
                                simulation.id,

                            "attempt":
                                simulation.attempt,

                            "status":
                                simulation.status,

                            "mode":
                                simulation.simulation_mode,

                            "verification_ready":
                                simulation.verification_ready,

                            "rollback_ready":
                                simulation.rollback_ready,

                            "execution_allowed":
                                simulation.execution_allowed,

                            "finished_at":
                                simulation.finished_at,
                        }

                        if simulation is not None
                        else None
                    ),

                "verification":
                    (
                        {
                            "id":
                                verification.id,

                            "status":
                                verification.status,

                            "verification_type":
                                verification.verification_type,

                            "rollback_decision":
                                verification.rollback_decision,

                            "execution_allowed":
                                verification.execution_allowed,

                            "verified_at":
                                verification.verified_at,
                        }

                        if verification is not None
                        else None
                    ),

                "feedback":
                    (
                        {
                            "id":
                                feedback.id,

                            "revision":
                                feedback.revision,

                            "status":
                                feedback.feedback_status,

                            "diagnosis_assessment":
                                feedback.diagnosis_assessment,

                            "action_assessment":
                                feedback.action_assessment,

                            "resolution_status":
                                feedback.resolution_status,

                            "operator_confidence":
                                feedback.operator_confidence,

                            "quality_gate_status":
                                feedback.quality_gate_status,

                            "training_eligible":
                                feedback.training_eligible,

                            "reviewer":
                                feedback.reviewer,
                        }

                        if feedback is not None
                        else None
                    ),

                "safety":
                    {
                        "real_execution_enabled":
                            False,

                        "execution_mode":
                            (
                                action.execution_mode
                                if action is not None
                                else "ADVISORY"
                            ),

                        "auto_eligible":
                            (
                                action.auto_eligible
                                if action is not None
                                else False
                            ),
                    },
            }
        )

    return {
        "schema_version":
            _DASHBOARD_INCIDENT_SCHEMA_VERSION,

        "generated_at":
            _dashboard_datetime.now(
                _dashboard_timezone.utc
            ),

        "count":
            len(
                items
            ),

        "limit":
            limit,

        "items":
            items,
    }


# ====================================================
# STEP 38A MAP PAYLOAD V1
# ====================================================

from app.models.cell import (
    Cell as _DashboardCell,
)

from app.models.sector import (
    Sector as _DashboardSector,
)

from app.models.tower import (
    Tower as _DashboardTower,
)

from app.models.telemetry import (
    Telemetry as _DashboardTelemetry,
)


_DASHBOARD_MAP_SCHEMA_VERSION = (
    "DASHBOARD_MAP_V1"
)


@router.get(
    "/map"
)
def get_dashboard_map(
    device_limit: int = _dashboard_Query(
        default=250,
        ge=1,
        le=1000,
    ),
    db: Session = Depends(
        get_db
    ),
):
    # ------------------------------------------------
    # Towers
    # ------------------------------------------------

    towers = list(
        db.scalars(
            _dashboard_select(
                _DashboardTower
            )
            .order_by(
                _DashboardTower.id.asc()
            )
        ).all()
    )

    tower_items = []

    for tower in towers:
        tower_items.append(
            {
                "id":
                    tower.id,

                "tower_code":
                    tower.tower_code,

                "name":
                    tower.name,

                "latitude":
                    tower.latitude,

                "longitude":
                    tower.longitude,

                "elevation_m":
                    tower.elevation_m,

                "status":
                    tower.status,

                "coordinate_source":
                    "TOWER_NATIVE",
            }
        )

    # ------------------------------------------------
    # Cells
    #
    # Cells have no native coordinates.
    # Location is derived:
    #
    # Cell -> Sector -> Tower
    # ------------------------------------------------

    cells = list(
        db.scalars(
            _dashboard_select(
                _DashboardCell
            )
            .order_by(
                _DashboardCell.id.asc()
            )
        ).all()
    )

    cell_items = []

    cell_lookup = {}

    for cell in cells:
        sector = db.get(
            _DashboardSector,
            cell.sector_id,
        )

        tower = None

        if sector is not None:
            tower = db.get(
                _DashboardTower,
                sector.tower_id,
            )

        # --------------------------------------------
        # Latest CELL-level RCA case
        # --------------------------------------------

        latest_case = db.scalar(
            _dashboard_select(
                _DashboardRCACase
            )
            .where(
                _DashboardRCACase.scope_type
                == "CELL"
            )
            .where(
                _DashboardRCACase.scope_ref
                == cell.cell_id
            )
            .order_by(
                _DashboardRCACase.created_at.desc(),
                _DashboardRCACase.id.desc(),
            )
            .limit(
                1
            )
        )

        prediction = None
        action = None

        if latest_case is not None:
            prediction = db.scalar(
                _dashboard_select(
                    _DashboardRCAPrediction
                )
                .where(
                    _DashboardRCAPrediction.case_id
                    == latest_case.id
                )
                .where(
                    _DashboardRCAPrediction.engine_type
                    == "STRUCTURED_RCA_V1"
                )
                .order_by(
                    _DashboardRCAPrediction.created_at.desc(),
                    _DashboardRCAPrediction.id.desc(),
                )
                .limit(
                    1
                )
            )

            action = db.scalar(
                _dashboard_select(
                    _DashboardActionPlan
                )
                .where(
                    _DashboardActionPlan.rca_case_id
                    == latest_case.id
                )
                .order_by(
                    _DashboardActionPlan.id.desc()
                )
                .limit(
                    1
                )
            )

        latitude = (
            tower.latitude
            if tower is not None
            else None
        )

        longitude = (
            tower.longitude
            if tower is not None
            else None
        )

        item = {
            "id":
                cell.id,

            "cell_id":
                cell.cell_id,

            "technology":
                cell.technology,

            "band":
                cell.band,

            "bandwidth_mhz":
                cell.bandwidth_mhz,

            "pci":
                cell.pci,

            "earfcn":
                cell.earfcn,

            "status":
                cell.status,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "coordinate_source":
                (
                    "TOWER_DERIVED"
                    if tower is not None
                    else "UNAVAILABLE"
                ),

            "sector":
                (
                    {
                        "id":
                            sector.id,

                        "sector_code":
                            sector.sector_code,

                        "azimuth_deg":
                            sector.azimuth_deg,

                        "electrical_tilt_deg":
                            sector.electrical_tilt_deg,

                        "mechanical_tilt_deg":
                            sector.mechanical_tilt_deg,

                        "status":
                            sector.status,
                    }

                    if sector is not None
                    else None
                ),

            "tower":
                (
                    {
                        "id":
                            tower.id,

                        "tower_code":
                            tower.tower_code,

                        "name":
                            tower.name,

                        "elevation_m":
                            tower.elevation_m,

                        "status":
                            tower.status,
                    }

                    if tower is not None
                    else None
                ),

            "rca":
                (
                    {
                        "case_id":
                            latest_case.id,

                        "case_status":
                            latest_case.status,

                        "primary_cause":
                            (
                                prediction.primary_cause
                                if prediction is not None
                                else latest_case.baseline_primary_cause
                            ),

                        "confidence":
                            (
                                prediction.confidence
                                if prediction is not None
                                else None
                            ),

                        "verifier_status":
                            (
                                prediction.verifier_status
                                if prediction is not None
                                else None
                            ),
                    }

                    if latest_case is not None
                    else None
                ),

            "action":
                (
                    {
                        "id":
                            action.id,

                        "status":
                            action.status,

                        "action_code":
                            action.action_code,

                        "risk_level":
                            action.risk_level,

                        "execution_mode":
                            action.execution_mode,

                        "auto_eligible":
                            action.auto_eligible,
                    }

                    if action is not None
                    else None
                ),
        }

        cell_items.append(
            item
        )

        cell_lookup[
            cell.id
        ] = item

    # ------------------------------------------------
    # Devices
    #
    # Device coordinates come from latest telemetry.
    # ------------------------------------------------

    devices = list(
        db.scalars(
            _dashboard_select(
                Device
            )
            .order_by(
                Device.id.asc()
            )
            .limit(
                device_limit
            )
        ).all()
    )

    device_items = []

    geolocated_device_count = 0

    active_device_alert_count = 0

    for device in devices:

        latest_telemetry = db.scalar(
            _dashboard_select(
                _DashboardTelemetry
            )
            .where(
                _DashboardTelemetry.device_id
                == device.id
            )
            .order_by(
                _DashboardTelemetry.timestamp.desc(),
                _DashboardTelemetry.id.desc(),
            )
            .limit(
                1
            )
        )

        latest_alert = db.scalar(
            _dashboard_select(
                Alert
            )
            .where(
                Alert.device_id
                == device.id
            )
            .where(
                Alert.status.in_(
                    ACTIVE_ALERT_STATUSES
                )
            )
            .order_by(
                Alert.last_seen_at.desc(),
                Alert.id.desc(),
            )
            .limit(
                1
            )
        )

        if latest_alert is not None:
            active_device_alert_count += 1

        latitude = (
            latest_telemetry.latitude
            if latest_telemetry is not None
            else None
        )

        longitude = (
            latest_telemetry.longitude
            if latest_telemetry is not None
            else None
        )

        if (
            latitude is not None
            and longitude is not None
        ):
            geolocated_device_count += 1

        serving_cell = None

        if device.current_cell_id is not None:
            serving_cell = cell_lookup.get(
                device.current_cell_id
            )

        device_items.append(
            {
                "id":
                    device.id,

                "device_id":
                    device.device_id,

                "status":
                    device.status,

                "model":
                    device.model,

                "manufacturer":
                    device.manufacturer,

                "software_version":
                    device.software_version,

                "antenna_type":
                    device.antenna_type,

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "coordinate_source":
                    (
                        "LATEST_TELEMETRY"
                        if (
                            latitude is not None
                            and longitude is not None
                        )
                        else "UNAVAILABLE"
                    ),

                "latest_telemetry":
                    (
                        {
                            "id":
                                latest_telemetry.id,

                            "timestamp":
                                latest_telemetry.timestamp,

                            "rsrp":
                                latest_telemetry.rsrp,

                            "rsrq":
                                latest_telemetry.rsrq,

                            "rssi":
                                latest_telemetry.rssi,

                            "sinr":
                                latest_telemetry.sinr,

                            "download_mbps":
                                latest_telemetry.download_mbps,

                            "upload_mbps":
                                latest_telemetry.upload_mbps,

                            "latency_ms":
                                latest_telemetry.latency_ms,

                            "packet_loss":
                                latest_telemetry.packet_loss,
                        }

                        if latest_telemetry is not None
                        else None
                    ),

                "serving_cell":
                    (
                        {
                            "id":
                                serving_cell[
                                    "id"
                                ],

                            "cell_id":
                                serving_cell[
                                    "cell_id"
                                ],

                            "technology":
                                serving_cell[
                                    "technology"
                                ],

                            "band":
                                serving_cell[
                                    "band"
                                ],
                        }

                        if serving_cell is not None
                        else None
                    ),

                "active_alert":
                    (
                        {
                            "id":
                                latest_alert.id,

                            "status":
                                latest_alert.status,

                            "severity":
                                latest_alert.severity,

                            "risk_score":
                                latest_alert.risk_score,

                            "primary_cause":
                                latest_alert.primary_cause,

                            "title":
                                latest_alert.title,
                        }

                        if latest_alert is not None
                        else None
                    ),

                "serving_cell_rca":
                    (
                        serving_cell[
                            "rca"
                        ]

                        if serving_cell is not None
                        else None
                    ),

                "serving_cell_action":
                    (
                        serving_cell[
                            "action"
                        ]

                        if serving_cell is not None
                        else None
                    ),

                "safety":
                    {
                        "real_execution_enabled":
                            False,

                        "auto_execution_enabled":
                            False,
                    },
            }
        )

    # ------------------------------------------------
    # Flat points collection for map libraries
    # ------------------------------------------------

    points = []

    for tower in tower_items:
        points.append(
            {
                "point_type":
                    "TOWER",

                "id":
                    tower[
                        "tower_code"
                    ],

                "latitude":
                    tower[
                        "latitude"
                    ],

                "longitude":
                    tower[
                        "longitude"
                    ],

                "status":
                    tower[
                        "status"
                    ],
            }
        )

    for cell in cell_items:
        if (
            cell[
                "latitude"
            ]
            is None
            or cell[
                "longitude"
            ]
            is None
        ):
            continue

        points.append(
            {
                "point_type":
                    "CELL",

                "id":
                    cell[
                        "cell_id"
                    ],

                "latitude":
                    cell[
                        "latitude"
                    ],

                "longitude":
                    cell[
                        "longitude"
                    ],

                "status":
                    cell[
                        "status"
                    ],

                "primary_cause":
                    (
                        cell[
                            "rca"
                        ][
                            "primary_cause"
                        ]

                        if cell[
                            "rca"
                        ]
                        else None
                    ),

                "action_status":
                    (
                        cell[
                            "action"
                        ][
                            "status"
                        ]

                        if cell[
                            "action"
                        ]
                        else None
                    ),
            }
        )

    for device in device_items:
        if (
            device[
                "latitude"
            ]
            is None
            or device[
                "longitude"
            ]
            is None
        ):
            continue

        points.append(
            {
                "point_type":
                    "DEVICE",

                "id":
                    device[
                        "device_id"
                    ],

                "latitude":
                    device[
                        "latitude"
                    ],

                "longitude":
                    device[
                        "longitude"
                    ],

                "status":
                    device[
                        "status"
                    ],

                "active_alert":
                    (
                        device[
                            "active_alert"
                        ]
                        is not None
                    ),

                "severity":
                    (
                        device[
                            "active_alert"
                        ][
                            "severity"
                        ]

                        if device[
                            "active_alert"
                        ]
                        else None
                    ),
            }
        )

    return {
        "schema_version":
            _DASHBOARD_MAP_SCHEMA_VERSION,

        "generated_at":
            _dashboard_datetime.now(
                _dashboard_timezone.utc
            ),

        "summary":
            {
                "tower_count":
                    len(
                        tower_items
                    ),

                "cell_count":
                    len(
                        cell_items
                    ),

                "device_count":
                    len(
                        device_items
                    ),

                "geolocated_device_count":
                    geolocated_device_count,

                "active_device_alert_count":
                    active_device_alert_count,

                "point_count":
                    len(
                        points
                    ),
            },

        "towers":
            tower_items,

        "cells":
            cell_items,

        "devices":
            device_items,

        "points":
            points,

        "safety":
            {
                "execution_mode":
                    "ADVISORY",

                "real_network_execution_enabled":
                    False,

                "auto_execution_enabled":
                    False,
            },
    }

