from datetime import datetime


from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class EvidenceRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    evidence_key: str

    source: str
    category: str
    metric: str

    value_json: dict

    unit: str | None

    supports_causes: list
    contradicts_causes: list

    support_score: float
    reliability_score: float
    freshness_score: float
    specificity_score: float

    gate_passed: bool | None

    observed_at: datetime | None

    context_json: dict


class PredictionRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    engine_type: str

    primary_cause: str | None
    confidence: float | None

    rank: int

    output_json: dict

    verifier_status: str | None
    verifier_reason: str | None

    created_at: datetime


class RCACaseSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    case_uuid: str

    scope_type: str
    scope_ref: str

    trigger_type: str
    status: str

    risk_score: float | None
    risk_level: str | None

    baseline_primary_cause: str | None

    created_at: datetime
    updated_at: datetime


class RCACaseDetail(RCACaseSummary):
    evidence: list[
        EvidenceRead
    ]

    predictions: list[
        PredictionRead
    ]


class RCASnapshotResult(BaseModel):
    case: RCACaseSummary

    evidence_count: int
    prediction_count: int

    message: str


# ==========================================================
# Evidence Fusion
# ==========================================================


class FusionEvidenceItem(BaseModel):
    evidence_id: int

    evidence_key: str

    source: str
    category: str

    strength: float

    value: dict


class CauseFusionResult(BaseModel):
    cause: str

    confidence: float
    confidence_percent: float
    confidence_label: str

    support_score: float
    contradiction_score: float

    diversity_factor: float
    cause_specificity_weight: float

    supporting_evidence_count: int
    contradicting_evidence_count: int

    supporting_evidence: list[
        FusionEvidenceItem
    ]

    contradicting_evidence: list[
        FusionEvidenceItem
    ]

    rank: int


class EvidenceFusionResult(BaseModel):
    engine_type: str

    primary_cause: str | None

    primary_confidence: float
    primary_confidence_percent: float

    confidence_label: str

    rankings: list[
        CauseFusionResult
    ]

    note: str


# ==========================================================
# Hierarchical RCA
# ==========================================================


class HierarchicalCause(
    BaseModel
):
    cause: str

    confidence: float

    confidence_percent: float


class HierarchicalRootCause(
    HierarchicalCause
):
    confidence_label: str


class HierarchicalConditions(
    BaseModel
):
    persistent_degradation: bool

    weather_causal_evidence: bool

    device_specific_pattern: bool


class HierarchicalRCAResult(
    BaseModel
):
    engine_type: str

    incident_domain: HierarchicalCause

    primary_root_cause: HierarchicalRootCause

    contributing_factors: list[
        HierarchicalRootCause
    ]

    conditions: HierarchicalConditions

    flat_fusion: dict

    explanation: str


# ==========================================================
# Structured RCA
# ==========================================================


class StructuredRCAContributor(
    BaseModel
):
    cause: str

    confidence: float

    confidence_label: str


class StructuredRCAConditions(
    BaseModel
):
    persistent_degradation: bool

    weather_causal_evidence: bool

    device_specific_pattern: bool


class StructuredRCAResult(
    BaseModel
):
    engine_type: str

    schema_version: str

    case_id: int

    domain: str

    incident_domain_cause: str

    primary_root_cause: str

    confidence: float

    confidence_percent: float

    contributors: list[
        StructuredRCAContributor
    ]

    conditions: (
        StructuredRCAConditions
    )

    verification_required: bool

    verification_status: str

    verification_reasons: list[str]

    verified: bool = False


# ==========================================================
# RCA Proposal
# ==========================================================


class RCAProposalContributor(
    BaseModel
):
    cause: str

    confidence: float

    evidence_ids: list[int]


class RCAProposal(
    BaseModel
):
    schema_version: str = (
        "RCA_PROPOSAL_V1"
    )

    case_id: int

    source_engine: str

    proposed_domain: str

    primary_cause: str

    confidence: float

    evidence_ids: list[int]

    contributors: list[
        RCAProposalContributor
    ] = Field(
        default_factory=list
    )

    reasoning_summary: str | None = None


# ==========================================================
# ML RCA
# ==========================================================


class MLRCAProbability(
    BaseModel
):
    cause: str

    probability: float


class MLRCAResult(
    BaseModel
):
    prediction_id: int

    case_id: int

    engine_type: str

    predicted_cause: str

    confidence: float

    probabilities: list[
        MLRCAProbability
    ]

    model_schema: str

    dataset_sha256: str | None = None

    manifest_sha256: str | None = None

    advisory_only: bool