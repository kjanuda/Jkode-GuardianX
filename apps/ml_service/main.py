from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    ROOT
    / "data"
    / "ml"
    / "models"
    / "rca_random_forest_v1.joblib"
)

METRICS_PATH = (
    ROOT
    / "data"
    / "ml"
    / "models"
    / "rca_random_forest_v1_metrics.json"
)


# ==========================================================
# Load model + metadata
# ==========================================================

if not MODEL_PATH.exists():
    raise RuntimeError(
        f"Model not found: {MODEL_PATH}"
    )

if not METRICS_PATH.exists():
    raise RuntimeError(
        f"Metrics not found: {METRICS_PATH}"
    )


model = joblib.load(
    MODEL_PATH
)

with METRICS_PATH.open(
    "r",
    encoding="utf-8",
) as file:
    metadata = json.load(file)


FEATURE_COLUMNS = metadata[
    "feature_columns"
]

MODEL_CLASSES = metadata[
    "classes"
]


# ==========================================================
# API
# ==========================================================

app = FastAPI(
    title="Guardian X ML RCA Service",
    version="1.0.0",
    description=(
        "Machine-learning RCA inference sidecar. "
        "ML output is advisory evidence only. "
        "The deterministic verifier remains authoritative."
    ),
)


# ==========================================================
# Request schema
# ==========================================================

class RCAMLFeatures(BaseModel):

    population_affected_ratio: float = Field(
        ge=0.0,
        le=1.0,
    )

    congestion_signature: float
    coverage_signature: float
    interference_signature: float
    outage_signature: float

    terrain_context: float
    vegetation_context: float
    historical_context: float

    affected_devices: int = Field(
        ge=0
    )

    healthy_devices: int = Field(
        ge=0
    )

    mean_los_blocked_pct: float

    mean_geo_vulnerability: float

    mean_fresnel_occupancy_pct: float

    mean_max_fresnel_intrusion_m: float

    mean_minimum_clearance_ratio: float

    mean_environmental_vulnerability: float

    mean_weather_score: float

    device_model_pattern: Literal[
        "DEVICE_MODEL_SPECIFIC_PATTERN",
        "NO_MODEL_SPECIFIC_PATTERN",
    ]


# ==========================================================
# Response schema
# ==========================================================

class ClassProbability(BaseModel):
    cause: str
    probability: float


class RCAMLPrediction(BaseModel):

    engine: str

    predicted_cause: str

    confidence: float

    probabilities: list[
        ClassProbability
    ]

    model_schema: str

    dataset_sha256: str | None

    manifest_sha256: str | None

    advisory_only: bool


# ==========================================================
# Health
# ==========================================================

@app.get(
    "/health"
)
def health():

    return {
        "status":
            "ok",

        "service":
            "guardianx-ml-rca",

        "model_loaded":
            True,

        "classes":
            MODEL_CLASSES,

        "feature_count":
            len(
                FEATURE_COLUMNS
            ),

        "schema_version":
            metadata.get(
                "schema_version"
            ),

        "dataset_sha256":
            metadata.get(
                "dataset_sha256"
            ),

        "manifest_sha256":
            metadata.get(
                "manifest_sha256"
            ),
    }


# ==========================================================
# Prediction
# ==========================================================

@app.post(
    "/predict",
    response_model=RCAMLPrediction,
)
def predict(
    payload: RCAMLFeatures,
):

    raw = payload.model_dump()

    missing = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in raw
    ]

    if missing:
        raise HTTPException(
            status_code=422,
            detail={
                "error":
                    "Missing model features",

                "missing":
                    missing,
            },
        )


    # Explicit allowlist and exact model column order.
    frame = pd.DataFrame(
        [
            {
                feature:
                    raw[feature]
                for feature
                in FEATURE_COLUMNS
            }
        ]
    )


    predicted = model.predict(
        frame
    )[0]


    probabilities_raw = (
        model.predict_proba(
            frame
        )[0]
    )


    classifier = (
        model.named_steps[
            "classifier"
        ]
    )

    classes = list(
        classifier.classes_
    )


    probability_map = {
        cause:
            float(probability)

        for (
            cause,
            probability,
        ) in zip(
            classes,
            probabilities_raw,
        )
    }


    confidence = float(
        probability_map[
            predicted
        ]
    )


    probabilities = [
        ClassProbability(
            cause=cause,
            probability=probability,
        )

        for (
            cause,
            probability,
        ) in sorted(
            probability_map.items(),
            key=lambda item:
                item[1],
            reverse=True,
        )
    ]


    return RCAMLPrediction(
        engine=
            "RCA_RANDOM_FOREST_V1",

        predicted_cause=
            predicted,

        confidence=
            confidence,

        probabilities=
            probabilities,

        model_schema=
            metadata.get(
                "schema_version",
                "UNKNOWN",
            ),

        dataset_sha256=
            metadata.get(
                "dataset_sha256"
            ),

        manifest_sha256=
            metadata.get(
                "manifest_sha256"
            ),

        advisory_only=
            True,
    )
