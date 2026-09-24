from pprint import pprint

import requests


BASE_URL = (
    "http://127.0.0.1:8000"
)

CASE_ID = 13


def main():
    url = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}/"
        f"local-llm-proposal"
    )

    print()
    print(
        "GUARDIAN X - LOCAL "
        "OLLAMA RCA TEST"
    )

    print(
        "-" * 70
    )

    response = requests.post(
        url,
        timeout=360,
    )

    print(
        "HTTP STATUS:",
        response.status_code,
    )

    if response.status_code != 200:
        print()
        pprint(
            response.json()
        )

        return

    result = (
        response.json()
    )

    proposal = (
        result[
            "proposal"
        ]
    )

    verification = (
        result[
            "verification"
        ]
    )

    print()
    print(
        "LOCAL MODEL RESULT"
    )

    pprint(
        {
            "provider":
                result[
                    "provider"
                ],

            "model":
                result[
                    "model"
                ],

            "primary_cause":
                proposal[
                    "primary_cause"
                ],

            "domain":
                proposal[
                    "proposed_domain"
                ],

            "confidence":
                proposal[
                    "confidence"
                ],

            "evidence_ids":
                proposal[
                    "evidence_ids"
                ],

            "contributors":
                proposal[
                    "contributors"
                ],

            "proposal_status":
                verification[
                    "proposal_status"
                ],

            "verified":
                verification[
                    "verified"
                ],

            "verification_reasons":
                verification[
                    "verification_reasons"
                ],

            "proposal_id":
                verification[
                    "proposal_id"
                ],
        }
    )

    print()
    print(
        "REASONING SUMMARY"
    )

    print(
        proposal[
            "reasoning_summary"
        ]
    )

    print()
    print(
        "OLLAMA METADATA"
    )

    pprint(
        result[
            "ollama_metadata"
        ]
    )

    print()

    if verification[
        "verified"
    ]:
        print(
            "RESULT: ACCEPTED ✅"
        )

    else:
        print(
            "RESULT: SAFELY REJECTED ✅"
        )


if __name__ == "__main__":
    main()