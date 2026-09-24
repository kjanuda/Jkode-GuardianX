
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = (
    Path(__file__).resolve()
    .parents[4]
)

ML_DATA_DIR = (
    ROOT
    / "data"
    / "ml"
)

SYNTHETIC_MANIFEST = (
    ML_DATA_DIR
    / "synthetic_rca_manifest.jsonl"
)

SCENARIO_PROBE = (
    ML_DATA_DIR
    / "scenario_probe.json"
)


def load_rca_provenance() -> dict[int, dict[str, Any]]:
    """
    Return explicit provenance keyed by case_id.

    Unknown cases remain UNKNOWN elsewhere.
    Never infer REAL merely because a case
    lacks synthetic metadata.
    """

    provenance: dict[
        int,
        dict[str, Any],
    ] = {}

    # -----------------------------------------
    # Bulk verified synthetic cases
    # -----------------------------------------

    if SYNTHETIC_MANIFEST.exists():
        with SYNTHETIC_MANIFEST.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                item = json.loads(
                    line
                )

                case_id = int(
                    item[
                        "case_id"
                    ]
                )

                provenance[
                    case_id
                ] = {
                    **item,

                    "provenance_source":
                        "SYNTHETIC_MANIFEST",

                    "provenance_registered":
                        True,
                }

    # -----------------------------------------
    # Probe cases are explicitly synthetic,
    # but they are validation/probe rows only.
    # They should not become ML training rows.
    # -----------------------------------------

    if SCENARIO_PROBE.exists():
        data = json.loads(
            SCENARIO_PROBE.read_text(
                encoding="utf-8"
            )
        )

        for item in data.get(
            "results",
            [],
        ):
            case_id = int(
                item[
                    "case_id"
                ]
            )

            # Bulk manifest has higher priority.
            if case_id in provenance:
                continue

            provenance[
                case_id
            ] = {
                **item,

                "data_origin":
                    "SYNTHETIC",

                "provenance_source":
                    "SCENARIO_PROBE",

                "provenance_registered":
                    True,

                "probe_only":
                    True,
            }

    return provenance

