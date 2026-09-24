import sys
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


from app.rca.structured import (
    build_structured_rca,
)

from app.rca.verifier import (
    verify_structured_rca,
)


def main():
    hierarchy = {
        "incident_domain": {
            "cause":
                "COVERAGE_OR_PROPAGATION",

            "confidence":
                0.7268,
        },

        "primary_root_cause": {
            "cause":
                "TERRAIN_PROPAGATION_LIKELY",

            "confidence":
                0.6904,

            "confidence_label":
                "MODERATE",
        },

        "contributing_factors": [
            {
                "cause":
                    "VEGETATION_PROPAGATION_POSSIBLE",

                "confidence":
                    0.407,

                "confidence_label":
                    "LOW",
            }
        ],

        "conditions": {
            "persistent_degradation":
                True,

            "weather_causal_evidence":
                False,

            "device_specific_pattern":
                False,
        },
    }

    structured = (
        build_structured_rca(
            case_id=13,
            hierarchy=hierarchy,
        )
    )

    verified = (
        verify_structured_rca(
            diagnosis=structured
        )
    )

    print()
    print(
        "GUARDIAN X - STRUCTURED RCA TEST"
    )

    print(
        "-" * 70
    )

    pprint(
        verified
    )


if __name__ == "__main__":
    main()