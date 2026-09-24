
from sqlalchemy.orm import Session

from app.correlation.cross_layer import (
    analyze_cell_cross_layers,
)

from app.models.rca import (
    RCACase,
    RCAEvidence,
    RCAPrediction,
)

from app.rca.cell_context import (
    analyze_cell_context,
)

from app.rca.evidence import (
    build_cell_context_evidence,
    build_cross_layer_evidence,
    build_population_evidence,
)


def make_json_safe_population(
    population: dict,
) -> dict:
    output = dict(
        population
    )

    output[
        "window_start"
    ] = population[
        "window_start"
    ].isoformat()

    output[
        "window_end"
    ] = population[
        "window_end"
    ].isoformat()

    return output


def create_population_rca_snapshot(
    *,
    db: Session,
    cell_id: int,
    cell_external_id: str,
    population: dict,
    trigger_type: str = (
        "POPULATION_CORRELATION"
    ),
) -> RCACase:

    likely_scope = (
        population[
            "likely_scope"
        ]
    )

    # ======================================================
    # Cross-layer analysis
    # ======================================================

    cross_layer = (
        analyze_cell_cross_layers(
            db=db,

            cell_id=cell_id,

            window_start=(
                population[
                    "window_start"
                ]
            ),

            window_end=(
                population[
                    "window_end"
                ]
            ),

            population=population,
        )
    )

    # ======================================================
    # Cell context analysis
    # ======================================================

    cell_context = (
        analyze_cell_context(
            db=db,

            cell_id=cell_id,

            window_start=(
                population[
                    "window_start"
                ]
            ),

            window_end=(
                population[
                    "window_end"
                ]
            ),

            max_devices=3,

            history_limit=10,
        )
    )

    # ======================================================
    # Create RCA case
    # ======================================================

    case = RCACase(
        device_id=None,

        alert_id=None,

        scope_type="CELL",

        scope_ref=(
            cell_external_id
        ),

        trigger_type=(
            trigger_type
        ),

        status="OPEN",

        # Population prevalence is not
        # the same thing as service risk.
        #
        # Evidence fusion calculates
        # calibrated confidence later.
        risk_score=None,

        risk_level=None,

        baseline_primary_cause=(
            likely_scope
        ),
    )

    db.add(
        case
    )

    db.flush()

    # ======================================================
    # Build evidence
    #
    # Three independent evidence layers:
    #
    # 1. Population correlation
    # 2. Cross-layer network analysis
    # 3. Cell context:
    #    - terrain
    #    - vegetation
    #    - weather
    #    - historical persistence
    # ======================================================

    evidence_items = (
        build_population_evidence(
            population
        )
        +
        build_cross_layer_evidence(
            population=population,
            cross_layer=cross_layer,
        )
        +
        build_cell_context_evidence(
            population=population,
            cross_layer=cross_layer,
            cell_context=cell_context,
        )
    )

    # ======================================================
    # Persist evidence
    # ======================================================

    for item in evidence_items:
        db.add(
            RCAEvidence(
                case_id=case.id,
                **item,
            )
        )

    # ======================================================
    # Baseline population prediction
    # ======================================================

    prediction = RCAPrediction(
        case_id=case.id,

        engine_type=(
            "POPULATION_RULE_BASELINE"
        ),

        primary_cause=(
            likely_scope
        ),

        # Evidence fusion calculates
        # calibrated confidence later.
        confidence=None,

        rank=1,

        # Keep all diagnostic layers.
        #
        # This allows the RCA API/UI to inspect:
        #
        # population -> what the population correlation found
        # cross_layer -> what the network signature found
        # cell_context -> what geo/environment/history found
        output_json={
            "population":
                make_json_safe_population(
                    population
                ),

            "cross_layer":
                cross_layer,

            "cell_context":
                cell_context,
        },

        verifier_status=(
            "NOT_VERIFIED"
        ),

        verifier_reason=None,
    )

    db.add(
        prediction
    )

    # ======================================================
    # Commit
    # ======================================================

    db.commit()

    db.refresh(
        case
    )

    return case

