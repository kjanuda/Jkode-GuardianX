from datetime import (
    datetime,
    timezone,
)

from app.models.alert import Alert


# =====================================================
# ALERT STATUSES
# =====================================================

OPEN = "OPEN"
ACKNOWLEDGED = "ACKNOWLEDGED"
MITIGATING = "MITIGATING"
RESOLVED = "RESOLVED"
REOPENED = "REOPENED"


ACTIVE_ALERT_STATUSES = (
    OPEN,
    ACKNOWLEDGED,
    MITIGATING,
    REOPENED,
)


ALL_ALERT_STATUSES = (
    OPEN,
    ACKNOWLEDGED,
    MITIGATING,
    RESOLVED,
    REOPENED,
)


# =====================================================
# VALID STATE TRANSITIONS
# =====================================================

VALID_TRANSITIONS = {
    OPEN: {
        ACKNOWLEDGED,
        RESOLVED,
    },

    ACKNOWLEDGED: {
        MITIGATING,
        RESOLVED,
    },

    MITIGATING: {
        RESOLVED,
    },

    RESOLVED: {
        REOPENED,
    },

    REOPENED: {
        ACKNOWLEDGED,
        RESOLVED,
    },
}


class InvalidAlertTransition(
    ValueError
):
    pass


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def normalize_status(
    status: str,
) -> str:
    return status.strip().upper()


def is_active_status(
    status: str,
) -> bool:
    return (
        normalize_status(status)
        in ACTIVE_ALERT_STATUSES
    )


def can_transition(
    current_status: str,
    new_status: str,
) -> bool:
    current = normalize_status(
        current_status
    )

    target = normalize_status(
        new_status
    )

    if current == target:
        return True

    return target in VALID_TRANSITIONS.get(
        current,
        set(),
    )


def transition_alert(
    alert: Alert,
    new_status: str,
    now: datetime | None = None,
) -> Alert:
    current = normalize_status(
        alert.status
    )

    target = normalize_status(
        new_status
    )

    if current not in ALL_ALERT_STATUSES:
        raise InvalidAlertTransition(
            f"Unknown current alert status: "
            f"{current}"
        )

    if target not in ALL_ALERT_STATUSES:
        raise InvalidAlertTransition(
            f"Unknown target alert status: "
            f"{target}"
        )

    # Idempotent retry.
    if current == target:
        return alert

    if not can_transition(
        current,
        target,
    ):
        raise InvalidAlertTransition(
            f"Invalid alert transition: "
            f"{current} -> {target}"
        )

    timestamp = (
        now
        if now is not None
        else utc_now()
    )

    alert.status = target
    alert.status_updated_at = timestamp

    if target == ACKNOWLEDGED:
        alert.acknowledged_at = (
            timestamp
        )

    elif target == MITIGATING:
        alert.mitigation_started_at = (
            timestamp
        )

    elif target == RESOLVED:
        alert.resolved_at = (
            timestamp
        )

    elif target == REOPENED:
        alert.reopened_at = (
            timestamp
        )

        alert.reopened_count = (
            (alert.reopened_count or 0)
            + 1
        )

        # New lifecycle cycle.
        alert.resolved_at = None
        alert.acknowledged_at = None
        alert.mitigation_started_at = None

    return alert
