from datetime import (
    datetime,
    timezone,
)

from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert

from app.services.alert_lifecycle import (
    ACTIVE_ALERT_STATUSES,
    OPEN,
    REOPENED,
    RESOLVED,
    transition_alert,
)


def get_primary_cause(
    risk: dict,
) -> str:
    causes = risk.get(
        "likely_causes",
        [],
    )

    if causes:
        return causes[0]

    return "UNKNOWN"


def build_fingerprint(
    device_id: int,
    primary_cause: str,
) -> str:
    raw = (
        f"{device_id}:"
        f"{primary_cause}"
    )

    return sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()[:32]


def build_title(
    risk: dict,
    primary_cause: str,
) -> str:
    severity = risk[
        "risk_level"
    ]

    cause = primary_cause.replace(
        "_",
        " ",
    ).title()

    return (
        f"{severity} - {cause}"
    )


def build_summary(
    risk: dict,
) -> str:
    reasons = risk.get(
        "reasons",
        [],
    )

    if not reasons:
        return (
            "Guardian X detected "
            "a service-risk condition."
        )

    return "; ".join(
        reasons[:4]
    )


def update_alert_from_risk(
    alert: Alert,
    risk: dict,
    primary_cause: str,
    now: datetime,
) -> None:
    alert.last_seen_at = now

    alert.occurrence_count += 1

    alert.severity = risk[
        "risk_level"
    ]

    alert.risk_score = risk[
        "risk_score"
    ]

    alert.primary_cause = (
        primary_cause
    )

    alert.title = build_title(
        risk,
        primary_cause,
    )

    alert.summary = build_summary(
        risk
    )


def resolve_active_alerts(
    db: Session,
    device_id: int,
) -> int:
    now = datetime.now(
        timezone.utc
    )

    alerts = db.scalars(
        select(Alert).where(
            Alert.device_id
            == device_id,

            Alert.status.in_(
                ACTIVE_ALERT_STATUSES
            ),
        )
    ).all()

    for alert in alerts:
        transition_alert(
            alert,
            RESOLVED,
            now=now,
        )

        # Preserve previous Guardian X
        # alert ordering behaviour.
        alert.last_seen_at = now

    if alerts:
        db.commit()

    return len(alerts)


def resolve_other_active_alerts(
    db: Session,
    device_id: int,
    keep_fingerprint: str,
) -> int:
    now = datetime.now(
        timezone.utc
    )

    alerts = db.scalars(
        select(Alert).where(
            Alert.device_id
            == device_id,

            Alert.status.in_(
                ACTIVE_ALERT_STATUSES
            ),

            Alert.fingerprint
            != keep_fingerprint,
        )
    ).all()

    for alert in alerts:
        transition_alert(
            alert,
            RESOLVED,
            now=now,
        )

        alert.last_seen_at = now

    if alerts:
        db.flush()

    return len(alerts)


def get_active_matching_alert(
    db: Session,
    device_id: int,
    fingerprint: str,
) -> Alert | None:
    return db.scalar(
        select(Alert)
        .where(
            Alert.device_id
            == device_id,

            Alert.fingerprint
            == fingerprint,

            Alert.status.in_(
                ACTIVE_ALERT_STATUSES
            ),
        )
        .order_by(
            Alert.last_seen_at.desc()
        )
        .limit(1)
    )


def get_resolved_matching_alert(
    db: Session,
    device_id: int,
    fingerprint: str,
) -> Alert | None:
    return db.scalar(
        select(Alert)
        .where(
            Alert.device_id
            == device_id,

            Alert.fingerprint
            == fingerprint,

            Alert.status
            == RESOLVED,
        )
        .order_by(
            Alert.last_seen_at.desc()
        )
        .limit(1)
    )


def evaluate_alert(
    db: Session,
    device_id: int,
    risk: dict,
) -> dict:
    # =====================================================
    # HEALTHY / RECOVERED
    # Resolve every active lifecycle state.
    # =====================================================

    if not risk[
        "alert_required"
    ]:
        resolved_count = (
            resolve_active_alerts(
                db=db,
                device_id=device_id,
            )
        )

        return {
            "action": (
                "RESOLVED"
                if resolved_count > 0
                else "NONE"
            ),

            "risk_score":
                risk[
                    "risk_score"
                ],

            "risk_level":
                risk[
                    "risk_level"
                ],

            "resolved_count":
                resolved_count,

            "alert":
                None,
        }

    primary_cause = (
        get_primary_cause(
            risk
        )
    )

    fingerprint = (
        build_fingerprint(
            device_id=device_id,
            primary_cause=primary_cause,
        )
    )

    # =====================================================
    # Resolve a different active incident on this device.
    # Keep only the current fingerprint active.
    # =====================================================

    resolved_old_incidents = (
        resolve_other_active_alerts(
            db=db,
            device_id=device_id,
            keep_fingerprint=fingerprint,
        )
    )

    now = datetime.now(
        timezone.utc
    )

    # =====================================================
    # SAME ACTIVE INCIDENT
    #
    # OPEN / ACKNOWLEDGED / MITIGATING / REOPENED
    # stays in its current workflow state.
    #
    # Repeated telemetry must NOT reset an operator's
    # ACKNOWLEDGED or MITIGATING state back to OPEN.
    # =====================================================

    existing_active = (
        get_active_matching_alert(
            db=db,
            device_id=device_id,
            fingerprint=fingerprint,
        )
    )

    if existing_active is not None:
        update_alert_from_risk(
            alert=existing_active,
            risk=risk,
            primary_cause=primary_cause,
            now=now,
        )

        db.commit()

        db.refresh(
            existing_active
        )

        return {
            "action":
                "UPDATED",

            "risk_score":
                risk[
                    "risk_score"
                ],

            "risk_level":
                risk[
                    "risk_level"
                ],

            "resolved_count":
                resolved_old_incidents,

            "alert":
                existing_active,
        }

    # =====================================================
    # REOPEN
    #
    # Same device + same fingerprint was previously
    # resolved and the fault has returned.
    #
    # Reuse the incident rather than creating a duplicate.
    # =====================================================

    resolved_existing = (
        get_resolved_matching_alert(
            db=db,
            device_id=device_id,
            fingerprint=fingerprint,
        )
    )

    if resolved_existing is not None:
        transition_alert(
            resolved_existing,
            REOPENED,
            now=now,
        )

        update_alert_from_risk(
            alert=resolved_existing,
            risk=risk,
            primary_cause=primary_cause,
            now=now,
        )

        db.commit()

        db.refresh(
            resolved_existing
        )

        return {
            "action":
                "REOPENED",

            "risk_score":
                risk[
                    "risk_score"
                ],

            "risk_level":
                risk[
                    "risk_level"
                ],

            "resolved_count":
                resolved_old_incidents,

            "alert":
                resolved_existing,
        }

    # =====================================================
    # BRAND NEW INCIDENT
    # =====================================================

    alert = Alert(
        device_id=device_id,

        fingerprint=fingerprint,

        status=OPEN,

        severity=risk[
            "risk_level"
        ],

        risk_score=risk[
            "risk_score"
        ],

        primary_cause=(
            primary_cause
        ),

        title=build_title(
            risk,
            primary_cause,
        ),

        summary=build_summary(
            risk
        ),

        occurrence_count=1,

        reopened_count=0,

        first_seen_at=now,
        last_seen_at=now,

        status_updated_at=now,
    )

    db.add(
        alert
    )

    db.commit()

    db.refresh(
        alert
    )

    return {
        "action":
            "CREATED",

        "risk_score":
            risk[
                "risk_score"
            ],

        "risk_level":
            risk[
                "risk_level"
            ],

        "resolved_count":
            resolved_old_incidents,

        "alert":
            alert,
    }
