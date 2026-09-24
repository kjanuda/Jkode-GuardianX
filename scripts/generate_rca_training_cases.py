
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path
from uuid import uuid4

import requests


BASE_URL = "http://127.0.0.1:8000"
CELL_ID = "GX-CELL-001"

ROOT = Path(__file__).resolve().parents[1]

API_ROOT = (
    ROOT
    / "apps"
    / "api"
)

SIMULATOR = (
    ROOT
    / "scripts"
    / "population_simulator.py"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "ml"
)

MANIFEST_PATH = (
    OUTPUT_DIR
    / "synthetic_rca_manifest.jsonl"
)


SCENARIOS = {
    "network": {
        "expected_domain":
            "NETWORK_DOMAIN",

        "expected_cause":
            "CONGESTION_OR_BACKHAUL",
    },

    "device-model": {
        "expected_domain":
            "DEVICE_DOMAIN",

        "expected_cause":
            "DEVICE_MODEL_OR_FIRMWARE",
    },

    "coverage": {
        "expected_domain":
            "PROPAGATION_DOMAIN",

        "expected_cause":
            "TERRAIN_PROPAGATION_LIKELY",
    },

    "interference": {
        "expected_domain":
            "NETWORK_DOMAIN",

        "expected_cause":
            "INTERFERENCE",
    },

    "outage": {
        "expected_domain":
            "NETWORK_DOMAIN",

        "expected_cause":
            "OUTAGE",
    },
}


SEED_OFFSETS = {
    "network": 0,
    "device-model": 10000,
    "coverage": 20000,
    "interference": 30000,
    "outage": 40000,
}


def post_json(
    path: str,
    *,
    timeout: int = 300,
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


def run_simulator(
    *,
    mode: str,
    seed: int,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                SIMULATOR
            ),
            "--mode",
            mode,
            "--count-per-model",
            "10",
            "--seed",
            str(
                seed
            ),
        ],
        cwd=str(
            API_ROOT
        ),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Simulator failed:\n"
            f"{result.stdout}\n"
            f"{result.stderr}"
        )


def create_snapshot() -> dict:
    return post_json(
        (
            f"/api/v1/rca/cell/"
            f"{CELL_ID}/snapshot"
            "?window_minutes=10"
        ),
        timeout=300,
    )


def run_structured(
    case_id: int,
) -> dict:
    return post_json(
        (
            f"/api/v1/rca/cases/"
            f"{case_id}/structured"
        ),
        timeout=300,
    )


def append_manifest(
    row: dict,
) -> None:
    with MANIFEST_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                row,
                ensure_ascii=False,
            )
            + "\n"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate verified Guardian X "
            "synthetic RCA training cases"
        )
    )

    parser.add_argument(
        "--runs-per-mode",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--base-seed",
        type=int,
        default=34000,
    )

    parser.add_argument(
        "--modes",
        nargs="+",
        choices=list(
            SCENARIOS.keys()
        ),
        default=None,
        help=(
            "Optional subset of simulator "
            "modes to generate"
        ),
    )

    args = parser.parse_args()

    selected_modes = (
        args.modes
        if args.modes
        else list(
            SCENARIOS.keys()
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    batch_id = str(
        uuid4()
    )

    total = (
        len(
            selected_modes
        )
        * args.runs_per_mode
    )

    passed = 0
    failed = 0
    generated = 0

    print()
    print(
        "GUARDIAN X - SYNTHETIC "
        "RCA DATASET GENERATOR"
    )

    print("=" * 72)

    print(
        f"Batch ID      : {batch_id}"
    )

    print(
        f"Runs/mode     : "
        f"{args.runs_per_mode}"
    )

    print(
        "Selected modes: "
        f"{', '.join(selected_modes)}"
    )

    print(
        f"Expected cases: {total}"
    )

    print("=" * 72)

    for mode in selected_modes:
        expected = (
            SCENARIOS[
                mode
            ]
        )

        for run_index in range(
            args.runs_per_mode
        ):
            seed = (
                args.base_seed
                + SEED_OFFSETS[
                    mode
                ]
                + run_index
            )

            print()
            print(
                f"[{generated + 1}/{total}] "
                f"{mode} | seed={seed}"
            )

            try:
                run_simulator(
                    mode=mode,
                    seed=seed,
                )

                snapshot = (
                    create_snapshot()
                )

                case = (
                    snapshot[
                        "case"
                    ]
                )

                case_id = int(
                    case[
                        "id"
                    ]
                )

                structured = (
                    run_structured(
                        case_id
                    )
                )

                verified = (
                    structured.get(
                        "verified"
                    )
                    is True
                )

                verified_cause = (
                    structured.get(
                        "primary_root_cause"
                    )
                )

                verified_domain = (
                    structured.get(
                        "domain"
                    )
                )

                cause_match = (
                    verified_cause
                    == expected[
                        "expected_cause"
                    ]
                )

                domain_match = (
                    verified_domain
                    == expected[
                        "expected_domain"
                    ]
                )

                label_match = (
                    verified
                    and cause_match
                    and domain_match
                )

                row = {
                    "schema_version":
                        "SYNTHETIC_RCA_MANIFEST_V1",

                    "data_origin":
                        "SYNTHETIC",

                    "generator":
                        "GUARDIAN_X_POPULATION_SIM_V1",

                    "batch_id":
                        batch_id,

                    "generation_group":
                        f"{batch_id}:{mode}",

                    "seed":
                        seed,

                    "scenario_name":
                        mode,

                    "cell_id":
                        CELL_ID,

                    "case_id":
                        case_id,

                    "case_uuid":
                        case.get(
                            "case_uuid"
                        ),

                    "expected_domain":
                        expected[
                            "expected_domain"
                        ],

                    "expected_cause":
                        expected[
                            "expected_cause"
                        ],

                    "verified_domain":
                        verified_domain,

                    "verified_cause":
                        verified_cause,

                    "verified_confidence":
                        structured.get(
                            "confidence"
                        ),

                    "structured_verified":
                        verified,

                    "cause_match":
                        cause_match,

                    "domain_match":
                        domain_match,

                    "label_match":
                        label_match,

                    "verification_status":
                        structured.get(
                            "verification_status"
                        ),

                    "verification_reasons":
                        structured.get(
                            "verification_reasons"
                        )
                        or [],

                    "created_at":
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                }

                append_manifest(
                    row
                )

                generated += 1

                if label_match:
                    passed += 1

                    print(
                        "PASS | "
                        f"case={case_id} | "
                        f"{verified_cause} | "
                        f"confidence="
                        f"{structured.get('confidence')}"
                    )

                else:
                    failed += 1

                    print(
                        "LABEL MISMATCH | "
                        f"case={case_id}"
                    )

                    print(
                        " expected:",
                        expected[
                            "expected_cause"
                        ],
                    )

                    print(
                        " verified:",
                        verified_cause,
                    )

                    print(
                        " expected domain:",
                        expected[
                            "expected_domain"
                        ],
                    )

                    print(
                        " verified domain:",
                        verified_domain,
                    )

            except Exception as exc:
                generated += 1
                failed += 1

                print(
                    "ERROR:",
                    exc,
                )

    print()
    print("=" * 72)

    print(
        f"Generated : {generated}"
    )

    print(
        f"Matched   : {passed}"
    )

    print(
        f"Rejected  : {failed}"
    )

    print(
        f"Manifest  : "
        f"{MANIFEST_PATH}"
    )

    print()

    if failed == 0:
        print(
            "RESULT: PASS"
        )
    else:
        print(
            "RESULT: CHECK MISMATCHES"
        )


if __name__ == "__main__":
    main()

