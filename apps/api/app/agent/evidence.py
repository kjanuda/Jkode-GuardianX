from __future__ import annotations

import re
from typing import Any

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import Session

from app.models import (
    ActionPlan,
    Alert,
    Cell,
    Device,
    Telemetry,
)

from app.models.rca import (
    RCACase,
    RCAPrediction,
)

from app.rca.proposal_service import (
    get_case_evidence_packet,
)

from app.rca.rag_context import (
    build_compact_llm_packet,
)


ACTIVE_ALERT_STATUSES = (
    "OPEN",
    "ACKNOWLEDGED",
    "MITIGATING",
    "REOPENED",
)


def _iso(
    value: Any,
) -> str | None:
    if value is None:
        return None

    isoformat = getattr(
        value,
        "isoformat",
        None,
    )

    if callable(
        isoformat
    ):
        return isoformat()

    return str(
        value
    )


def _find_case_id(
    question: str,
) -> int | None:
    patterns = (
        r"\bRCA[-\s#:]*(\d+)\b",
        r"\bCASE[-\s#:]*(\d+)\b",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            question,
            re.IGNORECASE,
        )

        if match:
            return int(
                match.group(
                    1
                )
            )

    return None


def _find_action_plan_id(
    question: str,
) -> int | None:
    match = re.search(
        r"\b(?:PLAN|ACTION)[-\s#:]*(\d+)\b",
        question,
        re.IGNORECASE,
    )

    if not match:
        return None

    return int(
        match.group(
            1
        )
    )


def _find_cell_id(
    question: str,
) -> str | None:
    match = re.search(
        r"\bGX-CELL-[A-Z0-9-]+\b",
        question,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        match.group(
            0
        )
        .upper()
    )


def _find_device_id(
    question: str,
) -> str | None:
    match = re.search(
        r"\bGX-DEVICE-[A-Z0-9-]+\b",
        question,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        match.group(
            0
        )
        .upper()
    )


def _prediction_payload(
    prediction: RCAPrediction | None,
) -> dict | None:
    if prediction is None:
        return None

    return {
        "prediction_id":
            prediction.id,

        "engine_type":
            prediction.engine_type,

        "primary_cause":
            prediction.primary_cause,

        "confidence":
            (
                float(
                    prediction.confidence
                )
                if prediction.confidence
                is not None
                else None
            ),

        "rank":
            prediction.rank,

        "verifier_status":
            prediction.verifier_status,

        "verifier_reason":
            prediction.verifier_reason,

        "output":
            prediction.output_json
            or {},

        "created_at":
            _iso(
                prediction.created_at
            ),
    }


def _action_payload(
    action: ActionPlan | None,
) -> dict | None:
    if action is None:
        return None

    return {
        "id":
            action.id,

        "rca_case_id":
            action.rca_case_id,

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

        "status":
            action.status,

        "execution_mode":
            action.execution_mode,

        "safety_gate_status":
            action.safety_gate_status,

        "requires_human_approval":
            action.requires_human_approval,

        "auto_eligible":
            action.auto_eligible,

        "risk_level":
            action.risk_level,

        "blast_radius":
            action.blast_radius,

        "reviewed_by":
            action.reviewed_by,

        "reviewed_at":
            _iso(
                action.reviewed_at
            ),

        "safety_checks":
            action.safety_checks_json
            or {},

        "verification_required":
            action.verification_required,

        "rollback_required":
            action.rollback_required,
    }


def _alert_payload(
    alert: Alert | None,
    *,
    external_device_id: str | None,
) -> dict | None:
    if alert is None:
        return None

    return {
        "id":
            alert.id,

        "device_id":
            external_device_id,

        "status":
            alert.status,

        "severity":
            alert.severity,

        "risk_score":
            float(
                alert.risk_score
                or 0.0
            ),

        "primary_cause":
            alert.primary_cause,

        "title":
            alert.title,

        "occurrence_count":
            alert.occurrence_count,

        "first_seen_at":
            _iso(
                alert.first_seen_at
            ),

        "last_seen_at":
            _iso(
                alert.last_seen_at
            ),

        "resolved_at":
            _iso(
                alert.resolved_at
            ),
    }


def _telemetry_payload(
    telemetry: Telemetry | None,
) -> dict | None:
    if telemetry is None:
        return None

    fields = (
        "rsrp",
        "rsrq",
        "rssi",
        "sinr",
        "download_mbps",
        "upload_mbps",
        "latency_ms",
        "packet_loss",
        "latitude",
        "longitude",
    )

    result = {
        "timestamp":
            _iso(
                getattr(
                    telemetry,
                    "timestamp",
                    None,
                )
            ),
    }

    for field in fields:
        result[
            field
        ] = getattr(
            telemetry,
            field,
            None,
        )

    return result


def build_agent_evidence(
    *,
    db: Session,
    question: str,
    case_id: int | None = None,
    action_plan_id: int | None = None,
    device_id: str | None = None,
    cell_id: str | None = None,
) -> dict:
    # --------------------------------------------------
    # Explicit request fields win over question parsing.
    # --------------------------------------------------

    resolved_case_id = (
        case_id
        or _find_case_id(
            question
        )
    )

    resolved_action_id = (
        action_plan_id
        or _find_action_plan_id(
            question
        )
    )

    resolved_device_id = (
        device_id
        or _find_device_id(
            question
        )
    )

    resolved_cell_id = (
        cell_id
        or _find_cell_id(
            question
        )
    )

    action: ActionPlan | None = None
    case: RCACase | None = None
    device: Device | None = None
    cell: Cell | None = None
    latest_alert: Alert | None = None
    latest_telemetry: Telemetry | None = None

    # --------------------------------------------------
    # Action -> RCA relationship
    # --------------------------------------------------

    if resolved_action_id:
        action = db.get(
            ActionPlan,
            resolved_action_id,
        )

        if action is None:
            raise ValueError(
                (
                    "Action plan not found: "
                    f"{resolved_action_id}"
                )
            )

        resolved_case_id = (
            resolved_case_id
            or action.rca_case_id
        )

    # --------------------------------------------------
    # Device context
    # --------------------------------------------------

    if resolved_device_id:
        device = db.scalar(
            select(
                Device
            ).where(
                Device.device_id
                == resolved_device_id
            )
        )

        if device is None:
            raise ValueError(
                (
                    "Device not found: "
                    f"{resolved_device_id}"
                )
            )

        latest_alert = db.scalar(
            select(
                Alert
            )
            .where(
                Alert.device_id
                == device.id
            )
            .order_by(
                Alert.last_seen_at.desc()
            )
        )

        latest_telemetry = db.scalar(
            select(
                Telemetry
            )
            .where(
                Telemetry.device_id
                == device.id
            )
            .order_by(
                Telemetry.timestamp.desc()
            )
        )

        current_cell_id = getattr(
            device,
            "current_cell_id",
            None,
        )

        if (
            resolved_cell_id is None
            and current_cell_id
            is not None
        ):
            current_cell = db.get(
                Cell,
                current_cell_id,
            )

            if current_cell:
                resolved_cell_id = (
                    current_cell.cell_id
                )

    # --------------------------------------------------
    # Cell context
    # --------------------------------------------------

    if resolved_cell_id:
        cell = db.scalar(
            select(
                Cell
            ).where(
                Cell.cell_id
                == resolved_cell_id
            )
        )

        if cell is None:
            raise ValueError(
                (
                    "Cell not found: "
                    f"{resolved_cell_id}"
                )
            )

        if resolved_case_id is None:
            case = db.scalar(
                select(
                    RCACase
                )
                .where(
                    RCACase.scope_ref
                    == resolved_cell_id
                )
                .order_by(
                    RCACase.created_at.desc()
                )
            )

            if case:
                resolved_case_id = (
                    case.id
                )

    # --------------------------------------------------
    # RCA case
    # --------------------------------------------------

    if resolved_case_id:
        if case is None:
            case = db.get(
                RCACase,
                resolved_case_id,
            )

        if case is None:
            raise ValueError(
                (
                    "RCA case not found: "
                    f"{resolved_case_id}"
                )
            )

        if (
            resolved_cell_id is None
            and getattr(
                case,
                "scope_type",
                None,
            ) == "CELL"
        ):
            resolved_cell_id = getattr(
                case,
                "scope_ref",
                None,
            )

    # --------------------------------------------------
    # RCA predictions
    # --------------------------------------------------

    predictions: list[
        RCAPrediction
    ] = []

    if case:
        predictions = list(
            db.scalars(
                select(
                    RCAPrediction
                )
                .where(
                    RCAPrediction.case_id
                    == case.id
                )
                .order_by(
                    RCAPrediction.created_at.desc(),
                    RCAPrediction.id.desc(),
                )
            ).all()
        )

    structured = next(
        (
            item
            for item
            in predictions
            if item.engine_type
            == "STRUCTURED_RCA_V1"
        ),
        None,
    )

    consensus = next(
        (
            item
            for item
            in predictions
            if item.engine_type
            == "RCA_CONSENSUS_V1"
        ),
        None,
    )

    # --------------------------------------------------
    # RCA -> action
    # --------------------------------------------------

    if (
        action is None
        and case
    ):
        action = db.scalar(
            select(
                ActionPlan
            )
            .where(
                ActionPlan.rca_case_id
                == case.id
            )
            .order_by(
                ActionPlan.created_at.desc()
            )
        )

    # --------------------------------------------------
    # Compact canonical RCA evidence
    # --------------------------------------------------

    compact_evidence: list[
        dict[str, Any]
    ] = []

    if case:
        canonical = (
            get_case_evidence_packet(
                db=db,
                case_id=case.id,
            )
        )

        compact = (
            build_compact_llm_packet(
                evidence_packet=canonical,
            )
        )

        compact_evidence = list(
            compact.get(
                "evidence",
                [],
            )
        )

    # Keep the explanatory context bounded.
    compact_evidence = (
        compact_evidence[
            :30
        ]
    )

    # --------------------------------------------------
    # Network fallback: latest active alerts
    # --------------------------------------------------

    active_alert_rows = (
        db.execute(
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
                Alert.status.in_(
                    ACTIVE_ALERT_STATUSES
                )
            )
            .order_by(
                Alert.last_seen_at.desc()
            )
            .limit(
                5
            )
        )
        .all()
    )

    active_alerts = [
        _alert_payload(
            alert,
            external_device_id=(
                external_id
            ),
        )
        for (
            alert,
            external_id
        )
        in active_alert_rows
    ]

    # --------------------------------------------------
    # Server-controlled source references
    # --------------------------------------------------

    sources: list[
        dict[str, Any]
    ] = []

    if case:
        sources.append(
            {
                "source_type":
                    "RCA_CASE",

                "source_id":
                    f"RCA-{case.id}",

                "label":
                    "Guardian X RCA case",

                "verified":
                    None,
            }
        )

    if structured:
        sources.append(
            {
                "source_type":
                    "STRUCTURED_RCA",

                "source_id":
                    str(
                        structured.id
                    ),

                "label":
                    (
                        "Deterministic "
                        "structured RCA"
                    ),

                "verified":
                    (
                        structured.verifier_status
                        == "VERIFIED"
                    ),
            }
        )

    if consensus:
        sources.append(
            {
                "source_type":
                    "RCA_CONSENSUS",

                "source_id":
                    str(
                        consensus.id
                    ),

                "label":
                    "RCA consensus record",

                "verified":
                    (
                        consensus.verifier_status
                        == "AGREEMENT"
                    ),
            }
        )

    for item in compact_evidence:
        evidence_id = (
            item.get(
                "evidence_id"
            )
        )

        if evidence_id is None:
            continue

        sources.append(
            {
                "source_type":
                    "RCA_EVIDENCE",

                "source_id":
                    str(
                        evidence_id
                    ),

                "label":
                    (
                        item.get(
                            "evidence_key"
                        )
                        or "RCA evidence"
                    ),

                "verified":
                    bool(
                        item.get(
                            "gate_passed"
                        )
                    ),
            }
        )

    if action:
        sources.append(
            {
                "source_type":
                    "ACTION_PLAN",

                "source_id":
                    f"PLAN-{action.id}",

                "label":
                    "Guardian X action plan",

                "verified":
                    (
                        action.status
                        == "VERIFIED_SUCCESS"
                    ),
            }
        )

    if latest_alert:
        sources.append(
            {
                "source_type":
                    "ALERT",

                "source_id":
                    str(
                        latest_alert.id
                    ),

                "label":
                    "Device alert record",

                "verified":
                    None,
            }
        )

    # --------------------------------------------------
    # Final bounded evidence packet
    # --------------------------------------------------

    return {
        "schema_version":
            "GUARDIAN_AGENT_EVIDENCE_V1",

        "entities": {
            "case_id":
                (
                    case.id
                    if case
                    else None
                ),

            "action_plan_id":
                (
                    action.id
                    if action
                    else None
                ),

            "device_id":
                resolved_device_id,

            "cell_id":
                resolved_cell_id,
        },

        "rca_case": (
            {
                "id":
                    case.id,

                "status":
                    getattr(
                        case,
                        "status",
                        None,
                    ),

                "scope_type":
                    getattr(
                        case,
                        "scope_type",
                        None,
                    ),

                "scope_ref":
                    getattr(
                        case,
                        "scope_ref",
                        None,
                    ),

                "trigger_type":
                    getattr(
                        case,
                        "trigger_type",
                        None,
                    ),

                "risk_score":
                    getattr(
                        case,
                        "risk_score",
                        None,
                    ),

                "risk_level":
                    getattr(
                        case,
                        "risk_level",
                        None,
                    ),

                "created_at":
                    _iso(
                        getattr(
                            case,
                            "created_at",
                            None,
                        )
                    ),
            }
            if case
            else None
        ),

        "deterministic_rca":
            _prediction_payload(
                structured
            ),

        "consensus":
            _prediction_payload(
                consensus
            ),

        "action_plan":
            _action_payload(
                action
            ),

        "device": (
            {
                "device_id":
                    device.device_id,

                "status":
                    device.status,

                "model":
                    getattr(
                        device,
                        "model",
                        None,
                    ),

                "manufacturer":
                    getattr(
                        device,
                        "manufacturer",
                        None,
                    ),

                "latest_telemetry":
                    _telemetry_payload(
                        latest_telemetry
                    ),

                "latest_alert":
                    _alert_payload(
                        latest_alert,

                        external_device_id=(
                            device.device_id
                        ),
                    ),
            }
            if device
            else None
        ),

        "cell": (
            {
                "cell_id":
                    cell.cell_id,

                "technology":
                    cell.technology,

                "band":
                    getattr(
                        cell,
                        "band",
                        None,
                    ),

                "status":
                    cell.status,
            }
            if cell
            else None
        ),

        "rca_evidence":
            compact_evidence,

        "network_active_alerts":
            active_alerts,

        "sources":
            sources,

        "authority": {
            "read_only_agent":
                True,

            "deterministic_rca_authoritative":
                True,

            "llm_can_override_rca":
                False,

            "llm_can_execute_actions":
                False,

            "real_network_execution_enabled":
                False,

            "auto_execution_enabled":
                False,
        },
    }
