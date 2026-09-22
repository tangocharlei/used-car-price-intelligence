"""
Data loading, cleaning, and reusable scikit-learn preprocessing.

The fair-market-value feature schema and engineering live in
``src.features.feature_engineering``. This module:

1. Loads the raw CSV via a project-root-relative path (never mutates it).
2. Drops invalid targets and exact duplicates.
3. Builds ``(X, y)`` through feature engineering.
4. Constructs a ``ColumnTransformer`` for numeric / categorical pipelines
   that can be ``fit`` during training and ``transform`` during inference.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features.feature_engineering import (
    CATEGORICAL_FEATURES,
    CATEGORICAL_UNKNOWN,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    REQUIRED_RAW_COLUMNS,
    TARGET_COLUMN,
    build_model_matrix,
    get_feature_lists,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_FILENAME = "Used_Car_Price_Prediction.csv"


def get_project_root() -> Path:
    """
    Resolve the repository root from this file location.

    ``src/data/preprocess.py`` → parents[0]=data, [1]=src, [2]=project root.
    """
    return Path(__file__).resolve().parents[2]


def get_raw_data_path(filename: str = RAW_FILENAME) -> Path:
    """Return ``<project_root>/data/raw/<filename>``."""
    return get_project_root() / "data" / "raw" / filename


# ---------------------------------------------------------------------------
# Validation & loading
# ---------------------------------------------------------------------------


def validate_raw_dataframe(df: pd.DataFrame) -> None:
    """Defensive checks before cleaning / engineering."""
    if df is None:
        raise ValueError("Dataset is None.")
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(df)!r}.")
    if df.empty:
        raise ValueError("Dataset is empty.")
    if TARGET_COLUMN not in df.columns:
        raise KeyError(
            f"Target column '{TARGET_COLUMN}' is missing from the dataset. "
            f"Available columns: {list(df.columns)}"
        )
    missing = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Required columns missing from dataset: {missing}")


def load_raw_data(path: str | Path | None = None) -> pd.DataFrame:
    """
    Load the raw used-vehicle CSV.

    Parameters
    ----------
    path :
        Optional override. Defaults to ``data/raw/Used_Car_Price_Prediction.csv``
        under the project root.

    Returns
    -------
    pd.DataFrame
        A copy of the raw data. The file on disk is never modified.
    """
    data_path = Path(path) if path is not None else get_raw_data_path()
    if not data_path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    validate_raw_dataframe(df)
    return df.copy()


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean listing data for modeling.

    - Drops rows with non-positive / non-numeric ``sale_price``
    - Removes exact duplicate rows
    - Does **not** write back to ``data/raw/``
    - Leaves numeric imputation and categorical ``Unknown`` filling to
      feature engineering + the sklearn pipeline (fit/transform safe)
    """
    validate_raw_dataframe(df)

    out = df.copy()
    out[TARGET_COLUMN] = pd.to_numeric(out[TARGET_COLUMN], errors="coerce")
    before = len(out)
    out = out.loc[out[TARGET_COLUMN].notna() & (out[TARGET_COLUMN] > 0)].copy()
    dropped_price = before - len(out)

    before_dupes = len(out)
    out = out.drop_duplicates().reset_index(drop=True)
    dropped_dupes = before_dupes - len(out)

    if out.empty:
        raise ValueError(
            "Cleaning removed all rows. Check sale_price validity and duplicates."
        )

    out.attrs["rows_dropped_invalid_price"] = int(dropped_price)
    out.attrs["rows_dropped_duplicates"] = int(dropped_dupes)
    return out


# ---------------------------------------------------------------------------
# Preprocessing pipeline (sklearn)
# ---------------------------------------------------------------------------


def build_preprocessor(
    numeric_features: list[str] | None = None,
    categorical_features: list[str] | None = None,
    *,
    scale_numeric: bool = True,
) -> ColumnTransformer:
    """
    Build an unfitted ColumnTransformer for fair-price modeling.

    Numerical pipeline
        Median imputation → optional StandardScaler
        (skewed mileage is already ``log1p``-transformed in feature engineering).
        Set ``scale_numeric=False`` for tree-based models that do not need scaling.

    Categorical pipeline
        Constant ``Unknown`` imputation → OneHotEncoder(handle_unknown=\"ignore\")

    Fit once on training data and reuse ``transform`` for validation / Streamlit
    inference so encoding vocabulary and impute statistics stay consistent.
    """
    num_cols = list(numeric_features) if numeric_features is not None else list(NUMERIC_FEATURES)
    cat_cols = (
        list(categorical_features)
        if categorical_features is not None
        else list(CATEGORICAL_FEATURES)
    )

    if not num_cols and not cat_cols:
        raise ValueError("Preprocessor requires at least one numeric or categorical column.")

    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    numeric_pipeline = Pipeline(steps=numeric_steps)

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="constant", fill_value=CATEGORICAL_UNKNOWN),
            ),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, num_cols),
            ("cat", categorical_pipeline, cat_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def prepare_xy(
    df: pd.DataFrame | None = None,
    *,
    path: str | Path | None = None,
    reference_year: int | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    End-to-end: load (optional) → clean → engineer → return ``(X, y)``.

    Parameters
    ----------
    df :
        Optional in-memory dataframe. If ``None``, load from ``path`` / default raw CSV.
    path :
        Optional raw CSV path override.
    reference_year :
        Pinned year for ``vehicle_age``. Pass the same value at inference as at
        training for reproducibility. ``None`` uses the current calendar year.

    Returns
    -------
    X, y
        Clean feature frame (model columns only) and ``sale_price`` target.
    """
    if df is None:
        raw = load_raw_data(path=path)
    else:
        validate_raw_dataframe(df)
        raw = df.copy()

    cleaned = clean_data(raw)
    X, y = build_model_matrix(cleaned, reference_year=reference_year)

    if X.empty or len(y) == 0:
        raise ValueError("Prepared feature matrix or target is empty.")
    if len(X) != len(y):
        raise ValueError(f"X/y length mismatch: {len(X)} vs {len(y)}")

    return X, y


def prepare_preprocessor(
    X: pd.DataFrame | None = None,
    *,
    scale_numeric: bool = True,
) -> ColumnTransformer:
    """
    Construct a preprocessor aligned to the standard model feature lists.

    If ``X`` is provided, verifies it contains the expected columns (order is
    enforced by the ColumnTransformer feature lists).
    """
    if X is not None:
        missing = [c for c in MODEL_FEATURES if c not in X.columns]
        if missing:
            raise KeyError(f"X is missing expected model features: {missing}")
        if X.empty:
            raise ValueError("Cannot build preprocessor from an empty feature frame.")

    numeric_features, categorical_features = get_feature_lists()
    return build_preprocessor(
        numeric_features,
        categorical_features,
        scale_numeric=scale_numeric,
    )


def get_preprocessing_bundle(
    *,
    path: str | Path | None = None,
    reference_year: int | None = None,
) -> dict[str, Any]:
    """
    Convenience bundle for upcoming training / inference code.

    Returns
    -------
    dict with keys:
        ``X``, ``y``, ``preprocessor`` (unfitted), ``reference_year``,
        ``numeric_features``, ``categorical_features``
    """
    X, y = prepare_xy(path=path, reference_year=reference_year)
    preprocessor = prepare_preprocessor(X)
    resolved_year = X.attrs.get("reference_year", reference_year)

    return {
        "X": X,
        "y": y,
        "preprocessor": preprocessor,
        "reference_year": resolved_year,
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "model_features": list(MODEL_FEATURES),
    }
