import sys

from pathlib import Path
from pprint import pprint


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


from app.rca.consensus import (
    build_consensus_result,
)


DETERMINISTIC = {
    "id": 48,

    "primary_cause":
        "TERRAIN_PROPAGATION_LIKELY",

    "confidence":
        0.6904,

    "verifier_status":
        "VERIFIED",

    "output_json": {
        "verified":
            True,

        "domain":
            "PROPAGATION_DOMAIN",

        "primary_root_cause":
            "TERRAIN_PROPAGATION_LIKELY",

        "confidence":
            0.6904,

        "contributors": [
            {
                "cause":
                    "VEGETATION_PROPAGATION_POSSIBLE",

                "confidence":
                    0.407,
            }
        ],
    },
}


def accepted_llm_audit(
    *,
    cause,
    domain,
):
    return {
        "id": 999,

        "primary_cause":
            cause,

        "confidence":
            0.90,

        "verifier_status":
            "ACCEPTED",

        "output_json": {
            "proposal": {
                "primary_cause":
                    cause,

                "proposed_domain":
                    domain,

                "confidence":
                    0.90,
            },

            "verification": {
                "verified":
                    True,

                "proposal_status":
                    "ACCEPTED",

                "primary_cause":
                    cause,

                "proposed_domain":
                    domain,

                "confidence":
                    0.90,

                "proposal_id":
                    "TEST-PROPOSAL",

                "verified_contributors":
                    [],
            },
        },
    }


def run_test(
    title,
    llm_audit,
    expected_reasons,
):
    result = (
        build_consensus_result(
            case_id=999,
            deterministic=DETERMINISTIC,
            llm_audit=llm_audit,
        )
    )

    reasons = set(
        result[
            "reasons"
        ]
    )

    checks = {
        "disagreement":
            result[
                "consensus_status"
            ]
            == "DISAGREEMENT",

        "blocked":
            result[
                "action_gate"
            ]
            == "BLOCKED",

        "human_review":
            result[
                "human_review_required"
            ]
            is True,

        "expected_reasons":
            all(
                reason in reasons
                for reason
                in expected_reasons
            ),

        "confidence_not_boosted":
            result[
                "deterministic"
            ][
                "confidence"
            ]
            == 0.6904,
    }

    print()
    print(title)
    print("-" * 70)

    pprint(
        checks
    )

    print()

    pprint(
        {
            "consensus_status":
                result[
                    "consensus_status"
                ],

            "action_gate":
                result[
                    "action_gate"
                ],

            "human_review_required":
                result[
                    "human_review_required"
                ],

            "reasons":
                result[
                    "reasons"
                ],
        }
    )

    return all(
        checks.values()
    )


def main():
    results = []

    # ----------------------------------------
    # Same domain, different root cause
    # ----------------------------------------

    results.append(
        run_test(
            (
                "ROOT-CAUSE DISAGREEMENT "
                "WITH SAME DOMAIN"
            ),

            accepted_llm_audit(
                cause=(
                    "COVERAGE_OR_PROPAGATION"
                ),

                domain=(
                    "PROPAGATION_DOMAIN"
                ),
            ),

            [
                "ROOT_CAUSE_DISAGREEMENT"
            ],
        )
    )

    # ----------------------------------------
    # Different domain + different cause
    # ----------------------------------------

    results.append(
        run_test(
            (
                "DOMAIN + ROOT-CAUSE "
                "DISAGREEMENT"
            ),

            accepted_llm_audit(
                cause=(
                    "CONGESTION_OR_BACKHAUL"
                ),

                domain=(
                    "NETWORK_DOMAIN"
                ),
            ),

            [
                "DOMAIN_DISAGREEMENT",
                "ROOT_CAUSE_DISAGREEMENT",
            ],
        )
    )

    print()
    print("=" * 70)

    print(
        "CONSENSUS DISAGREEMENT SUITE:",
        (
            "PASS"
            if all(results)
            else "FAIL"
        ),
    )


if __name__ == "__main__":
    main()