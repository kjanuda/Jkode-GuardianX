from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ==========================================================
# Project paths
# ==========================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    ROOT
    / "data"
    / "ml"
    / "rca_dataset.csv"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "ml"
    / "synthetic_rca_manifest.jsonl"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "ml"
    / "models"
)

MODEL_PATH = (
    OUTPUT_DIR
    / "rca_random_forest_v1.joblib"
)

METRICS_PATH = (
    OUTPUT_DIR
    / "rca_random_forest_v1_metrics.json"
)


# ==========================================================
# Explicit safe feature allowlist
# ==========================================================

NUMERIC_FEATURES = [
    "population_affected_ratio",
    "congestion_signature",
    "coverage_signature",
    "interference_signature",
    "outage_signature",
    "terrain_context",
    "vegetation_context",
    "historical_context",
    "affected_devices",
    "healthy_devices",
    "mean_los_blocked_pct",
    "mean_geo_vulnerability",
    "mean_fresnel_occupancy_pct",
    "mean_max_fresnel_intrusion_m",
    "mean_minimum_clearance_ratio",
    "mean_environmental_vulnerability",
    "mean_weather_score",
]

CATEGORICAL_FEATURES = [
    "device_model_pattern",
]

FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

TARGET_COLUMN = "label_primary_cause"

GROUP_COLUMN = "split_group"


# ==========================================================
# File hashing
# ==========================================================

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


# ==========================================================
# Data
# ==========================================================

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}"
    )

if not MANIFEST_PATH.exists():
    raise FileNotFoundError(
        f"Manifest not found: {MANIFEST_PATH}"
    )

df = pd.read_csv(DATA_PATH)

if "training_eligible" not in df.columns:
    raise RuntimeError(
        "Missing required column: training_eligible"
    )

eligible = (
    df["training_eligible"]
    .astype(str)
    .str.lower()
    .eq("true")
)

df = df[eligible].copy()

if len(df) == 0:
    raise RuntimeError(
        "No training-eligible rows found."
    )


# ==========================================================
# Hard leakage checks
# ==========================================================

FORBIDDEN_FEATURES = {
    "expected_cause",
    "expected_domain",
    "manifest_verified_cause",
    "manifest_verified_domain",
    "verified_cause",
    "label_primary_cause",
    "label_domain",
    "label_confidence",
    "scenario_name",
    "profile",
    "coverage_subtype",
    "target_model",
    "seed",
    "batch_id",
    "generation_group",
    "split_group",
    "case_id",
    "case_uuid",
}

leaked = (
    set(FEATURE_COLUMNS)
    & FORBIDDEN_FEATURES
)

if leaked:
    raise RuntimeError(
        "Forbidden leakage features detected: "
        + ", ".join(
            sorted(leaked)
        )
    )


# ==========================================================
# Required column validation
# ==========================================================

missing_columns = [
    column
    for column in (
        FEATURE_COLUMNS
        + [
            TARGET_COLUMN,
            GROUP_COLUMN,
        ]
    )
    if column not in df.columns
]

if missing_columns:
    raise RuntimeError(
        "Missing required columns: "
        + ", ".join(
            missing_columns
        )
    )


# ==========================================================
# Feature / target split
# ==========================================================

X = df[
    FEATURE_COLUMNS
].copy()

y = df[
    TARGET_COLUMN
].copy()

groups = df[
    GROUP_COLUMN
].copy()


# ==========================================================
# Additional data validation
# ==========================================================

if y.isna().any():
    raise RuntimeError(
        "Target column contains missing values: "
        f"{TARGET_COLUMN}"
    )

if groups.isna().any():
    raise RuntimeError(
        "Group column contains missing values: "
        f"{GROUP_COLUMN}"
    )

if y.nunique() < 2:
    raise RuntimeError(
        "At least two target classes are required."
    )

if groups.nunique() < 3:
    raise RuntimeError(
        "At least 3 unique groups are required "
        "for 3-fold group-aware cross-validation."
    )


# ==========================================================
# Preprocessing
# ==========================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="median"
            ),
        ),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            ),
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            NUMERIC_FEATURES,
        ),
        (
            "categorical",
            categorical_pipeline,
            CATEGORICAL_FEATURES,
        ),
    ]
)


# ==========================================================
# Model
# ==========================================================

def build_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )


# ==========================================================
# Group-aware CV
# ==========================================================

cv = StratifiedGroupKFold(
    n_splits=3,
    shuffle=True,
    random_state=42,
)

fold_results = []

all_true = []
all_pred = []


# ==========================================================
# Training summary
# ==========================================================

print()
print("GUARDIAN X - RCA ML BASELINE")
print("=" * 72)

print(
    f"Project root   : {ROOT}"
)

print(
    f"Dataset        : {DATA_PATH}"
)

print(
    f"Manifest       : {MANIFEST_PATH}"
)

print(
    f"Training rows  : {len(df)}"
)

print(
    f"Feature count  : {len(FEATURE_COLUMNS)}"
)

print(
    f"Group count    : {groups.nunique()}"
)

print(
    f"Class count    : {y.nunique()}"
)

print(
    f"Target         : {TARGET_COLUMN}"
)

print(
    f"Group column   : {GROUP_COLUMN}"
)

print("=" * 72)


# ==========================================================
# Cross-validation
# ==========================================================

for (
    fold_index,
    (
        train_index,
        test_index,
    ),
) in enumerate(
    cv.split(
        X,
        y,
        groups,
    ),
    start=1,
):

    X_train = X.iloc[
        train_index
    ]

    X_test = X.iloc[
        test_index
    ]

    y_train = y.iloc[
        train_index
    ]

    y_test = y.iloc[
        test_index
    ]

    train_groups = set(
        groups.iloc[
            train_index
        ]
    )

    test_groups = set(
        groups.iloc[
            test_index
        ]
    )

    overlap = (
        train_groups
        & test_groups
    )

    if overlap:
        raise RuntimeError(
            "GROUP LEAKAGE DETECTED: "
            + ", ".join(
                sorted(
                    map(
                        str,
                        overlap,
                    )
                )
            )
        )

    model = build_model()

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    balanced_accuracy = (
        balanced_accuracy_score(
            y_test,
            predictions,
        )
    )

    fold_results.append(
        {
            "fold": fold_index,
            "train_rows": len(train_index),
            "test_rows": len(test_index),
            "train_groups": len(train_groups),
            "test_groups": len(test_groups),
            "accuracy": float(
                accuracy
            ),
            "balanced_accuracy": float(
                balanced_accuracy
            ),
        }
    )

    all_true.extend(
        y_test.tolist()
    )

    all_pred.extend(
        predictions.tolist()
    )

    print()
    print(
        f"FOLD {fold_index}"
    )

    print(
        "-" * 72
    )

    print(
        f"Train rows        : "
        f"{len(train_index)}"
    )

    print(
        f"Test rows         : "
        f"{len(test_index)}"
    )

    print(
        f"Train groups      : "
        f"{len(train_groups)}"
    )

    print(
        f"Test groups       : "
        f"{len(test_groups)}"
    )

    print(
        f"Group overlap     : "
        f"{len(overlap)}"
    )

    print(
        f"Accuracy          : "
        f"{accuracy:.4f}"
    )

    print(
        f"Balanced accuracy : "
        f"{balanced_accuracy:.4f}"
    )


# ==========================================================
# Overall CV metrics
# ==========================================================

labels = sorted(
    y.unique()
)

report = classification_report(
    all_true,
    all_pred,
    labels=labels,
    output_dict=True,
    zero_division=0,
)

matrix = confusion_matrix(
    all_true,
    all_pred,
    labels=labels,
)

overall_accuracy = accuracy_score(
    all_true,
    all_pred,
)

overall_balanced_accuracy = (
    balanced_accuracy_score(
        all_true,
        all_pred,
    )
)


# ==========================================================
# Print overall results
# ==========================================================

print()
print("=" * 72)
print("OVERALL GROUP-AWARE CV")
print("=" * 72)

print(
    f"Accuracy          : "
    f"{overall_accuracy:.4f}"
)

print(
    f"Balanced accuracy : "
    f"{overall_balanced_accuracy:.4f}"
)

print()
print("CLASSIFICATION REPORT")

print(
    classification_report(
        all_true,
        all_pred,
        labels=labels,
        zero_division=0,
    )
)

print(
    "CONFUSION MATRIX"
)

matrix_df = pd.DataFrame(
    matrix,
    index=labels,
    columns=labels,
)

print(
    matrix_df.to_string()
)


# ==========================================================
# Final model
#
# Train on all eligible synthetic data after CV.
# This artifact is for API integration.
# CV metrics remain the evaluation evidence.
# ==========================================================

final_model = build_model()

final_model.fit(
    X,
    y,
)


# ==========================================================
# Save artifacts
# ==========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

joblib.dump(
    final_model,
    MODEL_PATH,
)


# ==========================================================
# File integrity hashes
# ==========================================================

dataset_sha256 = sha256_file(
    DATA_PATH
)

manifest_sha256 = sha256_file(
    MANIFEST_PATH
)


# ==========================================================
# Metrics artifact
# ==========================================================

metrics = {
    "schema_version":
        "GUARDIAN_X_RCA_ML_V1",

    "evaluation_type":
        "SYNTHETIC_GROUP_AWARE_CV",

    "training_rows":
        int(len(df)),

    "group_count":
        int(groups.nunique()),

    "classes":
        labels,

    "feature_columns":
        FEATURE_COLUMNS,

    "numeric_features":
        NUMERIC_FEATURES,

    "categorical_features":
        CATEGORICAL_FEATURES,

    "cv_folds":
        3,

    "fold_results":
        fold_results,

    "overall_accuracy":
        float(
            overall_accuracy
        ),

    "overall_balanced_accuracy":
        float(
            overall_balanced_accuracy
        ),

    "classification_report":
        report,

    "confusion_matrix": {
        "labels":
            labels,

        "matrix":
            matrix.tolist(),
    },

    "dataset_sha256":
        dataset_sha256,

    "manifest_sha256":
        manifest_sha256,

    "warning": (
        "Metrics are measured on controlled "
        "synthetic verified RCA cases using "
        "group-aware cross-validation. They "
        "must not be represented as real-world "
        "production accuracy."
    ),
}


with METRICS_PATH.open(
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        metrics,
        file,
        indent=2,
    )


# ==========================================================
# Final output
# ==========================================================

print()
print("=" * 72)

print(
    f"MODEL SAVED   : "
    f"{MODEL_PATH}"
)

print(
    f"METRICS SAVED : "
    f"{METRICS_PATH}"
)

print()
print(
    f"DATASET SHA256 : "
    f"{dataset_sha256}"
)

print(
    f"MANIFEST SHA256: "
    f"{manifest_sha256}"
)

print()
print("RESULT: PASS")