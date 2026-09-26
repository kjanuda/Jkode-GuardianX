from __future__ import annotations

import json
import os
import socket

from urllib.error import (
    HTTPError,
    URLError,
)

from urllib.request import (
    ProxyHandler,
    Request,
    build_opener,
)

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.ml.features import (
    build_case_ml_features,
    validate_ml_features,
)

from app.models.rca import (
    RCACase,
    RCAPrediction,
)


ML_ENGINE_TYPE = (
    "RCA_RANDOM_FOREST_V1"
)

ML_OUTPUT_SCHEMA = (
    "RCA_ML_PREDICTION_V1"
)

EXPECTED_MODEL_SCHEMA = (
    "GUARDIAN_X_RCA_ML_V1"
)

ML_SERVICE_URL = (
    os.getenv(
        "GUARDIANX_ML_URL",
        "http://127.0.0.1:8100",
    )
    .rstrip("/")
)

ML_TIMEOUT_SECONDS = 5.0


ALLOWED_CAUSES = {
    "CONGESTION_OR_BACKHAUL",
    "COVERAGE_OR_PROPAGATION",
    "DEVICE_MODEL_OR_FIRMWARE",
    "INTERFERENCE",
    "OUTAGE",
    "TERRAIN_PROPAGATION_LIKELY",
}


class MLRCAServiceError(
    RuntimeError
):
    pass


def request_ml_prediction(
    *,
    features: dict,
) -> dict:

    request = Request(
        url=(
            f"{ML_SERVICE_URL}"
            "/predict"
        ),
        data=json.dumps(
            features
        ).encode(
            "utf-8"
        ),
        headers={
            "Content-Type":
                "application/json",
        },
        method="POST",
    )

    try:
        # --------------------------------------------------
        # Direct connection.
        #
        # ProxyHandler({}) disables environment/system
        # proxy configuration so localhost requests go
        # directly to the ML sidecar.
        # --------------------------------------------------

        opener = build_opener(
            ProxyHandler({})
        )

        with opener.open(
            request,
            timeout=ML_TIMEOUT_SECONDS,
        ) as response:

            body = response.read()

    except HTTPError as exc:

        try:
            detail = (
                exc.read()
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

        except Exception:
            detail = str(
                exc
            )

        raise MLRCAServiceError(
            "ML service returned "
            f"HTTP {exc.code}: "
            f"{detail}"
        ) from exc

    except (
        URLError,
        TimeoutError,
        socket.timeout,
        OSError,
    ) as exc:

        raise MLRCAServiceError(
            "ML service unavailable: "
            f"{exc}"
        ) from exc


    try:
        result = json.loads(
            body.decode(
                "utf-8"
            )
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:

        raise MLRCAServiceError(
            "ML service returned "
            "invalid JSON"
        ) from exc


    predicted_cause = (
        result.get(
            "predicted_cause"
        )
    )

    confidence = result.get(
        "confidence"
    )

    model_schema = result.get(
        "model_schema"
    )

    advisory_only = result.get(
        "advisory_only"
    )


    if (
        predicted_cause
        not in ALLOWED_CAUSES
    ):
        raise MLRCAServiceError(
            "ML service returned "
            "unsupported cause"
        )


    if not isinstance(
        confidence,
        (int, float),
    ):
        raise MLRCAServiceError(
            "ML service returned "
            "invalid confidence"
        )


    if not (
        0.0
        <= float(confidence)
        <= 1.0
    ):
        raise MLRCAServiceError(
            "ML confidence outside "
            "valid range"
        )


    if (
        model_schema
        != EXPECTED_MODEL_SCHEMA
    ):
        raise MLRCAServiceError(
            "ML model schema mismatch: "
            f"{model_schema}"
        )


    if advisory_only is not True:
        raise MLRCAServiceError(
            "ML service violated "
            "advisory-only contract"
        )


    return result


def run_case_ml_prediction(
    *,
    db: Session,
    case_id: int,
) -> dict:

    case = db.get(
        RCACase,
        case_id,
    )

    if case is None:
        raise ValueError(
            "RCA case not found"
        )


    # ------------------------------------------------------
    # Same feature extraction used by dataset construction.
    # ------------------------------------------------------

    features = (
        build_case_ml_features(
            db=db,
            case_id=case_id,
        )
    )

    validate_ml_features(
        features
    )


    # ------------------------------------------------------
    # ML inference
    #
    # No DB write occurs until a valid sidecar response
    # has been received and validated.
    # ------------------------------------------------------

    ml_result = (
        request_ml_prediction(
            features=features
        )
    )


    predicted_cause = (
        ml_result[
            "predicted_cause"
        ]
    )

    confidence = float(
        ml_result[
            "confidence"
        ]
    )


    output = {
        "schema_version":
            ML_OUTPUT_SCHEMA,

        "engine_type":
            ML_ENGINE_TYPE,

        "case_id":
            case_id,

        "predicted_cause":
            predicted_cause,

        "confidence":
            confidence,

        "probabilities":
            ml_result.get(
                "probabilities",
                [],
            ),

        "model_schema":
            ml_result.get(
                "model_schema"
            ),

        "dataset_sha256":
            ml_result.get(
                "dataset_sha256"
            ),

        "manifest_sha256":
            ml_result.get(
                "manifest_sha256"
            ),

        "advisory_only":
            True,

        # Audit snapshot.
        # These are only model features,
        # never label/provenance metadata.
        "features":
            features,
    }


    # ------------------------------------------------------
    # Idempotent ML persistence
    # ------------------------------------------------------

    db.execute(
        delete(
            RCAPrediction
        ).where(
            RCAPrediction.case_id
            == case_id,

            RCAPrediction.engine_type
            == ML_ENGINE_TYPE,
        )
    )


    prediction = (
        RCAPrediction(
            case_id=case_id,

            engine_type=(
                ML_ENGINE_TYPE
            ),

            primary_cause=(
                predicted_cause
            ),

            confidence=confidence,

            rank=1,

            output_json=output,

            verifier_status=(
                "ADVISORY"
            ),

            verifier_reason=(
                "ML prediction is advisory "
                "only; deterministic verifier "
                "remains authoritative."
            ),
        )
    )


    try:
        db.add(
            prediction
        )

        db.flush()

        prediction_id = (
            prediction.id
        )

        db.commit()

    except Exception:
        db.rollback()
        raise


    return {
        "prediction_id":
            prediction_id,

        "case_id":
            case_id,

        "engine_type":
            ML_ENGINE_TYPE,

        "predicted_cause":
            predicted_cause,

        "confidence":
            confidence,

        "probabilities":
            output[
                "probabilities"
            ],

        "model_schema":
            output[
                "model_schema"
            ],

        "dataset_sha256":
            output[
                "dataset_sha256"
            ],

        "manifest_sha256":
            output[
                "manifest_sha256"
            ],

        "advisory_only":
            True,
    }