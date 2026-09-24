from __future__ import annotations

from sqlalchemy.orm import Session

from app.rca.ollama_adapter import (
    generate_ollama_rca_proposal,
)

from app.rca.proposal_service import (
    get_case_evidence_packet,
    verify_case_proposal,
)

from app.rca.rag_context import (
    build_compact_llm_packet,
)


def run_local_llm_rca(
    *,
    db: Session,
    case_id: int,
) -> dict:
    """
    Guardian X local LLM RCA pipeline.

    Database evidence
        -> Canonical evidence packet
        -> Compact LLM evidence packet
        -> Local Ollama model
        -> Structured proposal
        -> Deterministic verifier
        -> Audit trail

    Important safety boundary:

        LLM
            -> receives compact evidence only

        Verifier
            -> independently verifies the proposal
               against the complete database evidence

    Ollama never directly creates the
    final verified RCA.
    """

    # ========================================================
    # 1. BUILD CANONICAL EVIDENCE PACKET
    # ========================================================

    evidence_packet = (
        get_case_evidence_packet(
            db=db,
            case_id=case_id,
        )
    )

    # ========================================================
    # 2. BUILD COMPACT LLM PACKET
    # ========================================================
    #
    # The canonical packet may contain large structured
    # objects such as detailed terrain/Fresnel obstruction
    # geometry.
    #
    # The local LLM receives only decision-relevant
    # evidence and context fields.
    #
    # The complete evidence remains available through
    # the canonical packet / database for verification.
    #

    compact_packet = (
        build_compact_llm_packet(
            evidence_packet=(
                evidence_packet
            )
        )
    )

    # ========================================================
    # 3. GENERATE LLM RCA PROPOSAL
    # ========================================================

    generated = (
        generate_ollama_rca_proposal(
            evidence_packet=(
                compact_packet
            )
        )
    )

    model_output = dict(
        generated[
            "proposal"
        ]
    )

    # ========================================================
    # 4. SERVER-CONTROLLED PROPOSAL FIELDS
    # ========================================================
    #
    # The local LLM is NOT trusted to choose:
    #
    #   - case_id
    #   - schema_version
    #   - source_engine
    #
    # These are controlled by Guardian X.
    #

    proposal = {
        "schema_version":
            "RCA_PROPOSAL_V1",

        "case_id":
            case_id,

        "source_engine":
            "LLM_RAG",

        **model_output,
    }

    # ========================================================
    # 5. DETERMINISTIC VERIFICATION
    # ========================================================
    #
    # IMPORTANT:
    #
    # Do NOT verify against compact_packet.
    #
    # verify_case_proposal() independently accesses the
    # complete database evidence for the case.
    #
    # This preserves the safety boundary:
    #
    #     LLM -> proposal
    #     Verifier -> final authority
    #

    verification = (
        verify_case_proposal(
            db=db,
            case_id=case_id,
            proposal=proposal,
        )
    )

    # ========================================================
    # 6. RETURN AUDITABLE RESULT
    # ========================================================

    return {
        "schema_version":
            "LOCAL_LLM_RCA_RUN_V1",

        "case_id":
            case_id,

        "provider":
            "OLLAMA_LOCAL",

        "model":
            generated[
                "model"
            ],

        "proposal":
            proposal,

        "verification":
            verification,

        "accepted":
            verification[
                "verified"
            ],

        "ollama_metadata":
            generated[
                "ollama_metadata"
            ],
    }