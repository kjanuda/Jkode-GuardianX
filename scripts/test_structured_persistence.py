from pprint import pprint

import requests


BASE_URL = "http://127.0.0.1:8000"

CASE_ID = 13


def main():
    endpoint = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}/structured"
    )

    case_endpoint = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}"
    )

    print()
    print(
        "GUARDIAN X - STRUCTURED "
        "RCA PERSISTENCE TEST"
    )

    print(
        "-" * 70
    )

    first = requests.post(
        endpoint,
        timeout=30,
    )

    first.raise_for_status()

    second = requests.post(
        endpoint,
        timeout=30,
    )

    second.raise_for_status()

    case_response = requests.get(
        case_endpoint,
        timeout=30,
    )

    case_response.raise_for_status()

    case_data = (
        case_response.json()
    )

    structured_predictions = [
        item
        for item
        in case_data[
            "predictions"
        ]
        if item[
            "engine_type"
        ]
        == "STRUCTURED_RCA_V1"
    ]

    result = (
        second.json()
    )

    checks = {
        "verified":
            result[
                "verified"
            ]
            is True,

        "status":
            result[
                "verification_status"
            ]
            == "VERIFIED",

        "root_cause":
            result[
                "primary_root_cause"
            ]
            == (
                "TERRAIN_PROPAGATION_LIKELY"
            ),

        "one_structured_prediction":
            len(
                structured_predictions
            )
            == 1,

        "db_verifier_status":
            (
                len(
                    structured_predictions
                )
                == 1
                and structured_predictions[
                    0
                ][
                    "verifier_status"
                ]
                == "VERIFIED"
            ),
    }

    pprint(
        checks
    )

    print()

    print(
        "STRUCTURED DB ROW:"
    )

    pprint(
        structured_predictions
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