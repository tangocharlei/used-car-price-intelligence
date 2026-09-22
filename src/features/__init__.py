"""Feature engineering and modeling schema for fair-price regression."""

from src.features.feature_engineering import (
    CATEGORICAL_FEATURES,
    EXCLUDED_CONTEXT_COLUMNS,
    IDENTIFIER_COLUMNS,
    LEAKAGE_COLUMNS,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    build_model_matrix,
    engineer_features,
    excluded_columns_summary,
    get_feature_lists,
    resolve_reference_year,
)

__all__ = [
    "CATEGORICAL_FEATURES",
    "EXCLUDED_CONTEXT_COLUMNS",
    "IDENTIFIER_COLUMNS",
    "LEAKAGE_COLUMNS",
    "MODEL_FEATURES",
    "NUMERIC_FEATURES",
    "TARGET_COLUMN",
    "build_model_matrix",
    "engineer_features",
    "excluded_columns_summary",
    "get_feature_lists",
    "resolve_reference_year",
]
