from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


class AgentQueryRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=1500,
    )

    case_id: int | None = Field(
        default=None,
        ge=1,
    )

    action_plan_id: int | None = Field(
        default=None,
        ge=1,
    )

    device_id: str | None = Field(
        default=None,
        max_length=120,
    )

    cell_id: str | None = Field(
        default=None,
        max_length=120,
    )


class AgentSource(BaseModel):
    source_type: str
    source_id: str
    label: str

    verified: bool | None = None


class AgentAuthority(BaseModel):
    read_only_agent: bool

    deterministic_rca_authoritative: bool

    llm_can_override_rca: bool

    llm_can_execute_actions: bool

    real_network_execution_enabled: bool

    auto_execution_enabled: bool


class AgentQueryResponse(BaseModel):
    schema_version: str

    answer: str

    provider: str
    model: str

    intent: str

    entities: dict[str, Any]

    sources: list[AgentSource]

    authority: AgentAuthority

    evidence_summary: dict[str, Any]
