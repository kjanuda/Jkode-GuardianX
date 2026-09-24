from pprint import pprint

import requests


BASE_URL = (
    "http://127.0.0.1:8000"
)

CASE_ID = 13


def main():
    packet_url = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}/"
        f"evidence-packet"
    )

    verify_url = (
        f"{BASE_URL}/api/v1/rca/"
        f"cases/{CASE_ID}/"
        f"proposals/verify"
    )

    packet_response = (
        requests.get(
            packet_url,
            timeout=30,
        )
    )

    packet_response.raise_for_status()

    packet = (
        packet_response.json()
    )

    evidence_by_key = {
        item[
            "evidence_key"
        ]: item
        for item
        in packet[
            "evidence"
        ]
    }

    terrain = (
        evidence_by_key[
            "CELL_TERRAIN_CONTEXT"
        ]
    )

    vegetation = (
        evidence_by_key.get(
            "CELL_VEGETATION_CONTEXT"
        )
    )

    contributors = []

    if vegetation is not None:
        contributors.append(
            {
                "cause":
                    "VEGETATION_PROPAGATION_POSSIBLE",

                "confidence":
                    0.40,

                "evidence_ids": [
                    vegetation[
                        "evidence_id"
                    ]
                ],
            }
        )

    proposal = {
        "schema_version":
            "RCA_PROPOSAL_V1",

        "case_id":
            CASE_ID,

        "source_engine":
            "LLM_RAG",

        "proposed_domain":
            "PROPAGATION_DOMAIN",

        "primary_cause":
            "TERRAIN_PROPAGATION_LIKELY",

        "confidence":
            0.69,

        "evidence_ids": [
            terrain[
                "evidence_id"
            ]
        ],

        "contributors":
            contributors,

        "reasoning_summary":
            (
                "Terrain evidence supports "
                "the primary propagation "
                "diagnosis."
            ),
    }

    valid_response = requests.post(
        verify_url,
        json=proposal,
        timeout=30,
    )

    valid_response.raise_for_status()

    valid = (
        valid_response.json()
    )

    bad_proposal = {
        **proposal,

        "evidence_ids":
            [999999],
    }

    bad_response = requests.post(
        verify_url,
        json=bad_proposal,
        timeout=30,
    )

    bad_response.raise_for_status()

    bad = (
        bad_response.json()
    )

    checks = {
        "packet_case":
            packet[
                "case_id"
            ]
            == CASE_ID,

        "terrain_found":
            terrain is not None,

        "valid_accepted":
            valid[
                "verified"
            ]
            is True,

        "valid_status":
            valid[
                "proposal_status"
            ]
            == "ACCEPTED",

        "invalid_rejected":
            bad[
                "verified"
            ]
            is False,

        "invalid_status":
            bad[
                "proposal_status"
            ]
            == "REJECTED",

        "audit_id_created":
            bool(
                valid.get(
                    "proposal_id"
                )
            ),
    }

    print()
    print(
        "GUARDIAN X - REAL "
        "PROPOSAL API TEST"
    )

    print(
        "-" * 70
    )

    pprint(
        checks
    )

    print()

    print(
        "VALID RESULT"
    )

    pprint(
        valid
    )

    print()

    print(
        "INVALID RESULT"
    )

    pprint(
        bad
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