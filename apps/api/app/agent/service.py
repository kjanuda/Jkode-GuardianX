from __future__ import annotations

from sqlalchemy.orm import Session

from app.agent.evidence import (
    build_agent_evidence,
)

from app.agent.ollama import (
    generate_agent_answer,
)

from app.agent.prompts import (
    SYSTEM_PROMPT,
    build_agent_user_prompt,
)


def _detect_intent(
    question: str,
) -> str:
    lowered = question.lower()

    if any(
        word in lowered
        for word in (
            "why",
            "root cause",
            "rca",
            "cause",
            "diagnosis",
        )
    ):
        return "EXPLAIN_RCA"

    if any(
        word in lowered
        for word in (
            "action",
            "fix",
            "mitigate",
            "simulation",
            "rollback",
        )
    ):
        return "EXPLAIN_ACTION"

    if any(
        word in lowered
        for word in (
            "alert",
            "incident",
            "critical",
        )
    ):
        return "EXPLAIN_ALERT"

    if any(
        word in lowered
        for word in (
            "signal",
            "rsrp",
            "rsrq",
            "sinr",
            "latency",
            "telemetry",
        )
    ):
        return "EXPLAIN_TELEMETRY"

    return "NETWORK_QUERY"


def _compact_prediction(
    value: dict | None,
) -> dict | None:
    if not value:
        return None

    output = (
        value.get("output")
        or {}
    )

    return {
        "prediction_id":
            value.get(
                "prediction_id"
            ),

        "engine_type":
            value.get(
                "engine_type"
            ),

        "primary_cause":
            value.get(
                "primary_cause"
            ),

        "confidence":
            value.get(
                "confidence"
            ),

        "verifier_status":
            value.get(
                "verifier_status"
            ),

        "verifier_reason":
            value.get(
                "verifier_reason"
            ),

        "domain":
            output.get(
                "domain"
            ),

        "contributors":
            output.get(
                "contributors"
            )
            or [],

        "verification_status":
            output.get(
                "verification_status"
            ),

        "consensus_status":
            output.get(
                "consensus_status"
            ),

        "action_gate":
            output.get(
                "action_gate"
            ),
    }


def _compact_action(
    value: dict | None,
) -> dict | None:
    if not value:
        return None

    safety = (
        value.get(
            "safety_checks"
        )
        or {}
    )

    return {
        "id":
            value.get("id"),

        "action_code":
            value.get(
                "action_code"
            ),

        "title":
            value.get(
                "title"
            ),

        "target_type":
            value.get(
                "target_type"
            ),

        "target_ref":
            value.get(
                "target_ref"
            ),

        "status":
            value.get(
                "status"
            ),

        "execution_mode":
            value.get(
                "execution_mode"
            ),

        "safety_gate_status":
            value.get(
                "safety_gate_status"
            ),

        "requires_human_approval":
            value.get(
                "requires_human_approval"
            ),

        "auto_eligible":
            value.get(
                "auto_eligible"
            ),

        "risk_level":
            value.get(
                "risk_level"
            ),

        "execution_allowed":
            safety.get(
                "execution_allowed"
            ),

        "physical_change_allowed":
            safety.get(
                "physical_change_allowed"
            ),

        "auto_execution_allowed":
            safety.get(
                "auto_execution_allowed"
            ),
    }


def _compact_rca_evidence(
    items: list[dict],
) -> list[dict]:
    compact: list[dict] = []

    for item in items[:8]:
        compact.append(
            {
                "evidence_id":
                    item.get(
                        "evidence_id"
                    ),

                "evidence_key":
                    item.get(
                        "evidence_key"
                    ),

                "category":
                    item.get(
                        "category"
                    ),

                "value":
                    item.get(
                        "value"
                    ),

                "supports_causes":
                    item.get(
                        "supports_causes"
                    )
                    or [],

                "contradicts_causes":
                    item.get(
                        "contradicts_causes"
                    )
                    or [],

                "support_score":
                    item.get(
                        "support_score"
                    ),

                "gate_passed":
                    item.get(
                        "gate_passed"
                    ),
            }
        )

    return compact


def _build_llm_evidence(
    evidence: dict,
) -> dict:
    return {
        "schema_version":
            "GUARDIAN_AGENT_LLM_CONTEXT_V1",

        "entities":
            evidence.get(
                "entities"
            )
            or {},

        "rca_case":
            evidence.get(
                "rca_case"
            ),

        "deterministic_rca":
            _compact_prediction(
                evidence.get(
                    "deterministic_rca"
                )
            ),

        "consensus":
            _compact_prediction(
                evidence.get(
                    "consensus"
                )
            ),

        "action_plan":
            _compact_action(
                evidence.get(
                    "action_plan"
                )
            ),

        "device":
            evidence.get(
                "device"
            ),

        "cell":
            evidence.get(
                "cell"
            ),

        "rca_evidence":
            _compact_rca_evidence(
                evidence.get(
                    "rca_evidence"
                )
                or []
            ),

        "authority":
            evidence.get(
                "authority"
            )
            or {},
    }


def run_guardian_agent(
    *,
    db: Session,
    question: str,
    case_id: int | None = None,
    action_plan_id: int | None = None,
    device_id: str | None = None,
    cell_id: str | None = None,
) -> dict:
    evidence = build_agent_evidence(
        db=db,
        question=question,
        case_id=case_id,
        action_plan_id=(
            action_plan_id
        ),
        device_id=device_id,
        cell_id=cell_id,
    )

    llm_evidence = (
        _build_llm_evidence(
            evidence
        )
    )

    user_prompt = (
        build_agent_user_prompt(
            question=question,
            evidence=llm_evidence,
        )
    )

    generated = (
        generate_agent_answer(
            system_prompt=(
                SYSTEM_PROMPT
            ),
            user_prompt=(
                user_prompt
            ),
        )
    )

    return {
        "schema_version":
            "GUARDIAN_AGENT_RESPONSE_V1",

        "answer":
            generated[
                "answer"
            ],

        "provider":
            generated[
                "provider"
            ],

        "model":
            generated[
                "model"
            ],

        "intent":
            _detect_intent(
                question
            ),

        "entities":
            evidence[
                "entities"
            ],

        "sources":
            evidence[
                "sources"
            ],

        "authority":
            evidence[
                "authority"
            ],

        "evidence_summary": {
            "rca_case_available":
                evidence[
                    "rca_case"
                ]
                is not None,

            "deterministic_rca_available":
                evidence[
                    "deterministic_rca"
                ]
                is not None,

            "consensus_available":
                evidence[
                    "consensus"
                ]
                is not None,

            "action_plan_available":
                evidence[
                    "action_plan"
                ]
                is not None,

            "device_context_available":
                evidence[
                    "device"
                ]
                is not None,

            "cell_context_available":
                evidence[
                    "cell"
                ]
                is not None,

            "rca_evidence_count":
                len(
                    evidence[
                        "rca_evidence"
                    ]
                ),

            "active_alert_count":
                len(
                    evidence[
                        "network_active_alerts"
                    ]
                ),
        },
    }
