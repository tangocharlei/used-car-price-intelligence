"""
Feature engineering for fair-market used-vehicle price modeling.

Defines the modeling schema (target, allowed features, leakage exclusions),
engineers a small set of justified features, and returns an (X, y) matrix
suitable for the scikit-learn preprocessing pipeline in ``src.data.preprocess``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

TARGET_COLUMN = "sale_price"

# Explicit leakage: price derivatives, internal valuations, post-listing signals.
LEAKAGE_COLUMNS: tuple[str, ...] = (
    "emi_starts_from",
    "booking_down_pymnt",
    "broker_quote",
    "original_price",
    "times_viewed",
)

# Identifiers, near-unique fields, or redundant / ultra-high-cardinality keys.
IDENTIFIER_COLUMNS: tuple[str, ...] = (
    "car_name",  # redundant with make + model
    "ad_created_on",  # near-unique listing timestamp
    "rto",  # high-cardinality registration code
    "registered_city",  # high-cardinality; listing city retained instead
    "variant",  # ~900 levels; sparse and unstable for one-hot encoding
)

# Columns that encode listing operations or platform price judgment — not
# intrinsic vehicle attributes for a fair-market-value model.
EXCLUDED_CONTEXT_COLUMNS: tuple[str, ...] = (
    "car_rating",  # includes "overpriced" — platform judgment about price
    "reserved",  # transactional listing state
    "car_availability",  # inventory logistics state
    "is_hot",  # marketplace engagement flag
    "source",  # acquisition channel; not a vehicle attribute
)

# Raw columns required before engineering (subset of the full CSV).
REQUIRED_RAW_COLUMNS: tuple[str, ...] = (
    TARGET_COLUMN,
    "yr_mfr",
    "kms_run",
    "total_owners",
    "fuel_type",
    "body_type",
    "transmission",
    "make",
    "model",
    "city",
    "registered_state",
    "assured_buy",
    "warranty_avail",
    "fitness_certificate",
)

# Inference does not need the target; engineering still needs the vehicle fields.
INFERENCE_REQUIRED_COLUMNS: tuple[str, ...] = tuple(
    c for c in REQUIRED_RAW_COLUMNS if c != TARGET_COLUMN
)

# Final model feature names (after engineering).
NUMERIC_FEATURES: tuple[str, ...] = (
    "vehicle_age",
    "kms_run_log1p",
    "total_owners",
    "assured_buy",
    "warranty_avail",
    "fitness_certificate",
)

CATEGORICAL_FEATURES: tuple[str, ...] = (
    "fuel_type",
    "body_type",
    "transmission",
    "make",
    "model",
    "city",
    "registered_state",
)

MODEL_FEATURES: tuple[str, ...] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

CATEGORICAL_UNKNOWN = "Unknown"


def resolve_reference_year(reference_year: int | None = None) -> int:
    """
    Resolve the year used to compute ``vehicle_age``.

    Parameters
    ----------
    reference_year :
        If provided, use this fixed year (recommended when fitting a model so
        training and inference stay reproducible). If ``None``, use the current
        calendar year from the system clock.

    Notes
    -----
    Persist the ``reference_year`` used at training time (e.g. alongside the
    model artifact) and pass the same value at inference. Using a floating
    "today" year without pinning will shift ``vehicle_age`` over time.
    """
    if reference_year is None:
        return int(datetime.now().year)
    year = int(reference_year)
    if year < 1990 or year > 2100:
        raise ValueError(f"reference_year out of plausible range: {year}")
    return year


def add_vehicle_age(
    df: pd.DataFrame,
    *,
    reference_year: int | None = None,
    year_col: str = "yr_mfr",
) -> pd.DataFrame:
    """
    Add ``vehicle_age = reference_year - yr_mfr``.

    ``yr_mfr`` is retained in the returned frame for auditing but is **not**
    part of ``MODEL_FEATURES`` (collinear with ``vehicle_age``).
    """
    if year_col not in df.columns:
        raise KeyError(f"Required column missing for age engineering: '{year_col}'")

    out = df.copy()
    year = resolve_reference_year(reference_year)
    out["vehicle_age"] = year - pd.to_numeric(out[year_col], errors="coerce")
    out.attrs["reference_year"] = year
    return out


def add_log_kms(df: pd.DataFrame, *, kms_col: str = "kms_run") -> pd.DataFrame:
    """
    Add ``kms_run_log1p = log(1 + kms_run)``.

    Justified by the strong right skew and long mileage tail observed in EDA.
    Negative / non-numeric values become NaN and are left for median imputation.
    """
    if kms_col not in df.columns:
        raise KeyError(f"Required column missing for mileage engineering: '{kms_col}'")

    out = df.copy()
    kms = pd.to_numeric(out[kms_col], errors="coerce")
    kms = kms.where(kms >= 0)
    out["kms_run_log1p"] = np.log1p(kms)
    return out


def _normalize_binary(series: pd.Series) -> pd.Series:
    """Map common truthy/falsy representations to nullable 0/1 floats."""
    if pd.api.types.is_bool_dtype(series):
        return series.astype("float")

    mapping = {
        True: 1.0,
        False: 0.0,
        "True": 1.0,
        "False": 0.0,
        "true": 1.0,
        "false": 0.0,
        "1": 1.0,
        "0": 0.0,
        1: 1.0,
        0: 0.0,
        1.0: 1.0,
        0.0: 0.0,
    }
    return series.map(mapping).astype("float")


def _fill_categorical_unknown(
    df: pd.DataFrame, columns: Iterable[str]
) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            continue
        as_str = out[col].astype("string")
        as_str = as_str.str.strip()
        as_str = as_str.mask(as_str.isna() | (as_str == "") | (as_str.str.lower() == "nan"))
        out[col] = as_str.fillna(CATEGORICAL_UNKNOWN).astype("object")
    return out


def engineer_features(
    df: pd.DataFrame,
    *,
    reference_year: int | None = None,
    require_target: bool = False,
) -> pd.DataFrame:
    """
    Apply all feature-engineering steps and normalize model columns.

    Returns a copy; does not mutate the input or the raw CSV.

    Parameters
    ----------
    require_target :
        If ``True``, also require ``sale_price`` (training path). Inference
        callers should leave this ``False``.
    """
    if df is None or df.empty:
        raise ValueError("Cannot engineer features on an empty dataset.")

    required = REQUIRED_RAW_COLUMNS if require_target else INFERENCE_REQUIRED_COLUMNS
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns for feature engineering: {missing}")

    out = add_vehicle_age(df, reference_year=reference_year)
    out = add_log_kms(out)

    for col in ("assured_buy", "warranty_avail", "fitness_certificate"):
        out[col] = _normalize_binary(out[col])

    out["total_owners"] = pd.to_numeric(out["total_owners"], errors="coerce")
    out = _fill_categorical_unknown(out, CATEGORICAL_FEATURES)

    # Guard against impossible ages from bad year values.
    out.loc[out["vehicle_age"] < 0, "vehicle_age"] = np.nan

    return out


def get_feature_lists() -> tuple[list[str], list[str]]:
    """Return ``(numeric_features, categorical_features)`` for the preprocessor."""
    return list(NUMERIC_FEATURES), list(CATEGORICAL_FEATURES)


def build_model_matrix(
    df: pd.DataFrame,
    *,
    reference_year: int | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Build the modeling matrix.

    Parameters
    ----------
    df :
        Cleaned raw-style dataframe (valid ``sale_price``, deduplicated).
    reference_year :
        Optional pinned year for ``vehicle_age`` (see ``resolve_reference_year``).

    Returns
    -------
    X : pd.DataFrame
        Feature frame with ``MODEL_FEATURES`` only (leakage/identifiers excluded).
    y : pd.Series
        Target ``sale_price``.
    """
    if TARGET_COLUMN not in df.columns:
        raise KeyError(f"Target column '{TARGET_COLUMN}' is missing.")

    engineered = engineer_features(df, reference_year=reference_year, require_target=True)

    missing_feats = [c for c in MODEL_FEATURES if c not in engineered.columns]
    if missing_feats:
        raise KeyError(f"Engineered frame missing model features: {missing_feats}")

    X = engineered.loc[:, list(MODEL_FEATURES)].copy()
    y = pd.to_numeric(engineered[TARGET_COLUMN], errors="coerce")

    if y.isna().any():
        raise ValueError("Target contains non-numeric or null values after cleaning.")

    if len(X) == 0:
        raise ValueError("Feature matrix X is empty after engineering.")

    X.attrs["reference_year"] = engineered.attrs.get("reference_year")
    return X, y.astype(float)


def excluded_columns_summary() -> dict[str, tuple[str, ...]]:
    """Document columns intentionally kept out of the fair-price feature set."""
    return {
        "leakage": LEAKAGE_COLUMNS,
        "identifiers": IDENTIFIER_COLUMNS,
        "excluded_context": EXCLUDED_CONTEXT_COLUMNS,
        "replaced_by_engineering": ("yr_mfr", "kms_run"),
    }
