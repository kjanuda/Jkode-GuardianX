import sys
from copy import deepcopy
from pathlib import Path
from pprint import pprint


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
    verify_structured_rca,
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

    "verification_required":
        True,

    "verification_status":
        "PENDING",

    "verification_reasons":
        [],
}


def run_test(
    name: str,
    diagnosis: dict,
    expected_verified: bool,
    expected_reason: str | None = None,
) -> bool:
    result = verify_structured_rca(
        diagnosis=diagnosis
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
            and expected_reason
            in result[
                "verification_reasons"
            ]
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
    # 1. Valid terrain diagnosis
    # ---------------------------------

    valid = deepcopy(
        BASE_DIAGNOSIS
    )

    results.append(
        run_test(
            "VALID TERRAIN RCA",
            valid,
            True,
        )
    )


    # ---------------------------------
    # 2. Low confidence
    # ---------------------------------

    low_confidence = deepcopy(
        BASE_DIAGNOSIS
    )

    low_confidence[
        "confidence"
    ] = 0.30

    results.append(
        run_test(
            "LOW CONFIDENCE RCA",
            low_confidence,
            False,
            (
                "ROOT_CAUSE_"
                "CONFIDENCE_TOO_LOW"
            ),
        )
    )


    # ---------------------------------
    # 3. Unsupported weather claim
    # ---------------------------------

    weather = deepcopy(
        BASE_DIAGNOSIS
    )

    weather[
        "primary_root_cause"
    ] = "WEATHER_STRESS_POSSIBLE"

    weather[
        "conditions"
    ][
        "weather_causal_evidence"
    ] = False

    results.append(
        run_test(
            "UNSUPPORTED WEATHER RCA",
            weather,
            False,
            (
                "WEATHER_CAUSE_WITHOUT_"
                "WEATHER_EVIDENCE"
            ),
        )
    )


    # ---------------------------------
    # 4. Unsupported device claim
    # ---------------------------------

    device = deepcopy(
        BASE_DIAGNOSIS
    )

    device[
        "domain"
    ] = "DEVICE_DOMAIN"

    device[
        "primary_root_cause"
    ] = (
        "DEVICE_MODEL_OR_FIRMWARE"
    )

    device[
        "conditions"
    ][
        "device_specific_pattern"
    ] = False

    results.append(
        run_test(
            "UNSUPPORTED DEVICE RCA",
            device,
            False,
            (
                "DEVICE_CAUSE_WITHOUT_"
                "DEVICE_PATTERN"
            ),
        )
    )


    # ---------------------------------
    # 5. Unknown root cause
    # ---------------------------------

    unknown = deepcopy(
        BASE_DIAGNOSIS
    )

    unknown[
        "primary_root_cause"
    ] = "UNKNOWN"

    results.append(
        run_test(
            "UNKNOWN ROOT CAUSE",
            unknown,
            False,
            "NO_SUPPORTED_ROOT_CAUSE",
        )
    )


    print()
    print(
        "=" * 60
    )

    print(
        "VERIFIER TEST SUITE:",
        (
            "PASS"
            if all(results)
            else "FAIL"
        ),
    )


if __name__ == "__main__":
    main()