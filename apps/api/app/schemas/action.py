from pydantic import BaseModel, Field


class ActionApprovalRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=120,
    )

    reason: str | None = Field(
        default=None,
        max_length=2000,
    )


class ActionRejectionRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=120,
    )

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )
