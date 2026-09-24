import sys

from copy import deepcopy
from pathlib import Path
from pprint import pprint
from types import SimpleNamespace


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


from app.rca.verifier import (
    verify_structured_rca_with_evidence,
)


BASE_DIAGNOSIS = {
    "schema_version":
        "RCA_STRUCTURED_V1",

    "case_id":
        999,

    "domain":
        "PROPAGATION_DOMAIN",

    "incident_domain_cause":
        "COVERAGE_OR_PROPAGATION",

    "primary_root_cause":
        "TERRAIN_PROPAGATION_LIKELY",

    "confidence":
        0.70,

    "confidence_percent":
        70.0,

    "contributors":
        [],

    "conditions": {
        "persistent_degradation":
            False,

        "weather_causal_evidence":
            False,

        "device_specific_pattern":
            False,
    },
}


def terrain_evidence(
    *,
    gate=True,
    freshness=0.95,
    reliability=0.90,
    supports=True,
):
    return SimpleNamespace(
        evidence_key=(
            "CELL_TERRAIN_CONTEXT"
        ),

        support_score=1.0,

        reliability_score=(
            reliability
        ),

        freshness_score=(
            freshness
        ),

        specificity_score=0.95,

        gate_passed=gate,

        supports_causes=(
            [
                "TERRAIN_PROPAGATION_LIKELY"
            ]
            if supports
            else []
        ),

        contradicts_causes=[],
    )


def run_test(
    name,
    diagnosis,
    evidence_items,
    expected_verified,
    expected_reason=None,
):
    result = (
        verify_structured_rca_with_evidence(
            diagnosis=diagnosis,
            evidence_items=evidence_items,
        )
    )

    passed = (
        result[
            "verified"
        ]
        == expected_verified
    )

    if expected_reason:
        passed = (
            passed
            and any(
                expected_reason
                in reason
                for reason
                in result[
                    "verification_reasons"
                ]
            )
        )

    print()
    print(name)
    print("-" * 60)

    pprint(
        {
            "verified":
                result[
                    "verified"
                ],

            "status":
                result[
                    "verification_status"
                ],

            "reasons":
                result[
                    "verification_reasons"
                ],

            "result":
                (
                    "PASS"
                    if passed
                    else "FAIL"
                ),
        }
    )

    return passed


def main():
    results = []

    # ---------------------------------
    # 1. Valid evidence
    # ---------------------------------

    results.append(
        run_test(
            "VALID TERRAIN EVIDENCE",

            deepcopy(
                BASE_DIAGNOSIS
            ),

            [
                terrain_evidence()
            ],

            True,
        )
    )

    # ---------------------------------
    # 2. Missing evidence
    # ---------------------------------

    results.append(
        run_test(
            "MISSING TERRAIN EVIDENCE",

            deepcopy(
                BASE_DIAGNOSIS
            ),

            [],

            False,

            "REQUIRED_EVIDENCE_MISSING",
        )
    )

    # ---------------------------------
    # 3. Gate failed
    # ---------------------------------

    results.append(
        run_test(
            "FAILED TERRAIN GATE",

            deepcopy(
                BASE_DIAGNOSIS
            ),

            [
                terrain_evidence(
                    gate=False
                )
            ],

            False,

            "REQUIRED_EVIDENCE_GATE_FAILED",
        )
    )

    # ---------------------------------
    # 4. Stale evidence
    # ---------------------------------

    results.append(
        run_test(
            "STALE TERRAIN EVIDENCE",

            deepcopy(
                BASE_DIAGNOSIS
            ),

            [
                terrain_evidence(
                    freshness=0.20
                )
            ],

            False,

            "REQUIRED_EVIDENCE_STALE",
        )
    )

    # ---------------------------------
    # 5. Low reliability
    # ---------------------------------

    results.append(
        run_test(
            "LOW RELIABILITY EVIDENCE",

            deepcopy(
                BASE_DIAGNOSIS
            ),

            [
                terrain_evidence(
                    reliability=0.30
                )
            ],

            False,

            (
                "REQUIRED_EVIDENCE_"
                "LOW_RELIABILITY"
            ),
        )
    )

    # ---------------------------------
    # 6. Evidence does not support cause
    # ---------------------------------

    results.append(
        run_test(
            "UNSUPPORTED TERRAIN CLAIM",

            deepcopy(
                BASE_DIAGNOSIS
            ),

            [
                terrain_evidence(
                    supports=False
                )
            ],

            False,

            (
                "REQUIRED_EVIDENCE_"
                "DOES_NOT_SUPPORT_CAUSE"
            ),
        )
    )

    # ---------------------------------
    # 7. Domain mismatch
    # ---------------------------------

    wrong_domain = deepcopy(
        BASE_DIAGNOSIS
    )

    wrong_domain[
        "domain"
    ] = "NETWORK_DOMAIN"

    results.append(
        run_test(
            "DOMAIN ROOT-CAUSE MISMATCH",

            wrong_domain,

            [
                terrain_evidence()
            ],

            False,

            "DOMAIN_CAUSE_MISMATCH",
        )
    )

    print()
    print("=" * 60)

    print(
        "EVIDENCE VERIFIER SUITE:",
        (
            "PASS"
            if all(results)
            else "FAIL"
        ),
    )


if __name__ == "__main__":
    main()