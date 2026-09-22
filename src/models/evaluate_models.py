"""
Regression evaluation helpers for used-vehicle price models.

All metrics are computed on the original rupee scale of ``sale_price``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline


def to_original_scale(y: np.ndarray | pd.Series, target_strategy: str) -> np.ndarray:
    """
    Map predictions / targets back to rupee scale when needed.

    Parameters
    ----------
    target_strategy :
        ``\"original\"`` leaves values unchanged.
        ``\"log1p\"`` applies ``expm1`` and clips at 0 (prices cannot be negative).
    """
    values = np.asarray(y, dtype=float)
    if target_strategy == "original":
        return values
    if target_strategy == "log1p":
        return np.clip(np.expm1(values), a_min=0.0, a_max=None)
    raise ValueError(f"Unknown target_strategy: {target_strategy!r}")


def regression_metrics(y_true: np.ndarray | pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    """Compute MAE, RMSE, and R² on the original sale_price scale."""
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr)))
    r2 = float(r2_score(y_true_arr, y_pred_arr))
    return {"MAE": mae, "RMSE": rmse, "R2": r2}


def predict_original_scale(
    model: BaseEstimator | Pipeline,
    X: pd.DataFrame,
    target_strategy: str,
) -> np.ndarray:
    """Generate predictions and convert them to the original rupee scale."""
    raw_pred = model.predict(X)
    return to_original_scale(raw_pred, target_strategy)


def evaluate_model(
    model: BaseEstimator | Pipeline,
    X_test: pd.DataFrame,
    y_test_original: pd.Series | np.ndarray,
    *,
    model_name: str,
    target_strategy: str,
) -> dict[str, Any]:
    """
    Evaluate a fitted pipeline on held-out data.

    Parameters
    ----------
    y_test_original :
        Ground-truth ``sale_price`` on the original rupee scale (never log-transformed).
    """
    y_pred = predict_original_scale(model, X_test, target_strategy)
    metrics = regression_metrics(y_test_original, y_pred)
    return {
        "model_name": model_name,
        "target_strategy": target_strategy,
        "MAE": metrics["MAE"],
        "RMSE": metrics["RMSE"],
        "R2": metrics["R2"],
    }


def build_comparison_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Assemble and sort the model comparison table (best MAE first)."""
    if not rows:
        raise ValueError("No evaluation rows provided.")

    comparison = pd.DataFrame(rows)
    expected = ["model_name", "target_strategy", "MAE", "RMSE", "R2"]
    missing = [c for c in expected if c not in comparison.columns]
    if missing:
        raise KeyError(f"Comparison rows missing columns: {missing}")

    return (
        comparison.loc[:, expected]
        .sort_values(["MAE", "RMSE", "R2"], ascending=[True, True, False])
        .reset_index(drop=True)
    )


def select_best_result(comparison: pd.DataFrame) -> pd.Series:
    """
    Select the best run primarily by lowest MAE.

    Ties are broken by lower RMSE, then higher R².
    """
    if comparison.empty:
        raise ValueError("Cannot select a best model from an empty comparison table.")

    ranked = comparison.sort_values(
        ["MAE", "RMSE", "R2"], ascending=[True, True, False]
    ).reset_index(drop=True)
    return ranked.iloc[0]


def save_comparison_csv(comparison: pd.DataFrame, path: str | Path) -> Path:
    """Persist the comparison dataframe to CSV."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(out, index=False)
    return out


def print_best_result(best: pd.Series) -> None:
    """Pretty-print the selected model summary."""
    print("\n========== BEST MODEL ==========")
    print(f"Model            : {best['model_name']}")
    print(f"Target strategy  : {best['target_strategy']}")
    print(f"MAE              : {best['MAE']:,.2f}")
    print(f"RMSE             : {best['RMSE']:,.2f}")
    print(f"R2               : {best['R2']:.4f}")
    print("================================\n")
