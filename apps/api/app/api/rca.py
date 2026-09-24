from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.risk import (
    get_device_risk,
)

from app.correlation.population import (
    analyze_cell_population,
)

from app.db.session import (
    get_db,
)

from app.models import (
    Cell,
    Device,
    Telemetry,
)

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)

from app.rca.fusion import (
    run_case_fusion,
)

from app.rca.hierarchy import (
    run_hierarchical_rca,
)

from app.rca.population_snapshot import (
    create_population_rca_snapshot,
)

from app.rca.proposal_service import (
    get_case_evidence_packet,
    verify_case_proposal,
)

from app.rca.snapshot import (
    create_rca_snapshot,
)

from app.rca.structured_pipeline import (
    run_structured_rca,
)

from app.rca.ollama_adapter import (
    OllamaRCAError,
)

from app.rca.local_llm_service import (
    run_local_llm_rca,
)

from app.rca.consensus import (
    run_case_consensus,
)

from app.schemas.rca import (
    EvidenceFusionResult,
    HierarchicalRCAResult,
    RCACaseDetail,
    RCACaseSummary,
    RCASnapshotResult,
    RCAProposal,
    StructuredRCAResult,
)


router = APIRouter(
    prefix="/api/v1/rca",
    tags=["RCA"],
)


# ==========================================================
# Device RCA Snapshot
# ==========================================================


@router.post(
    "/device/{device_external_id}/snapshot",
    response_model=RCASnapshotResult,
)
def create_device_rca_snapshot(
    device_external_id: str,

    history_limit: int = Query(
        default=10,
        ge=2,
        le=100,
    ),

    db: Session = Depends(
        get_db
    ),
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
        history_limit=(
            history_limit
        ),
        db=db,
    )

    case = create_rca_snapshot(
        db=db,

        device_id=device.id,

        device_external_id=(
            device_external_id
        ),

        telemetry=latest,

        risk=risk,
    )

    actual_evidence = db.scalars(
        select(RCAEvidence).where(
            RCAEvidence.case_id
            == case.id
        )
    ).all()

    predictions = db.scalars(
        select(RCAPrediction).where(
            RCAPrediction.case_id
            == case.id
        )
    ).all()

    return {
        "case":
            case,

        "evidence_count":
            len(
                actual_evidence
            ),

        "prediction_count":
            len(
                predictions
            ),

        "message":
            (
                "Canonical RCA evidence "
                "snapshot created"
            ),
    }


# ==========================================================
# Cell / Population RCA Snapshot
# ==========================================================


@router.post(
    "/cell/{cell_external_id}/snapshot",
    response_model=RCASnapshotResult,
)
def create_cell_rca_snapshot(
    cell_external_id: str,

    window_minutes: int = Query(
        default=10,
        ge=1,
        le=120,
    ),

    db: Session = Depends(
        get_db
    ),
):
    cell = db.scalar(
        select(Cell).where(
            Cell.cell_id
            == cell_external_id
        )
    )

    if cell is None:
        raise HTTPException(
            status_code=404,
            detail="Cell not found",
        )

    population = (
        analyze_cell_population(
            db=db,

            cell_id=cell.id,

            cell_external_id=(
                cell.cell_id
            ),

            window_minutes=(
                window_minutes
            ),
        )
    )

    if (
        population[
            "total_devices"
        ]
        == 0
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "No population telemetry "
                "available in this window"
            ),
        )

    # IMPORTANT:
    # create_population_rca_snapshot()
    # requires the internal database
    # cell_id in addition to cell_external_id.
    case = (
        create_population_rca_snapshot(
            db=db,

            cell_id=cell.id,

            cell_external_id=(
                cell.cell_id
            ),

            population=population,
        )
    )

    evidence_items = list(
        db.scalars(
            select(RCAEvidence)
            .where(
                RCAEvidence.case_id
                == case.id
            )
        ).all()
    )

    predictions = list(
        db.scalars(
            select(RCAPrediction)
            .where(
                RCAPrediction.case_id
                == case.id
            )
        ).all()
    )

    return {
        "case":
            case,

        "evidence_count":
            len(
                evidence_items
            ),

        "prediction_count":
            len(
                predictions
            ),

        "message":
            (
                "Population RCA evidence "
                "snapshot created"
            ),
    }


# ==========================================================
# RCA Case Detail
# ==========================================================


@router.get(
    "/cases/{case_id}",
    response_model=RCACaseDetail,
)
def get_rca_case(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    case = db.get(
        RCACase,
        case_id,
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="RCA case not found",
        )

    evidence_items = db.scalars(
        select(RCAEvidence)
        .where(
            RCAEvidence.case_id
            == case.id
        )
        .order_by(
            RCAEvidence.id.asc()
        )
    ).all()

    predictions = db.scalars(
        select(RCAPrediction)
        .where(
            RCAPrediction.case_id
            == case.id
        )
        .order_by(
            RCAPrediction.rank.asc(),
            RCAPrediction.id.asc(),
        )
    ).all()

    return {
        "id":
            case.id,

        "case_uuid":
            case.case_uuid,

        "scope_type":
            case.scope_type,

        "scope_ref":
            case.scope_ref,

        "trigger_type":
            case.trigger_type,

        "status":
            case.status,

        "risk_score":
            case.risk_score,

        "risk_level":
            case.risk_level,

        "baseline_primary_cause":
            case.baseline_primary_cause,

        "created_at":
            case.created_at,

        "updated_at":
            case.updated_at,

        "evidence":
            evidence_items,

        "predictions":
            predictions,
    }


# ==========================================================
# Device RCA History
# ==========================================================


@router.get(
    "/device/{device_external_id}/cases",
    response_model=list[
        RCACaseSummary
    ],
)
def get_device_rca_cases(
    device_external_id: str,

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    db: Session = Depends(
        get_db
    ),
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

    return list(
        db.scalars(
            select(RCACase)
            .where(
                RCACase.device_id
                == device.id
            )
            .order_by(
                RCACase.created_at.desc()
            )
            .limit(limit)
        ).all()
    )


# ==========================================================
# Cell / Population RCA History
# ==========================================================


@router.get(
    "/cell/{cell_external_id}/cases",
    response_model=list[
        RCACaseSummary
    ],
)
def get_cell_rca_cases(
    cell_external_id: str,

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    db: Session = Depends(
        get_db
    ),
):
    cell = db.scalar(
        select(Cell).where(
            Cell.cell_id
            == cell_external_id
        )
    )

    if cell is None:
        raise HTTPException(
            status_code=404,
            detail="Cell not found",
        )

    return list(
        db.scalars(
            select(RCACase)
            .where(
                RCACase.scope_type
                == "CELL",

                RCACase.scope_ref
                == cell_external_id,
            )
            .order_by(
                RCACase.created_at.desc()
            )
            .limit(limit)
        ).all()
    )


# ==========================================================
# Evidence Fusion
# ==========================================================


@router.post(
    "/cases/{case_id}/fuse",
    response_model=EvidenceFusionResult,
)
def fuse_rca_case(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return run_case_fusion(
            db=db,
            case_id=case_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


# ==========================================================
# Hierarchical RCA
# ==========================================================


@router.post(
    "/cases/{case_id}/hierarchy",
    response_model=HierarchicalRCAResult,
)
def build_case_hierarchy(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return run_hierarchical_rca(
            db=db,
            case_id=case_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


# ==========================================================
# Verified Structured RCA
# ==========================================================


@router.post(
    "/cases/{case_id}/structured",
    response_model=StructuredRCAResult,
)
def build_case_structured_rca(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return run_structured_rca(
            db=db,
            case_id=case_id,
        )

    except ValueError as exc:
        message = str(
            exc
        )

        if message == (
            "RCA case not found"
        ):
            status_code = 404

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc


# ==========================================================
# Real DB Evidence Packet
# ==========================================================


@router.get(
    "/cases/{case_id}/evidence-packet"
)
def get_rca_evidence_packet(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return get_case_evidence_packet(
            db=db,
            case_id=case_id,
        )

    except ValueError as exc:
        message = str(
            exc
        )

        raise HTTPException(
            status_code=(
                404
                if message
                == "RCA case not found"
                else 400
            ),
            detail=message,
        ) from exc


# ==========================================================
# RCA Proposal Verification
# ==========================================================


@router.post(
    "/cases/{case_id}/proposals/verify"
)
def verify_rca_case_proposal(
    case_id: int,

    proposal: RCAProposal,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return verify_case_proposal(
            db=db,
            case_id=case_id,
            proposal=(
                proposal.model_dump()
            ),
        )

    except ValueError as exc:
        message = str(
            exc
        )

        raise HTTPException(
            status_code=(
                404
                if message
                == "RCA case not found"
                else 400
            ),
            detail=message,
        ) from exc


# ==========================================================
# Local Ollama RCA Proposal
# ==========================================================


@router.post(
    "/cases/{case_id}/local-llm-proposal"
)
def run_case_local_llm_proposal(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return run_local_llm_rca(
            db=db,
            case_id=case_id,
        )

    except ValueError as exc:
        message = str(
            exc
        )

        raise HTTPException(
            status_code=(
                404
                if message
                == "RCA case not found"
                else 400
            ),

            detail=message,
        ) from exc

    except OllamaRCAError as exc:
        raise HTTPException(
            status_code=503,

            detail=str(
                exc
            ),
        ) from exc


# ==========================================================
# RCA Consensus / Agreement Gate
# ==========================================================


@router.post(
    "/cases/{case_id}/consensus"
)
def run_rca_case_consensus(
    case_id: int,

    db: Session = Depends(
        get_db
    ),
):
    try:
        return run_case_consensus(
            db=db,
            case_id=case_id,
        )

    except ValueError as exc:
        message = str(
            exc
        )

        if message == (
            "RCA case not found"
        ):
            status_code = 404

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from exc