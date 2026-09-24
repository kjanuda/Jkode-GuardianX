import sys

from pathlib import Path
from pprint import pprint
from types import SimpleNamespace


API_ROOT = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "api"
)

if str(API_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(API_ROOT),
    )


from app.rca.proposal_verifier import (
    verify_rca_proposal,
)


def evidence(
    *,
    evidence_id,
    evidence_key,
    supports,
    contradicts=None,
    gate=True,
    reliability=0.90,
    freshness=0.95,
    specificity=0.95,
    support_score=1.0,
):
    return SimpleNamespace(
        id=evidence_id,

        evidence_key=evidence_key,

        supports_causes=supports,

        contradicts_causes=(
            contradicts or []
        ),

        gate_passed=gate,

        reliability_score=(
            reliability
        ),

        freshness_score=(
            freshness
        ),

        specificity_score=(
            specificity
        ),

        support_score=(
            support_score
        ),
    )


EVIDENCE = [
    evidence(
        evidence_id=104,

        evidence_key=(
            "CELL_TERRAIN_CONTEXT"
        ),

        supports=[
            "TERRAIN_PROPAGATION_LIKELY"
        ],
    ),

    evidence(
        evidence_id=105,

        evidence_key=(
            "CELL_VEGETATION_CONTEXT"
        ),

        supports=[
            "VEGETATION_PROPAGATION_POSSIBLE"
        ],

        freshness=0.70,

        specificity=0.80,
    ),
]


def run(
    title,
    proposal,
    expected,
):
    result = verify_rca_proposal(
        proposal=proposal,
        evidence_items=EVIDENCE,
    )

    passed = (
        result[
            "verified"
        ]
        is expected
    )

    print()
    print(title)
    print("-" * 60)

    pprint(
        {
            "status":
                result[
                    "proposal_status"
                ],

            "verified":
                result[
                    "verified"
                ],

            "reasons":
                result[
                    "verification_reasons"
                ],

            "result":
                (
                    "PASS"
                    if passed
                    else "FAIL"
                ),
        }
    )

    return passed


def main():
    results = []

    valid = {
        "schema_version":
            "RCA_PROPOSAL_V1",

        "case_id":
            13,

        "source_engine":
            "LLM_RAG",

        "proposed_domain":
            "PROPAGATION_DOMAIN",

        "primary_cause":
            "TERRAIN_PROPAGATION_LIKELY",

        "confidence":
            0.69,

        "evidence_ids":
            [104],

        "contributors": [
            {
                "cause":
                    "VEGETATION_PROPAGATION_POSSIBLE",

                "confidence":
                    0.40,

                "evidence_ids":
                    [105],
            }
        ],

        "reasoning_summary":
            (
                "Terrain obstruction is "
                "supported by the terrain "
                "context. Vegetation is a "
                "secondary contributor."
            ),
    }

    results.append(
        run(
            "VALID EVIDENCE-BASED PROPOSAL",
            valid,
            True,
        )
    )


    invented_evidence = {
        **valid,
        "evidence_ids":
            [9999],
    }

    results.append(
        run(
            "INVENTED EVIDENCE ID",
            invented_evidence,
            False,
        )
    )


    wrong_evidence = {
        **valid,
        "evidence_ids":
            [105],
    }

    results.append(
        run(
            "WRONG CAUSE EVIDENCE",
            wrong_evidence,
            False,
        )
    )


    wrong_domain = {
        **valid,
        "proposed_domain":
            "NETWORK_DOMAIN",
    }

    results.append(
        run(
            "WRONG DOMAIN",
            wrong_domain,
            False,
        )
    )


    hallucinated_cause = {
        **valid,
        "primary_cause":
            "ALIEN_RADIO_INTERFERENCE",
    }

    results.append(
        run(
            "UNKNOWN / HALLUCINATED CAUSE",
            hallucinated_cause,
            False,
        )
    )


    print()
    print("=" * 60)

    print(
        "RCA PROPOSAL SUITE:",
        (
            "PASS"
            if all(results)
            else "FAIL"
        ),
    )


if __name__ == "__main__":
    main()