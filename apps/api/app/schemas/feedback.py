from typing import Literal

from pydantic import BaseModel, Field


DiagnosisAssessment = Literal[
    "CORRECT",
    "PARTIALLY_CORRECT",
    "INCORRECT",
    "UNKNOWN",
]

ActionAssessment = Literal[
    "USEFUL",
    "PARTIALLY_USEFUL",
    "NOT_USEFUL",
    "NOT_APPLICABLE",
]

ResolutionStatus = Literal[
    "RESOLVED",
    "PARTIALLY_RESOLVED",
    "NOT_RESOLVED",
    "NO_CHANGE_PERFORMED",
]


class FeedbackCreateRequest(BaseModel):
    reviewer: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )


class FeedbackUpdateRequest(BaseModel):
    reviewer: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    diagnosis_assessment: (
        DiagnosisAssessment | None
    ) = None

    action_assessment: (
        ActionAssessment | None
    ) = None

    resolution_status: (
        ResolutionStatus | None
    ) = None

    operator_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    actual_root_cause: str | None = Field(
        default=None,
        max_length=120,
    )

    actual_resolution: str | None = Field(
        default=None,
        max_length=4000,
    )

    notes: str | None = Field(
        default=None,
        max_length=4000,
    )
