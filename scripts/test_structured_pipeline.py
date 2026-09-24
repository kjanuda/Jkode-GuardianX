import sys
from pathlib import Path
from pprint import pprint

import requests


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


from app.rca.structured import (
    build_structured_rca,
)

from app.rca.verifier import (
    verify_structured_rca,
)


BASE_URL = "http://127.0.0.1:8000"

CASE_ID = 13


def post_json(
    path: str,
) -> dict:
    response = requests.post(
        f"{BASE_URL}{path}",
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def main():
    print()
    print(
        "GUARDIAN X - STRUCTURED RCA "
        "END-TO-END TEST"
    )
    print(
        "-" * 70
    )

    print()
    print("1. Running evidence fusion...")

    fusion = post_json(
        f"/api/v1/rca/cases/"
        f"{CASE_ID}/fuse"
    )

    print(
        "Fusion primary:",
        fusion[
            "primary_cause"
        ],
    )

    print(
        "Fusion confidence:",
        fusion[
            "primary_confidence_percent"
        ],
    )


    print()
    print("2. Building hierarchy...")

    hierarchy = post_json(
        f"/api/v1/rca/cases/"
        f"{CASE_ID}/hierarchy"
    )

    print(
        "Incident domain:",
        hierarchy[
            "incident_domain"
        ][
            "cause"
        ],
    )

    print(
        "Primary root cause:",
        hierarchy[
            "primary_root_cause"
        ][
            "cause"
        ],
    )


    print()
    print(
        "3. Building structured RCA..."
    )

    structured = (
        build_structured_rca(
            case_id=CASE_ID,
            hierarchy=hierarchy,
        )
    )


    print()
    print(
        "4. Running deterministic "
        "verifier..."
    )

    verified = (
        verify_structured_rca(
            diagnosis=structured
        )
    )


    print()
    print(
        "FINAL VERIFIED DIAGNOSIS"
    )

    print(
        "-" * 70
    )

    pprint(
        verified
    )


    print()
    print(
        "PIPELINE VALIDATION"
    )

    print(
        "-" * 70
    )

    checks = {
        "schema":
            verified.get(
                "schema_version"
            )
            == "RCA_STRUCTURED_V1",

        "verified":
            verified.get(
                "verified"
            )
            is True,

        "domain":
            verified.get(
                "domain"
            )
            == "PROPAGATION_DOMAIN",

        "root_cause":
            verified.get(
                "primary_root_cause"
            )
            == (
                "TERRAIN_PROPAGATION_LIKELY"
            ),

        "no_rejections":
            verified.get(
                "verification_reasons"
            )
            == [],
    }

    pprint(
        checks
    )

    all_pass = all(
        checks.values()
    )

    print()
    print(
        "RESULT:",
        (
            "PASS"
            if all_pass
            else "CHECK"
        ),
    )


if __name__ == "__main__":
    main()