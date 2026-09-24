from pprint import pprint

import requests


BASE_URL = (
    "http://127.0.0.1:8000"
)

CASE_ID = 13


def main():
    consensus_url = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}/consensus"
    )

    case_url = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}"
    )

    first = requests.post(
        consensus_url,
        timeout=30,
    )

    first.raise_for_status()

    # Run twice to test idempotency.
    second = requests.post(
        consensus_url,
        timeout=30,
    )

    second.raise_for_status()

    result = (
        second.json()
    )

    case_response = requests.get(
        case_url,
        timeout=30,
    )

    case_response.raise_for_status()

    case_data = (
        case_response.json()
    )

    consensus_rows = [
        item
        for item
        in case_data[
            "predictions"
        ]
        if item[
            "engine_type"
        ]
        == "RCA_CONSENSUS_V1"
    ]

    checks = {
        "deterministic_verified":
            result[
                "deterministic"
            ][
                "verified"
            ]
            is True,

        "llm_accepted":
            result[
                "llm"
            ][
                "accepted"
            ]
            is True,

        "cause_match":
            result[
                "agreement"
            ][
                "primary_cause_match"
            ]
            is True,

        "domain_match":
            result[
                "agreement"
            ][
                "domain_match"
            ]
            is True,

        "agreement":
            result[
                "consensus_status"
            ]
            == "AGREEMENT",

        "policy_review_allowed":
            result[
                "action_gate"
            ]
            == (
                "ELIGIBLE_FOR_POLICY_REVIEW"
            ),

        "no_human_review":
            result[
                "human_review_required"
            ]
            is False,

        "one_consensus_row":
            len(
                consensus_rows
            )
            == 1,

        "confidence_not_boosted":
            result[
                "deterministic"
            ][
                "confidence"
            ]
            == 0.6904,
    }

    print()
    print(
        "GUARDIAN X - RCA "
        "CONSENSUS TEST"
    )

    print("-" * 70)

    pprint(
        checks
    )

    print()

    pprint(
        result
    )

    print()

    print(
        "RESULT:",
        (
            "PASS"
            if all(
                checks.values()
            )
            else "CHECK"
        ),
    )


if __name__ == "__main__":
    main()