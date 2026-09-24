from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from pprint import pprint

import requests


BASE_URL = "http://127.0.0.1:8000"
CELL_ID = "GX-CELL-001"

ROOT = Path(__file__).resolve().parents[1]

POPULATION_SIMULATOR = (
    ROOT
    / "scripts"
    / "population_simulator.py"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "ml"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "scenario_probe.json"
)


SCENARIOS = [
    {
        "mode": "network",
        "expected_family":
            "CONGESTION_OR_BACKHAUL",
    },
    {
        "mode": "device-model",
        "expected_family":
            "DEVICE_MODEL_OR_FIRMWARE",
    },
    {
        "mode": "coverage",
        "expected_family":
            "COVERAGE_OR_PROPAGATION",
    },
]


def post_json(
    path: str,
    *,
    timeout: int = 180,
) -> dict:
    response = requests.post(
        f"{BASE_URL}{path}",
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"{path} failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()


def run_population_simulator(
    mode: str,
) -> None:
    print()
    print(
        f"Generating population scenario: "
        f"{mode}"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(
                POPULATION_SIMULATOR
            ),
            "--mode",
            mode,
            "--count-per-model",
            "10",
        ],
        cwd=str(
            ROOT / "apps" / "api"
        ),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(
            result.stdout
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            f"Simulator failed for {mode}"
        )

    lines = [
        line
        for line
        in result.stdout.splitlines()
        if line.strip()
    ]

    # Only show tail so terminal stays clean.
    for line in lines[-8:]:
        print(
            line
        )


def create_case() -> int:
    result = post_json(
        (
            f"/api/v1/rca/cell/"
            f"{CELL_ID}/snapshot"
            f"?window_minutes=10"
        ),
        timeout=240,
    )

    return int(
        result[
            "case"
        ][
            "id"
        ]
    )


def structured_rca(
    case_id: int,
) -> dict:
    return post_json(
        (
            f"/api/v1/rca/cases/"
            f"{case_id}/structured"
        ),
        timeout=240,
    )


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "GUARDIAN X - RCA "
        "SCENARIO PROBE"
    )

    print(
        "=" * 72
    )

    results = []

    for scenario in SCENARIOS:
        mode = scenario[
            "mode"
        ]

        run_population_simulator(
            mode
        )

        case_id = (
            create_case()
        )

        diagnosis = (
            structured_rca(
                case_id
            )
        )

        verified_cause = (
            diagnosis.get(
                "primary_root_cause"
            )
        )

        domain = (
            diagnosis.get(
                "domain"
            )
        )

        verified = (
            diagnosis.get(
                "verified"
            )
        )

        row = {
            "data_origin":
                "SYNTHETIC",

            "scenario_name":
                mode,

            "case_id":
                case_id,

            "expected_family":
                scenario[
                    "expected_family"
                ],

            "verified":
                verified,

            "verified_domain":
                domain,

            "verified_cause":
                verified_cause,

            "confidence":
                diagnosis.get(
                    "confidence"
                ),

            "verification_status":
                diagnosis.get(
                    "verification_status"
                ),

            "verification_reasons":
                diagnosis.get(
                    "verification_reasons"
                ),
        }

        results.append(
            row
        )

        print()
        print(
            f"RESULT FOR {mode.upper()}"
        )

        print(
            "-" * 72
        )

        pprint(
            row
        )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "schema_version":
                    "RCA_SCENARIO_PROBE_V1",

                "results":
                    results,
            },
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        "=" * 72
    )

    print(
        f"Saved: {OUTPUT_PATH}"
    )

    print()

    print(
        "SUMMARY"
    )

    print(
        "-" * 72
    )

    for row in results:
        print(
            f"{row['scenario_name']:<14}"
            f" -> "
            f"{row['verified_cause']}"
            f" | "
            f"verified={row['verified']}"
        )


if __name__ == "__main__":
    main()