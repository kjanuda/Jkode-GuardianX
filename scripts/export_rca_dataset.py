import csv
import json
import sys

from collections import Counter
from pathlib import Path


ROOT = (
    Path(__file__).resolve()
    .parents[1]
)

API_ROOT = (
    ROOT
    / "apps"
    / "api"
)

if str(API_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(API_ROOT),
    )


from app.db.session import SessionLocal

from app.ml.rca_dataset import (
    build_rca_dataset,
)

from app.ml.provenance import (
    load_rca_provenance,
)


OUTPUT_DIR = (
    ROOT
    / "data"
    / "ml"
)

CSV_PATH = (
    OUTPUT_DIR
    / "rca_dataset.csv"
)

JSONL_PATH = (
    OUTPUT_DIR
    / "rca_dataset.jsonl"
)


def enrich_with_provenance(
    row: dict,
    provenance: dict,
) -> dict:
    case_id = int(
        row[
            "case_id"
        ]
    )

    meta = provenance.get(
        case_id
    )

    # -----------------------------------------
    # Never assume an unknown case is REAL.
    # -----------------------------------------

    if meta is None:
        return {
            **row,

            "data_origin":
                "UNKNOWN",

            "provenance_registered":
                False,

            "provenance_source":
                None,

            "scenario_name":
                None,

            "batch_id":
                None,

            "generation_group":
                None,

            "seed":
                None,

            "expected_domain":
                None,

            "expected_cause":
                None,

            "manifest_verified_domain":
                None,

            "manifest_verified_cause":
                None,

            "label_match":
                None,

            "probe_only":
                False,

            "split_group":
                None,

            # UNKNOWN provenance cannot enter
            # the ML training set.
            "training_eligible":
                False,
        }

    origin = meta.get(
        "data_origin",
        "UNKNOWN",
    )

    probe_only = bool(
        meta.get(
            "probe_only",
            False,
        )
    )

    label_match = meta.get(
        "label_match"
    )

    # Older probe manifest uses expected_family
    # and does not carry label_match.
    expected_cause = (
        meta.get(
            "expected_cause"
        )
        or meta.get(
            "expected_family"
        )
    )

    verified_cause = (
        meta.get(
            "verified_cause"
        )
    )

    verified_domain = (
        meta.get(
            "verified_domain"
        )
    )

    if (
        label_match is None
        and expected_cause
        and verified_cause
    ):
        # Probe-only information.
        # Useful for audit, not training.
        label_match = (
            expected_cause
            == verified_cause
        )

    synthetic_training_eligible = (
        origin == "SYNTHETIC"
        and meta.get(
            "provenance_source"
        )
        == "SYNTHETIC_MANIFEST"
        and row.get(
            "structured_verified"
        )
        is True
        and label_match
        is True
        and not probe_only
    )

    batch_id = meta.get(
        "batch_id"
    )

    scenario_name = meta.get(
        "scenario_name"
    )

    generation_group = meta.get(
        "generation_group"
    )

    split_group = (
        generation_group
        or (
            (
                f"{batch_id}:{scenario_name}"
            )
            if batch_id
            and scenario_name
            else None
        )
    )

    return {
        **row,

        "data_origin":
            origin,

        "provenance_registered":
            True,

        "provenance_source":
            meta.get(
                "provenance_source"
            ),

        "scenario_name":
            scenario_name,

        "batch_id":
            batch_id,

        "generation_group":
            generation_group,

        "seed":
            meta.get(
                "seed"
            ),

        "expected_domain":
            meta.get(
                "expected_domain"
            ),

        "expected_cause":
            expected_cause,

        "manifest_verified_domain":
            verified_domain,

        "manifest_verified_cause":
            verified_cause,

        "label_match":
            label_match,

        "probe_only":
            probe_only,

        "split_group":
            split_group,

        "training_eligible":
            synthetic_training_eligible,
    }


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    db = SessionLocal()

    try:
        raw_rows = (
            build_rca_dataset(
                db=db
            )
        )

    finally:
        db.close()

    provenance = (
        load_rca_provenance()
    )

    rows = [
        enrich_with_provenance(
            row,
            provenance,
        )
        for row in raw_rows
    ]

    print()
    print(
        "GUARDIAN X - RCA "
        "PROVENANCE DATASET EXPORT"
    )

    print("-" * 72)

    if not rows:
        print(
            "No verified RCA rows found."
        )
        return

    # Union of all fields keeps CSV stable.
    fieldnames = []

    seen_fields = set()

    for row in rows:
        for key in row:
            if key not in seen_fields:
                seen_fields.add(
                    key
                )

                fieldnames.append(
                    key
                )

    with CSV_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    with JSONL_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for row in rows:
            file.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                + "\n"
            )

    eligible = [
        row
        for row in rows
        if row[
            "training_eligible"
        ]
    ]

    origins = Counter(
        row[
            "data_origin"
        ]
        for row in rows
    )

    labels = Counter(
        row[
            "label_primary_cause"
        ]
        for row in eligible
    )

    print(
        f"Verified rows : {len(rows)}"
    )

    print(
        f"Training rows : {len(eligible)}"
    )

    print()
    print(
        "Origins:"
    )

    for origin, count in sorted(
        origins.items()
    ):
        print(
            f"  {origin:<12}: {count}"
        )

    print()
    print(
        "Eligible label balance:"
    )

    for label, count in sorted(
        labels.items()
    ):
        print(
            f"  {label:<32}: {count}"
        )

    print()
    print(
        f"CSV   : {CSV_PATH}"
    )

    print(
        f"JSONL : {JSONL_PATH}"
    )

    print()
    print(
        "RESULT: PASS"
    )


if __name__ == "__main__":
    main()