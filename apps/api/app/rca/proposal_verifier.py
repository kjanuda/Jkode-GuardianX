from __future__ import annotations

from typing import Any

from app.rca.verifier import (
    CAUSE_REQUIREMENTS,
    MIN_EVIDENCE_FRESHNESS,
    MIN_EVIDENCE_RELIABILITY,
    STRONG_CONTRADICTION_THRESHOLD,
    effective_evidence_strength,
)


MIN_PROPOSAL_CONFIDENCE = 0.50

MIN_CONTRIBUTOR_CONFIDENCE = 0.25


ALLOWED_SOURCE_ENGINES = {
    "RULE_ENGINE",
    "ML_MODEL",
    "LLM_RAG",
    "HUMAN_ANALYST",
}


def verify_evidence_reference(
    *,
    cause: str,
    evidence_ids: list[int],
    evidence_map: dict[int, Any],
) -> list[str]:
    reasons: list[str] = []

    if not evidence_ids:
        return [
            "NO_EVIDENCE_REFERENCES"
        ]

    for evidence_id in evidence_ids:
        evidence = evidence_map.get(
            evidence_id
        )

        if evidence is None:
            reasons.append(
                "EVIDENCE_ID_NOT_FOUND:"
                f"{evidence_id}"
            )

            continue

        # -----------------------------------------
        # Evidence gate
        # -----------------------------------------

        if evidence.gate_passed is False:
            reasons.append(
                "REFERENCED_EVIDENCE_"
                "GATE_FAILED:"
                f"{evidence_id}"
            )

            continue

        # -----------------------------------------
        # Freshness
        # -----------------------------------------

        freshness = float(
            evidence.freshness_score
            or 0.0
        )

        if freshness < (
            MIN_EVIDENCE_FRESHNESS
        ):
            reasons.append(
                "REFERENCED_EVIDENCE_STALE:"
                f"{evidence_id}"
            )

        # -----------------------------------------
        # Reliability
        # -----------------------------------------

        reliability = float(
            evidence.reliability_score
            or 0.0
        )

        if reliability < (
            MIN_EVIDENCE_RELIABILITY
        ):
            reasons.append(
                "REFERENCED_EVIDENCE_"
                "LOW_RELIABILITY:"
                f"{evidence_id}"
            )

        # -----------------------------------------
        # Cause support
        # -----------------------------------------

        supports = (
            evidence.supports_causes
            or []
        )

        contradicts = (
            evidence.contradicts_causes
            or []
        )

        if cause not in supports:
            reasons.append(
                "EVIDENCE_DOES_NOT_SUPPORT_"
                "PROPOSED_CAUSE:"
                f"{evidence_id}"
            )

        # -----------------------------------------
        # Strong contradiction
        # -----------------------------------------

        if cause in contradicts:
            strength = (
                effective_evidence_strength(
                    evidence
                )
            )

            if strength >= (
                STRONG_CONTRADICTION_THRESHOLD
            ):
                reasons.append(
                    "EVIDENCE_STRONGLY_"
                    "CONTRADICTS_PROPOSED_CAUSE:"
                    f"{evidence_id}"
                )

    return reasons


def verify_rca_proposal(
    *,
    proposal: dict[str, Any],
    evidence_items: list,
) -> dict[str, Any]:
    """
    Verify a proposal from any reasoning engine.

    Rule / ML / LLM-RAG / Human Analyst engines
    may propose diagnoses, but the proposal cannot
    become trusted RCA unless it passes the
    evidence and consistency gates.

    The verifier is the trust boundary between
    proposal generation and final RCA persistence.
    """

    reasons: list[str] = []

    # -----------------------------------------
    # Proposal schema
    # -----------------------------------------

    if (
        proposal.get(
            "schema_version"
        )
        != "RCA_PROPOSAL_V1"
    ):
        reasons.append(
            "INVALID_PROPOSAL_SCHEMA"
        )

    # -----------------------------------------
    # Source engine validation
    # -----------------------------------------

    source_engine = (
        proposal.get(
            "source_engine"
        )
    )

    if (
        source_engine
        not in ALLOWED_SOURCE_ENGINES
    ):
        reasons.append(
            "UNSUPPORTED_SOURCE_ENGINE"
        )

    # -----------------------------------------
    # Primary proposal
    # -----------------------------------------

    primary = proposal.get(
        "primary_cause"
    )

    domain = proposal.get(
        "proposed_domain"
    )

    confidence = float(
        proposal.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    # -----------------------------------------
    # Primary confidence validation
    # -----------------------------------------

    if (
        confidence < 0.0
        or confidence > 1.0
    ):
        reasons.append(
            "INVALID_CONFIDENCE_RANGE"
        )

    elif confidence < (
        MIN_PROPOSAL_CONFIDENCE
    ):
        reasons.append(
            "PROPOSAL_CONFIDENCE_TOO_LOW"
        )

    # -----------------------------------------
    # Primary cause validation
    # -----------------------------------------

    requirement = (
        CAUSE_REQUIREMENTS.get(
            primary
        )
    )

    if requirement is None:
        reasons.append(
            "UNSUPPORTED_PROPOSED_CAUSE"
        )

    else:
        expected_domain = (
            requirement[
                "domain"
            ]
        )

        if domain != expected_domain:
            reasons.append(
                "PROPOSAL_DOMAIN_CAUSE_"
                "MISMATCH"
            )

    # -----------------------------------------
    # Evidence map
    # -----------------------------------------

    evidence_map = {
        item.id: item
        for item in evidence_items
    }

    # -----------------------------------------
    # Primary evidence verification
    # -----------------------------------------

    primary_evidence_ids = (
        proposal.get(
            "evidence_ids"
        )
        or []
    )

    reasons.extend(
        verify_evidence_reference(
            cause=primary,
            evidence_ids=(
                primary_evidence_ids
            ),
            evidence_map=(
                evidence_map
            ),
        )
    )

    # -----------------------------------------
    # Contributor verification
    # -----------------------------------------

    verified_contributors = []

    contributors = (
        proposal.get(
            "contributors"
        )
        or []
    )

    for contributor in contributors:
        cause = contributor.get(
            "cause"
        )

        contributor_reasons = []

        # -----------------------------------------
        # Contributor cannot equal primary
        # -----------------------------------------

        if cause == primary:
            contributor_reasons.append(
                "CONTRIBUTOR_EQUALS_PRIMARY"
            )

        # -----------------------------------------
        # Contributor cause validation
        # -----------------------------------------

        if (
            cause
            not in CAUSE_REQUIREMENTS
        ):
            contributor_reasons.append(
                "UNSUPPORTED_CONTRIBUTOR_CAUSE"
            )

        # -----------------------------------------
        # Contributor confidence
        # -----------------------------------------

        contributor_confidence = float(
            contributor.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        if (
            contributor_confidence < 0.0
            or contributor_confidence > 1.0
        ):
            contributor_reasons.append(
                "INVALID_CONTRIBUTOR_"
                "CONFIDENCE"
            )

        elif (
            contributor_confidence
            < MIN_CONTRIBUTOR_CONFIDENCE
        ):
            contributor_reasons.append(
                "CONTRIBUTOR_CONFIDENCE_TOO_LOW"
            )

        # -----------------------------------------
        # Contributor cannot outrank primary
        # -----------------------------------------

        if (
            contributor_confidence
            > confidence
        ):
            contributor_reasons.append(
                "CONTRIBUTOR_CONFIDENCE_"
                "EXCEEDS_PRIMARY"
            )

        # -----------------------------------------
        # Contributor evidence verification
        # -----------------------------------------

        contributor_reasons.extend(
            verify_evidence_reference(
                cause=cause,
                evidence_ids=(
                    contributor.get(
                        "evidence_ids"
                    )
                    or []
                ),
                evidence_map=(
                    evidence_map
                ),
            )
        )

        # -----------------------------------------
        # Contributor audit reasons
        # -----------------------------------------

        if contributor_reasons:
            reasons.extend(
                [
                    "CONTRIBUTOR:"
                    f"{cause}:"
                    f"{reason}"
                    for reason
                    in contributor_reasons
                ]
            )

        else:
            verified_contributors.append(
                contributor
            )

    # -----------------------------------------
    # Deduplicate verification reasons
    # -----------------------------------------

    reasons = list(
        dict.fromkeys(
            reasons
        )
    )

    # -----------------------------------------
    # Final verification status
    # -----------------------------------------

    verified = (
        len(reasons) == 0
    )

    return {
        "schema_version":
            "RCA_PROPOSAL_VERIFICATION_V1",

        "case_id":
            proposal.get(
                "case_id"
            ),

        "source_engine":
            source_engine,

        "proposed_domain":
            domain,

        "primary_cause":
            primary,

        "confidence":
            confidence,

        "evidence_ids":
            primary_evidence_ids,

        "verified_contributors":
            verified_contributors,

        "proposal_status":
            (
                "ACCEPTED"
                if verified
                else "REJECTED"
            ),

        "verified":
            verified,

        "verification_reasons":
            reasons,

        # Explanation text is retained
        # for audit/debugging, but is never
        # treated as evidence.
        "reasoning_summary":
            proposal.get(
                "reasoning_summary"
            ),
    }