"""Model training, evaluation, and artifact helpers."""

from src.models.evaluate_models import (
    build_comparison_frame,
    evaluate_model,
    predict_original_scale,
    regression_metrics,
    select_best_result,
)

__all__ = [
    "build_comparison_frame",
    "build_model_pipeline",
    "evaluate_model",
    "get_estimator_registry",
    "predict_original_scale",
    "regression_metrics",
    "select_best_result",
    "train_and_evaluate",
]


def __getattr__(name: str):
    """Lazy exports to avoid circular imports when running ``python -m``."""
    if name in {"build_model_pipeline", "get_estimator_registry", "train_and_evaluate"}:
        from src.models import train_models

        return getattr(train_models, name)
    raise AttributeError(f"module {__name!r} has no attribute {name!r}")
