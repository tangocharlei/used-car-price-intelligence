"""
Train and compare regression models for used-vehicle fair market value.

Runnable from the project root::

    python -m src.models.train_models

Fits preprocessing only on training folds, evaluates on original-scale
``sale_price``, selects the best model by MAE, then refits on the full
cleaned dataset and writes artifacts under ``models/`` and ``reports/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from src.data.preprocess import get_project_root, prepare_preprocessor, prepare_xy
from src.features.feature_engineering import MODEL_FEATURES, resolve_reference_year
from src.models.evaluate_models import (
    build_comparison_frame,
    evaluate_model,
    print_best_result,
    save_comparison_csv,
    select_best_result,
)

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET_STRATEGIES: tuple[str, ...] = ("original", "log1p")

# Models that benefit from numeric StandardScaler inside the ColumnTransformer.
SCALED_MODELS: frozenset[str] = frozenset({"DummyRegressor", "Ridge"})


def get_models_dir() -> Path:
    """Return ``<project_root>/models`` (created if missing)."""
    path = get_project_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_reports_dir() -> Path:
    """Return ``<project_root>/reports`` (created if missing)."""
    path = get_project_root() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_estimator_registry() -> dict[str, Any]:
    """
    Estimators with reasonable defaults (no extensive tuning).

    Returns unfitted estimator instances keyed by display name.
    """
    return {
        "DummyRegressor": DummyRegressor(strategy="mean"),
        "Ridge": Ridge(alpha=1.0),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "XGBRegressor": XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }


def build_model_pipeline(model_name: str, estimator: Any) -> Pipeline:
    """
    Wrap preprocessing + estimator in a single sklearn Pipeline.

    Linear / dummy models use numeric scaling; tree models share the same
    categorical one-hot path but skip StandardScaler.
    """
    scale_numeric = model_name in SCALED_MODELS
    preprocessor = prepare_preprocessor(scale_numeric=scale_numeric)
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", estimator),
        ]
    )


def transform_target_for_training(
    y: pd.Series | np.ndarray,
    target_strategy: str,
) -> np.ndarray:
    """Apply the training-time target transform."""
    values = np.asarray(y, dtype=float)
    if target_strategy == "original":
        return values
    if target_strategy == "log1p":
        if np.any(values <= 0):
            raise ValueError("log1p target requires strictly positive sale_price values.")
        return np.log1p(values)
    raise ValueError(f"Unknown target_strategy: {target_strategy!r}")


def load_modeling_data(
    *,
    reference_year: int | None = None,
) -> tuple[pd.DataFrame, pd.Series, int]:
    """Load cleaned ``(X, y)`` via the shared preprocessing pipeline."""
    year = resolve_reference_year(reference_year)
    X, y = prepare_xy(reference_year=year)
    return X, y, year


def split_train_test(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Reproducible 80/20 split."""
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )


def run_model_comparison(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> pd.DataFrame:
    """
    Fit every model × target strategy on the training fold only.

    The sklearn Pipeline fits the ColumnTransformer exclusively on ``X_train``
    during ``pipeline.fit``, so test data never leaks into imputation /
    encoding / scaling statistics.
    """
    rows: list[dict[str, Any]] = []
    registry = get_estimator_registry()

    for model_name, estimator in registry.items():
        for target_strategy in TARGET_STRATEGIES:
            print(f"Training {model_name} | target={target_strategy} ...")
            pipeline = build_model_pipeline(model_name, estimator)
            y_train_fit = transform_target_for_training(y_train, target_strategy)
            pipeline.fit(X_train, y_train_fit)

            result = evaluate_model(
                pipeline,
                X_test,
                y_test,
                model_name=model_name,
                target_strategy=target_strategy,
            )
            rows.append(result)
            print(
                f"  MAE={result['MAE']:,.2f} | "
                f"RMSE={result['RMSE']:,.2f} | "
                f"R2={result['R2']:.4f}"
            )

    return build_comparison_frame(rows)


def retrain_final_pipeline(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    model_name: str,
    target_strategy: str,
) -> Pipeline:
    """Refit the winning configuration on the full cleaned dataset."""
    registry = get_estimator_registry()
    if model_name not in registry:
        raise KeyError(f"Unknown model_name for final retrain: {model_name}")

    pipeline = build_model_pipeline(model_name, registry[model_name])
    y_fit = transform_target_for_training(y, target_strategy)
    pipeline.fit(X, y_fit)
    return pipeline


def save_final_artifacts(
    pipeline: Pipeline,
    *,
    model_name: str,
    target_strategy: str,
    reference_year: int,
    metrics: dict[str, float],
    feature_list: list[str],
) -> tuple[Path, Path]:
    """Persist ``final_model.joblib`` and ``model_metadata.json``."""
    models_dir = get_models_dir()
    model_path = models_dir / "final_model.joblib"
    meta_path = models_dir / "model_metadata.json"

    joblib.dump(pipeline, model_path)

    metadata = {
        "selected_model_name": model_name,
        "target_strategy": target_strategy,
        "reference_year": int(reference_year),
        "feature_list": feature_list,
        "evaluation_metrics": {
            "MAE": float(metrics["MAE"]),
            "RMSE": float(metrics["RMSE"]),
            "R2": float(metrics["R2"]),
        },
        "train_test_split": {
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
        },
        "scale_numeric": model_name in SCALED_MODELS,
    }
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return model_path, meta_path


def train_and_evaluate(
    *,
    reference_year: int | None = None,
) -> dict[str, Any]:
    """
    Full training workflow: compare models, select winner, refit, save artifacts.
    """
    X, y, year = load_modeling_data(reference_year=reference_year)
    print(f"Loaded modeling data: X={X.shape}, y={y.shape}, reference_year={year}")

    X_train, X_test, y_train, y_test = split_train_test(X, y)
    print(f"Train size={len(X_train)}, Test size={len(X_test)}")

    comparison = run_model_comparison(X_train, X_test, y_train, y_test)
    comparison_path = save_comparison_csv(
        comparison, get_reports_dir() / "model_comparison.csv"
    )
    print(f"\nSaved comparison table -> {comparison_path}")
    print(comparison.to_string(index=False))

    best = select_best_result(comparison)
    print_best_result(best)

    final_pipeline = retrain_final_pipeline(
        X,
        y,
        model_name=str(best["model_name"]),
        target_strategy=str(best["target_strategy"]),
    )
    model_path, meta_path = save_final_artifacts(
        final_pipeline,
        model_name=str(best["model_name"]),
        target_strategy=str(best["target_strategy"]),
        reference_year=year,
        metrics={
            "MAE": float(best["MAE"]),
            "RMSE": float(best["RMSE"]),
            "R2": float(best["R2"]),
        },
        feature_list=list(MODEL_FEATURES),
    )
    print(f"Saved final model     -> {model_path}")
    print(f"Saved model metadata  -> {meta_path}")

    return {
        "comparison": comparison,
        "best": best,
        "model_path": model_path,
        "metadata_path": meta_path,
        "reference_year": year,
    }


def main() -> None:
    """CLI entry point."""
    train_and_evaluate()


if __name__ == "__main__":
    main()
