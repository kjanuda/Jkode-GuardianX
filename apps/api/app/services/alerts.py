
from datetime import (
    datetime,
    timezone,
)

from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert


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


def resolve_open_alerts(
    db: Session,
    device_id: int,
) -> int:
    now = datetime.now(
        timezone.utc
    )

    alerts = db.scalars(
        select(Alert).where(
            Alert.device_id == device_id,
            Alert.status == "OPEN",
        )
    ).all()

    for alert in alerts:
        alert.status = "RESOLVED"
        alert.resolved_at = now
        alert.last_seen_at = now

    if alerts:
        db.commit()

    return len(alerts)


def resolve_other_open_alerts(
    db: Session,
    device_id: int,
    keep_fingerprint: str,
) -> int:
    now = datetime.now(
        timezone.utc
    )

    alerts = db.scalars(
        select(Alert).where(
            Alert.device_id == device_id,
            Alert.status == "OPEN",
            Alert.fingerprint != keep_fingerprint,
        )
    ).all()

    for alert in alerts:
        alert.status = "RESOLVED"
        alert.resolved_at = now
        alert.last_seen_at = now

    if alerts:
        db.flush()

    return len(alerts)


def evaluate_alert(
    db: Session,
    device_id: int,
    risk: dict,
) -> dict:
    # -----------------------------------------
    # Healthy enough → resolve all open alerts
    # -----------------------------------------

    if not risk[
        "alert_required"
    ]:
        resolved_count = (
            resolve_open_alerts(
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

    # -----------------------------------------
    # Resolve stale OPEN incidents
    #
    # Keep only the current fingerprint OPEN.
    # Any other OPEN incident for this device
    # is considered stale.
    # -----------------------------------------

    resolved_old_incidents = (
        resolve_other_open_alerts(
            db=db,
            device_id=device_id,
            keep_fingerprint=fingerprint,
        )
    )

    now = datetime.now(
        timezone.utc
    )

    # -----------------------------------------
    # Dedup:
    # same device + same primary cause +
    # existing OPEN alert → update it
    # -----------------------------------------

    existing = db.scalar(
        select(Alert)
        .where(
            Alert.device_id == device_id,
            Alert.fingerprint == fingerprint,
            Alert.status == "OPEN",
        )
        .order_by(
            Alert.last_seen_at.desc()
        )
        .limit(1)
    )

    if existing is not None:
        existing.last_seen_at = now

        existing.occurrence_count += 1

        existing.severity = (
            risk[
                "risk_level"
            ]
        )

        existing.risk_score = (
            risk[
                "risk_score"
            ]
        )

        existing.title = (
            build_title(
                risk,
                primary_cause,
            )
        )

        existing.summary = (
            build_summary(
                risk
            )
        )

        db.commit()

        db.refresh(
            existing
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
                existing,
        }

    # -----------------------------------------
    # New incident
    # -----------------------------------------

    alert = Alert(
        device_id=device_id,

        fingerprint=fingerprint,

        status="OPEN",

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

        first_seen_at=now,
        last_seen_at=now,
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
