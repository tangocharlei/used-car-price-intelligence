"""
Deal Analyzer — fair market value prediction and asking-price verdicts.

Loads ``models/final_model.joblib`` and ``models/model_metadata.json``, applies
the same feature engineering used at training time, and classifies deals as
Good Deal / Fairly Priced / Overpriced.

Designed for reuse from scripts or a future Streamlit UI::

    from app.deal_analyzer import predict_fair_value, analyze_deal
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from src.features.feature_engineering import (
    INFERENCE_REQUIRED_COLUMNS,
    MODEL_FEATURES,
    engineer_features,
)
from src.models.evaluate_models import to_original_scale

# ---------------------------------------------------------------------------
# Paths & loading
# ---------------------------------------------------------------------------


def get_project_root() -> Path:
    """``app/deal_analyzer.py`` → parents[0]=app, [1]=project root."""
    return Path(__file__).resolve().parents[1]


def get_model_path() -> Path:
    return get_project_root() / "models" / "final_model.joblib"


def get_metadata_path() -> Path:
    return get_project_root() / "models" / "model_metadata.json"


class ModelLoadError(RuntimeError):
    """Raised when the saved model or metadata cannot be loaded."""


@lru_cache(maxsize=1)
def load_metadata(path: str | None = None) -> dict[str, Any]:
    """Load model metadata JSON (cached)."""
    meta_path = Path(path) if path is not None else get_metadata_path()
    if not meta_path.exists():
        raise ModelLoadError(
            f"Model metadata not found at '{meta_path}'. "
            "Train the model first with: python -m src.models.train_models"
        )
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelLoadError(f"Invalid model metadata JSON at '{meta_path}': {exc}") from exc

    required_keys = {"target_strategy", "reference_year", "feature_list"}
    missing = required_keys - set(metadata)
    if missing:
        raise ModelLoadError(f"Metadata missing required keys: {sorted(missing)}")
    return metadata


@lru_cache(maxsize=1)
def load_model(path: str | None = None) -> Any:
    """Load the fitted sklearn / XGBoost pipeline (cached)."""
    model_path = Path(path) if path is not None else get_model_path()
    if not model_path.exists():
        raise ModelLoadError(
            f"Trained model not found at '{model_path}'. "
            "Train the model first with: python -m src.models.train_models"
        )
    try:
        return joblib.load(model_path)
    except Exception as exc:  # noqa: BLE001 - surface any loader failure clearly
        raise ModelLoadError(f"Failed to load model from '{model_path}': {exc}") from exc


def clear_model_cache() -> None:
    """Clear cached model / metadata (useful in tests)."""
    load_model.cache_clear()
    load_metadata.cache_clear()


# ---------------------------------------------------------------------------
# Feature preparation
# ---------------------------------------------------------------------------


def _to_dataframe(
    vehicle_features: Mapping[str, Any] | pd.DataFrame,
) -> pd.DataFrame:
    """Normalize dict / DataFrame input to a single-row or multi-row frame."""
    if isinstance(vehicle_features, pd.DataFrame):
        if vehicle_features.empty:
            raise ValueError("vehicle_features DataFrame is empty.")
        return vehicle_features.copy()

    if isinstance(vehicle_features, Mapping):
        if not vehicle_features:
            raise ValueError("vehicle_features dictionary is empty.")
        return pd.DataFrame([dict(vehicle_features)])

    raise TypeError(
        "vehicle_features must be a dict-like mapping or a pandas DataFrame, "
        f"got {type(vehicle_features)!r}."
    )


def prepare_feature_frame(
    vehicle_features: Mapping[str, Any] | pd.DataFrame,
    *,
    reference_year: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Validate inputs and return a model-ready feature frame.

    Accepts either:
    - raw inference fields (``yr_mfr``, ``kms_run``, …), which are engineered; or
    - already-engineered ``MODEL_FEATURES`` columns.
    """
    meta = metadata if metadata is not None else load_metadata()
    year = int(reference_year if reference_year is not None else meta["reference_year"])
    expected_features = list(meta.get("feature_list") or MODEL_FEATURES)

    df = _to_dataframe(vehicle_features)

    already_engineered = all(col in df.columns for col in expected_features)
    if already_engineered:
        frame = df.loc[:, expected_features].copy()
    else:
        missing_raw = [c for c in INFERENCE_REQUIRED_COLUMNS if c not in df.columns]
        if missing_raw:
            raise KeyError(
                "Missing required vehicle features for prediction. "
                f"Provide raw fields {list(INFERENCE_REQUIRED_COLUMNS)} "
                f"or engineered fields {expected_features}. "
                f"Missing: {missing_raw}"
            )
        engineered = engineer_features(df, reference_year=year, require_target=False)
        missing_eng = [c for c in expected_features if c not in engineered.columns]
        if missing_eng:
            raise KeyError(f"Feature engineering did not produce required columns: {missing_eng}")
        frame = engineered.loc[:, expected_features].copy()

    if frame.empty:
        raise ValueError("Prepared feature frame is empty.")
    return frame


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def predict_fair_value(
    vehicle_features: Mapping[str, Any] | pd.DataFrame,
    *,
    model: Any | None = None,
    metadata: dict[str, Any] | None = None,
    reference_year: int | None = None,
) -> float | list[float]:
    """
    Predict fair market value in INR (original rupee scale).

    Parameters
    ----------
    vehicle_features :
        Dict (single vehicle) or DataFrame (one or more vehicles).
    model / metadata :
        Optional pre-loaded artifacts; otherwise loaded from ``models/``.
    reference_year :
        Override for ``vehicle_age``. Defaults to the year stored in metadata.

    Returns
    -------
    float
        Single predicted fair value when one row is provided.
    list[float]
        List of predictions when multiple rows are provided.
    """
    meta = metadata if metadata is not None else load_metadata()
    pipe = model if model is not None else load_model()
    target_strategy = str(meta["target_strategy"])

    X = prepare_feature_frame(
        vehicle_features,
        reference_year=reference_year,
        metadata=meta,
    )

    try:
        raw_pred = pipe.predict(X)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Model prediction failed: {exc}") from exc

    values = to_original_scale(raw_pred, target_strategy)
    values = np.asarray(values, dtype=float).reshape(-1)

    if np.any(~np.isfinite(values)) or np.any(values <= 0):
        raise ValueError(
            f"Model produced non-positive or non-finite fair value(s): {values.tolist()}"
        )

    if len(values) == 1:
        return float(values[0])
    return [float(v) for v in values]


# ---------------------------------------------------------------------------
# Deal analysis
# ---------------------------------------------------------------------------


def analyze_deal(
    predicted_fair_value: float,
    asking_price: float,
) -> dict[str, Any]:
    """
    Compare an asking price against the predicted fair market value.

    Classification
    --------------
    - ``percentage_difference <= -10`` → ``\"Good Deal\"``
    - ``-10 < percentage_difference <= 10`` → ``\"Fairly Priced\"``
    - ``percentage_difference > 10`` → ``\"Overpriced\"``
    """
    try:
        fair = float(predicted_fair_value)
        ask = float(asking_price)
    except (TypeError, ValueError) as exc:
        raise ValueError("predicted_fair_value and asking_price must be numeric.") from exc

    if not np.isfinite(fair) or fair <= 0:
        raise ValueError(f"predicted_fair_value must be a positive number, got {predicted_fair_value!r}.")
    if not np.isfinite(ask) or ask <= 0:
        raise ValueError(f"asking_price must be a positive number, got {asking_price!r}.")

    price_difference = ask - fair
    percentage_difference = (price_difference / fair) * 100.0

    if percentage_difference <= -10:
        verdict = "Good Deal"
    elif percentage_difference <= 10:
        verdict = "Fairly Priced"
    else:
        verdict = "Overpriced"

    return {
        "predicted_fair_value": round(fair, 2),
        "asking_price": round(ask, 2),
        "price_difference": round(price_difference, 2),
        "percentage_difference": round(percentage_difference, 2),
        "verdict": verdict,
    }


MARKET_RANGE_PCT = 0.05
NEGOTIATION_OPENING_FACTOR = 0.97
NEGOTIATION_MAX_FACTOR = 1.03


def compute_deal_score(percentage_difference: float) -> int:
    """
    Map asking-vs-fair percentage difference to a 0–100 deal score.

    Higher scores indicate a better deal for the buyer (asking below fair value).
    Uses smooth piecewise-linear interpolation between anchor points.
    """
    pct = float(percentage_difference)
    anchors: list[tuple[float, float]] = [
        (-30.0, 100.0),
        (-15.0, 97.0),
        (-5.0, 87.0),
        (0.0, 70.0),
        (5.0, 60.0),
        (15.0, 47.0),
        (30.0, 20.0),
        (50.0, 5.0),
    ]

    if pct <= anchors[0][0]:
        return int(round(anchors[0][1]))
    if pct >= anchors[-1][0]:
        return int(round(max(0.0, anchors[-1][1])))

    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= pct <= x1:
            span = x1 - x0
            t = 0.0 if span == 0 else (pct - x0) / span
            score = y0 + t * (y1 - y0)
            return int(round(max(0.0, min(100.0, score))))

    return 50


def compute_market_range(
    fair_value: float,
    *,
    range_pct: float = MARKET_RANGE_PCT,
) -> dict[str, float]:
    """Heuristic indicative market range around the AI fair-value estimate."""
    fair = float(fair_value)
    if not np.isfinite(fair) or fair <= 0:
        return {"low": 0.0, "mid": 0.0, "high": 0.0, "range_pct": range_pct}

    pct = max(0.0, float(range_pct))
    return {
        "low": round(fair * (1.0 - pct), 2),
        "mid": round(fair, 2),
        "high": round(fair * (1.0 + pct), 2),
        "range_pct": pct,
    }


def compute_negotiation_guidance(fair_value: float) -> dict[str, float]:
    """AI-generated negotiation anchors — not guarantees."""
    fair = float(fair_value)
    if not np.isfinite(fair) or fair <= 0:
        return {
            "opening_offer": 0.0,
            "target_price": 0.0,
            "max_recommended": 0.0,
        }
    return {
        "opening_offer": round(fair * NEGOTIATION_OPENING_FACTOR, 2),
        "target_price": round(fair, 2),
        "max_recommended": round(fair * NEGOTIATION_MAX_FACTOR, 2),
    }


def deal_assessment_summary(percentage_difference: float) -> str:
    """Short narrative comparing asking price to the AI fair value."""
    pct = float(percentage_difference)
    magnitude = abs(round(pct, 1))
    if pct > 0.05:
        return (
            f"The asking price is {magnitude}% above the AI-estimated fair market value."
        )
    if pct < -0.05:
        return (
            f"The asking price is {magnitude}% below the AI-estimated fair market value."
        )
    return "The asking price aligns closely with the AI-estimated fair market value."


def negotiation_guidance_summary(
    asking_price: float,
    fair_value: float,
    *,
    percentage_difference: float,
) -> str:
    """Contextual negotiation note based on current asking price."""
    pct = float(percentage_difference)
    ask = float(asking_price)
    fair = float(fair_value)

    if fair <= 0:
        return "Use the AI fair value as a reference point during negotiation."

    if pct > 10:
        return (
            "The asking price exceeds the AI fair value. Consider opening below the "
            "target price and negotiating toward the AI estimate."
        )
    if pct > 3:
        return (
            "There is modest upward room in the asking price. A disciplined offer near "
            "the opening anchor may still achieve a fair outcome."
        )
    if pct < -10:
        return (
            "The asking price is already below the AI fair value. Verify vehicle "
            "condition before proceeding — the listing may already be attractive."
        )
    if pct < -3:
        return (
            "The asking price is slightly below the AI fair value. You may have limited "
            "negotiation room, but the target price remains a sensible reference."
        )
    return (
        "The asking price is near the AI fair value. Use the opening offer and target "
        "price as structured negotiation anchors."
    )


def compute_prediction_confidence(
    vehicle_features: Mapping[str, Any],
    *,
    dataset_context: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Heuristic prediction confidence based on training-data coverage.

    This is NOT model predictive uncertainty — it reflects how well the
    submitted configuration is represented in the available dataset.
    """
    ref_year = int(dataset_context.get("reference_year", 2026))
    year_min = int(dataset_context.get("year_min", 1990))
    year_max = int(dataset_context.get("year_max", ref_year))
    yr_mfr = int(vehicle_features.get("yr_mfr", ref_year))
    kms = float(vehicle_features.get("kms_run", 0))
    make = str(vehicle_features.get("make", "")).strip().lower()
    model = str(vehicle_features.get("model", "")).strip().lower()

    make_models: Mapping[str, Any] = dataset_context.get("make_models") or {}
    models_for_make = make_models.get(make, [])
    if isinstance(models_for_make, list):
        model_known = model in [str(m).lower() for m in models_for_make]
    else:
        model_known = False
    make_known = make in make_models

    score = 0.0
    factors: list[str] = []

    if make_known and model_known:
        score += 40.0
        factors.append("make and model are represented in the training dataset")
    elif make_known:
        score += 24.0
        factors.append("make is represented, but this model is less common in training data")
    else:
        score += 8.0
        factors.append("make/model combination has limited representation in training data")

    if year_min <= yr_mfr <= year_max:
        span = max(year_max - year_min, 1)
        center_dist = abs(yr_mfr - (year_min + year_max) / 2.0) / (span / 2.0)
        year_points = 25.0 * max(0.35, 1.0 - center_dist)
        score += year_points
        factors.append("manufacturing year falls within the training range")
    else:
        score += 8.0
        factors.append("manufacturing year sits outside the common training range")

    kms_p25 = float(dataset_context.get("kms_p25", 0))
    kms_p75 = float(dataset_context.get("kms_p75", 0))
    if kms_p25 > 0 and kms_p75 >= kms_p25 and kms > 0:
        if kms_p25 <= kms <= kms_p75:
            score += 20.0
            factors.append("mileage is within a typical training distribution band")
        elif kms_p25 * 0.5 <= kms <= kms_p75 * 1.5:
            score += 12.0
            factors.append("mileage is moderately aligned with training listings")
        else:
            score += 5.0
            factors.append("mileage is outside the typical training distribution band")
    elif kms > 0:
        score += 10.0

    categorical_checks = [
        ("fuel_type", "fuel_types"),
        ("transmission", "transmissions"),
        ("body_type", "body_types"),
        ("city", "cities"),
    ]
    cat_points = 0.0
    for field, options_key in categorical_checks:
        options = dataset_context.get(options_key) or []
        if isinstance(options, (list, tuple, set)):
            raw = str(vehicle_features.get(field, "")).strip().lower()
            if raw and raw in {str(o).lower() for o in options}:
                cat_points += 3.75
    score += min(15.0, cat_points)

    score = int(round(max(0.0, min(100.0, score))))
    if score >= 75:
        level = "HIGH"
    elif score >= 50:
        level = "MODERATE"
    else:
        level = "LIMITED"

    if level == "HIGH":
        explanation = (
            "HIGH CONFIDENCE — The vehicle configuration is well represented "
            "within the available training data."
        )
    elif level == "MODERATE":
        explanation = (
            "MODERATE CONFIDENCE — The valuation is reasonable, but some inputs "
            "are less common in the training dataset."
        )
    else:
        explanation = (
            "LIMITED CONFIDENCE — Use this estimate as directional guidance; "
            "the configuration has limited coverage in training data."
        )

    return {
        "score": score,
        "level": level,
        "explanation": explanation,
        "factors": factors,
    }


def build_valuation_factors(
    vehicle_features: Mapping[str, Any],
    *,
    reference_year: int,
    dataset_context: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Transparent heuristic factor explanations — not exact feature importance."""
    ref_year = int(reference_year)
    yr_mfr = int(vehicle_features.get("yr_mfr", ref_year))
    age = max(0, ref_year - yr_mfr)
    kms = int(vehicle_features.get("kms_run", 0))
    owners = int(vehicle_features.get("total_owners", 1))

    factors: list[dict[str, str]] = []

    if age >= 12:
        factors.append(
            {
                "label": "Vehicle Age",
                "signal": "negative",
                "text": f"{age} years old — older vehicle; typically downward pressure on value.",
            }
        )
    elif age >= 6:
        factors.append(
            {
                "label": "Vehicle Age",
                "signal": "neutral",
                "text": f"{age} years old — moderate age profile for the used market.",
            }
        )
    else:
        factors.append(
            {
                "label": "Vehicle Age",
                "signal": "positive",
                "text": f"{age} years old — relatively newer vehicle; supports resale value.",
            }
        )

    expected_kms = max(age, 1) * 12_000
    ctx = dataset_context or {}
    kms_p75 = float(ctx.get("kms_p75", expected_kms * 1.25))
    if kms <= expected_kms * 0.85:
        factors.append(
            {
                "label": "Mileage",
                "signal": "positive",
                "text": f"{kms:,} km — lower mileage relative to vehicle age.",
            }
        )
    elif kms >= max(kms_p75, expected_kms * 1.35):
        factors.append(
            {
                "label": "Mileage",
                "signal": "negative",
                "text": f"{kms:,} km — higher mileage; typically downward pressure on value.",
            }
        )
    else:
        factors.append(
            {
                "label": "Mileage",
                "signal": "neutral",
                "text": f"{kms:,} km — mileage is within a typical range for this age.",
            }
        )

    if owners == 1:
        factors.append(
            {
                "label": "Previous Owners",
                "signal": "positive",
                "text": "Single owner — fewer previous owners; positive resale signal.",
            }
        )
    elif owners == 2:
        factors.append(
            {
                "label": "Previous Owners",
                "signal": "neutral",
                "text": "Two previous owners — common ownership profile.",
            }
        )
    else:
        factors.append(
            {
                "label": "Previous Owners",
                "signal": "negative",
                "text": f"{owners} previous owners — multiple ownership changes may reduce buyer confidence.",
            }
        )

    bool_factors = [
        ("assured_buy", "Assured Buy", "Positive listing confidence signal.", "Not flagged as assured buy."),
        ("warranty_avail", "Warranty Available", "Positive buyer confidence signal.", "No warranty indicated."),
        ("fitness_certificate", "Fitness Certificate", "Positive compliance signal.", "No fitness certificate indicated."),
    ]
    for key, label, pos_text, neg_text in bool_factors:
        if bool(vehicle_features.get(key, False)):
            factors.append({"label": label, "signal": "positive", "text": pos_text})
        else:
            factors.append({"label": label, "signal": "neutral", "text": neg_text})

    make = str(vehicle_features.get("make", "")).replace("_", " ").title()
    model = str(vehicle_features.get("model", "")).replace("_", " ").title()
    factors.append(
        {
            "label": "Make / Model",
            "signal": "neutral",
            "text": f"{make} {model} — brand and model segment influence market pricing.",
        }
    )

    fuel = str(vehicle_features.get("fuel_type", "")).replace("_", " ").title()
    transmission = str(vehicle_features.get("transmission", "")).replace("_", " ").title()
    factors.append(
        {
            "label": "Fuel & Transmission",
            "signal": "neutral",
            "text": f"{fuel} · {transmission} — configuration affects demand in this market.",
        }
    )

    return factors


def build_vehicle_signals(
    vehicle_features: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    reference_year: int,
    dataset_context: Mapping[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Positive signals and considerations derived from submitted inputs."""
    ref_year = int(reference_year)
    yr_mfr = int(vehicle_features.get("yr_mfr", ref_year))
    age = max(0, ref_year - yr_mfr)
    kms = int(vehicle_features.get("kms_run", 0))
    owners = int(vehicle_features.get("total_owners", 1))
    pct = float(result.get("percentage_difference", 0.0))

    positive: list[str] = []
    considerations: list[str] = []

    if owners == 1:
        positive.append("Single owner")
    elif owners >= 3:
        considerations.append("Multiple previous owners")

    if bool(vehicle_features.get("warranty_avail", False)):
        positive.append("Warranty available")
    if bool(vehicle_features.get("assured_buy", False)):
        positive.append("Assured Buy listing")
    if bool(vehicle_features.get("fitness_certificate", False)):
        positive.append("Fitness certificate")

    ctx = dataset_context or {}
    kms_p75 = float(ctx.get("kms_p75", age * 12_000 * 1.25))
    expected_kms = max(age, 1) * 12_000
    if kms >= max(kms_p75, expected_kms * 1.35):
        considerations.append("Higher than typical mileage for vehicle age")
    elif kms <= expected_kms * 0.85:
        positive.append("Lower mileage for vehicle age")

    if age >= 10:
        considerations.append("Older vehicle age profile")
    elif age <= 4:
        positive.append("Relatively newer vehicle")

    if pct > 5:
        considerations.append("Asking price above AI estimated value")
    elif pct < -5:
        positive.append("Asking price below AI estimated value")

    return {"positive": positive, "considerations": considerations}


def build_purchase_recommendation(
    report: Mapping[str, Any],
    vehicle_features: Mapping[str, Any],
    *,
    reference_year: int,
) -> dict[str, Any]:
    """
    Build an advisory purchase recommendation from valuation outputs and vehicle signals.

    Returns structured fields for the premium recommendation UI while preserving the
    existing status / deal-band logic.
    """
    pct = float(report.get("percentage_difference", 0.0))
    deal_score = int(report.get("deal_score", 0))
    ask = float(report.get("asking_price", 0.0))
    fair = float(report.get("predicted_fair_value", 0.0))

    confidence = report.get("confidence") or {}
    conf_level = str(confidence.get("level", "MODERATE")).strip().upper()
    conf_score = int(confidence.get("score", 50))

    signals = report.get("vehicle_signals") or {}
    positive = list(signals.get("positive") or [])
    considerations = list(signals.get("considerations") or [])

    ref_year = int(reference_year)
    yr_mfr = int(vehicle_features.get("yr_mfr", ref_year))
    age = max(0, ref_year - yr_mfr)
    kms = int(vehicle_features.get("kms_run", 0))
    owners = int(vehicle_features.get("total_owners", 1))
    assured = bool(vehicle_features.get("assured_buy", False))
    warranty = bool(vehicle_features.get("warranty_avail", False))
    fitness = bool(vehicle_features.get("fitness_certificate", False))

    major_concerns = len(considerations)
    low_confidence = conf_level in {"LIMITED", "LOW"} or conf_score < 45
    high_confidence = conf_level == "HIGH" and conf_score >= 70

    # Status bands based primarily on asking price vs fair value, then tempered by risk.
    if pct <= -12 and high_confidence and major_concerns == 0:
        status = "strong_positive"
        headline = "Strong Buying Opportunity"
        icon = "◆"
    elif pct <= -5 and major_concerns <= 1 and not low_confidence:
        status = "strong_positive" if deal_score >= 80 else "positive"
        headline = "Recommended to Consider" if status == "positive" else "Strong Buying Opportunity"
        icon = "✓" if status == "positive" else "◆"
    elif pct <= 5 and major_concerns <= 2:
        status = "positive" if major_concerns == 0 else "caution"
        headline = "Recommended to Consider" if status == "positive" else "Proceed with Caution"
        icon = "✓" if status == "positive" else "!"
    elif pct <= 15:
        status = "caution"
        headline = "Negotiate Before Buying"
        icon = "↓"
    else:
        status = "negative"
        headline = "Not Recommended at the Current Price"
        icon = "✕"

    if low_confidence and status in {"strong_positive", "positive"}:
        status = "caution"
        headline = "Proceed with Caution"
        icon = "!"

    # Compact commercial badge + colour tone (maps to existing status bands).
    if status == "strong_positive":
        badge = "STRONG BUY"
        tone = "buy"
    elif status == "positive":
        badge = "BUY"
        tone = "buy"
    elif status == "caution" and pct > 5:
        badge = "NEGOTIATE"
        tone = "caution"
    elif status == "caution":
        badge = "CONSIDER"
        tone = "caution"
    else:
        badge = "AVOID"
        tone = "avoid"

    gap_abs = abs(pct)
    if pct < -1:
        price_delta_label = f"{gap_abs:.1f}% BELOW FAIR VALUE"
        price_delta_tone = "below"
        price_clause = (
            f"Asking price ₹{int(round(ask)):,} is about {gap_abs:.1f}% below "
            f"the AI fair value of ₹{int(round(fair)):,}."
        )
    elif pct > 1:
        price_delta_label = f"{gap_abs:.1f}% ABOVE FAIR VALUE"
        price_delta_tone = "above"
        price_clause = (
            f"Asking price ₹{int(round(ask)):,} is about {gap_abs:.1f}% above "
            f"the AI fair value of ₹{int(round(fair)):,}."
        )
    else:
        price_delta_label = "NEAR FAIR VALUE"
        price_delta_tone = "aligned"
        price_clause = (
            f"Asking price ₹{int(round(ask)):,} is broadly aligned with "
            f"the AI fair value of ₹{int(round(fair)):,}."
        )

    stance = {
        "strong_positive": "This vehicle is recommended for purchase based on current valuation signals.",
        "positive": "This vehicle is recommended for consideration based on current valuation signals.",
        "caution": "This vehicle may still be viable, but price or risk factors call for caution.",
        "negative": "This vehicle is not recommended at the current asking price.",
    }.get(status, "Treat this valuation as advisory decision support.")

    decision_positives: list[str] = []
    seen_pos: set[str] = set()

    def _norm_key(text: str) -> str:
        return " ".join(text.casefold().replace("-", " ").split())

    def _add_positive(text: str) -> None:
        key = _norm_key(text)
        # Collapse near-duplicates (e.g. "Single owner" / "Single-owner history").
        aliases = {
            "single owner": "single owner history",
            "single owner history": "single owner history",
            "asking price below ai estimated value": "asking price below estimated market value",
            "asking price below estimated market value": "asking price below estimated market value",
            "warranty available": "warranty available",
            "assured buy listing": "assured buy listing",
            "fitness certificate": "valid fitness certificate",
            "valid fitness certificate": "valid fitness certificate",
            "lower mileage for vehicle age": "lower than average mileage for vehicle age",
            "lower than average mileage for vehicle age": "lower than average mileage for vehicle age",
            "relatively newer vehicle": "relatively newer vehicle age profile",
            "relatively newer vehicle age profile": "relatively newer vehicle age profile",
        }
        key = aliases.get(key, key)
        if key not in seen_pos:
            seen_pos.add(key)
            decision_positives.append(text)

    for item in positive:
        _add_positive(str(item))
    if pct < -5:
        _add_positive("Asking price below estimated market value")
    if owners == 1:
        _add_positive("Single-owner history")
    if assured:
        _add_positive("Assured Buy listing")
    if warranty:
        _add_positive("Warranty available")
    if fitness:
        _add_positive("Valid fitness certificate")
    expected_kms = max(age, 1) * 12_000
    if kms > 0 and kms <= expected_kms * 0.85:
        _add_positive("Lower-than-average mileage for vehicle age")
    if age <= 4:
        _add_positive("Relatively newer vehicle age profile")

    decision_risks: list[dict[str, str]] = []
    seen_risk: set[str] = set()

    def _add_risk(text: str, severity: str = "caution") -> None:
        key = _norm_key(text)
        aliases = {
            "asking price above ai estimated value": "asking price above estimated fair value",
            "asking price above estimated fair value": "asking price above estimated fair value",
            "asking price significantly above estimated fair value": (
                "asking price significantly above estimated fair value"
            ),
            "higher than typical mileage for vehicle age": "high mileage relative to vehicle age",
            "high mileage relative to vehicle age": "high mileage relative to vehicle age",
            "older vehicle age profile": "older vehicle age profile",
            "multiple previous owners": "multiple previous owners",
            "no warranty indicated": "no warranty indicated",
            "no fitness certificate indicated": "no fitness certificate indicated",
        }
        key = aliases.get(key, key)
        # Prefer the stronger price-risk wording if both exist.
        if (
            key == "asking price above estimated fair value"
            and "asking price significantly above estimated fair value" in seen_risk
        ):
            return
        if key == "asking price significantly above estimated fair value":
            seen_risk.discard("asking price above estimated fair value")
            decision_risks[:] = [
                r
                for r in decision_risks
                if _norm_key(r["text"])
                not in {
                    "asking price above ai estimated value",
                    "asking price above estimated fair value",
                }
            ]
        if key not in seen_risk:
            seen_risk.add(key)
            decision_risks.append({"text": text, "severity": severity})

    for item in considerations:
        text = str(item)
        severity = "critical" if "above" in text.casefold() and pct >= 12 else "caution"
        _add_risk(text, severity)
    if pct >= 12:
        _add_risk("Asking price significantly above estimated fair value", "critical")
    elif pct > 5:
        _add_risk("Asking price above estimated fair value", "caution")
    if age >= 10:
        _add_risk("Older vehicle age profile", "caution")
    if kms > 0 and kms >= expected_kms * 1.35:
        _add_risk("High mileage relative to vehicle age", "caution")
    if owners >= 3:
        _add_risk("Multiple previous owners", "caution")
    if not warranty:
        _add_risk("No warranty indicated", "caution")
    if not fitness:
        _add_risk("No fitness certificate indicated", "caution")
    if low_confidence:
        _add_risk(
            f"Limited prediction confidence ({conf_level.title()}, {conf_score}%)",
            "caution",
        )

    top_positives = decision_positives[:4]
    top_risks = [r["text"] for r in decision_risks[:3]]

    why_bits: list[str] = []
    if top_positives:
        if len(top_positives) == 1:
            why_bits.append(f"Key positives include {top_positives[0].lower()}.")
        else:
            why_bits.append(
                "Key positives include "
                + ", ".join(p.lower() for p in top_positives[:-1])
                + f", and {top_positives[-1].lower()}."
            )
    if top_risks:
        if len(top_risks) == 1:
            why_bits.append(f"Primary attention points include {top_risks[0].lower()}.")
        else:
            why_bits.append(
                "Primary attention points include "
                + ", ".join(r.lower() for r in top_risks[:-1])
                + f", and {top_risks[-1].lower()}."
            )
    elif not decision_risks:
        why_bits.append(
            "No major valuation concerns were detected from the available vehicle data."
        )
    if low_confidence:
        why_bits.append(
            f"Prediction confidence is {conf_level.title()} ({conf_score}%) — "
            "compare similar local listings before deciding."
        )
    elif status in {"strong_positive", "positive"}:
        why_bits.append(
            "Overall valuation economics support proceeding, subject to inspection."
        )
    elif status == "caution":
        why_bits.append(
            "Resolve highlighted price or risk factors before making a final decision."
        )
    else:
        why_bits.append(
            "Current pricing does not justify purchase without a material seller concession."
        )
    why_summary = " ".join(why_bits)

    # Concise supporting line under the headline (not the long paragraph).
    support_summary = {
        "strong_positive": (
            f"Deal score {deal_score}/100 with asking price meaningfully below AI fair value."
        ),
        "positive": (
            f"Deal score {deal_score}/100 with pricing and vehicle signals supporting consideration."
        ),
        "caution": (
            f"Deal score {deal_score}/100 — resolve price or risk factors before committing."
        ),
        "negative": (
            f"Deal score {deal_score}/100 — current asking price is difficult to justify."
        ),
    }.get(status, f"Deal score {deal_score}/100 based on current valuation signals.")

    if low_confidence:
        support_summary = (
            f"Deal score {deal_score}/100 with {conf_level.title()} confidence — "
            "treat the estimate cautiously."
        )

    next_steps: list[dict[str, str]] = [
        {
            "icon": "◎",
            "text": "Inspect the vehicle physically for mechanical and bodywork issues",
        },
        {
            "icon": "☰",
            "text": "Verify service and maintenance records",
        },
        {
            "icon": "▣",
            "text": "Confirm ownership and registration documents",
        },
        {
            "icon": "◈",
            "text": "Review insurance and accident history",
        },
    ]
    if not fitness:
        next_steps.append(
            {
                "icon": "✓",
                "text": "Obtain and verify applicable fitness and compliance certificates",
            }
        )
    else:
        next_steps.append(
            {
                "icon": "✓",
                "text": "Verify applicable fitness and compliance certificates",
            }
        )
    if pct > 5:
        next_steps.append(
            {
                "icon": "↓",
                "text": "Negotiate the asking price toward the AI fair-value estimate",
            }
        )
    next_steps = next_steps[:5]

    # Final AI verdict derived from the same status bands.
    if status == "strong_positive":
        verdict_label = "Strongly Recommended"
        verdict_detail = (
            "Strongly Recommended — subject to physical inspection and document verification."
        )
    elif status == "positive":
        verdict_label = "Recommended"
        verdict_detail = (
            "Recommended — subject to physical inspection and document verification."
        )
    elif status == "caution" and pct > 5:
        verdict_label = "Negotiate Before Buying"
        verdict_detail = (
            "Negotiate Before Buying — align price closer to AI fair value before committing."
        )
    elif status == "caution":
        verdict_label = "Worth Considering"
        verdict_detail = (
            "Worth Considering — proceed only after addressing the highlighted risk factors."
        )
    else:
        verdict_label = "Not Recommended"
        verdict_detail = (
            "Not Recommended — current asking price is not supported by the AI valuation."
        )

    if low_confidence and status != "negative":
        verdict_detail = (
            f"{verdict_label} — low prediction confidence means additional market research "
            "is advised before purchase."
        )

    # Single balanced purchase-guidance paragraph (used once in the executive report).
    pos_phrase = ""
    if top_positives:
        if len(top_positives) == 1:
            pos_phrase = f"favourable signals such as {top_positives[0].lower()}"
        else:
            pos_phrase = (
                "favourable signals including "
                + ", ".join(p.lower() for p in top_positives[:2])
            )
    risk_phrase = ""
    if top_risks:
        if len(top_risks) == 1:
            risk_phrase = top_risks[0].lower()
        else:
            risk_phrase = f"{top_risks[0].lower()} and {top_risks[1].lower()}"

    guidance_bits: list[str] = []
    if pos_phrase:
        guidance_bits.append(f"The vehicle shows {pos_phrase}.")
    else:
        guidance_bits.append(
            "Available listing characteristics do not present standout quality advantages."
        )
    guidance_bits.append(price_clause)
    if risk_phrase:
        guidance_bits.append(f"Key considerations include {risk_phrase}.")
    elif status in {"strong_positive", "positive"}:
        guidance_bits.append(
            "No major valuation concerns were detected from the available vehicle data."
        )
    if low_confidence:
        guidance_bits.append(
            "Prediction confidence is limited, so compare similar local listings before deciding."
        )
    elif status == "negative":
        guidance_bits.append(
            "A purchase is only attractive after a substantial seller concession and a "
            "satisfactory independent inspection."
        )
    elif status == "caution":
        guidance_bits.append(
            "A purchase may only be attractive following meaningful negotiation and "
            "a satisfactory independent inspection."
        )
    else:
        guidance_bits.append(
            "Proceed only after a physical inspection and verification of ownership documents."
        )
    guidance_summary = " ".join(guidance_bits)

    action_line = {
        "strong_positive": (
            "Recommendation: Proceed with purchase — subject to inspection and document checks."
        ),
        "positive": (
            "Recommendation: Consider purchasing after standard due diligence."
        ),
        "caution": (
            "Recommendation: Negotiate aggressively or consider comparable alternatives."
            if pct > 5
            else "Recommendation: Proceed only after addressing the highlighted risk factors."
        ),
        "negative": (
            "Recommendation: Do not buy at the current asking price; seek comparable alternatives."
        ),
    }.get(
        status,
        "Recommendation: Use this analysis as decision support alongside an independent inspection.",
    )

    # Executive verdict title used in the always-visible report header.
    executive_verdict = {
        "strong_positive": "Strongly Recommended",
        "positive": "Recommended",
        "caution": "Negotiate Before Buying" if pct > 5 else "Worth Considering",
        "negative": "Not Recommended at Current Price",
    }.get(status, verdict_label)

    disclaimer = (
        "Important: This recommendation is generated from available listing data and AI "
        "valuation signals. It is intended as decision support and does not replace a "
        "professional mechanical inspection, legal verification, or independent vehicle assessment."
    )

    # Backward-compatible long summary for any older consumers.
    summary = " ".join([stance, price_clause, support_summary])

    return {
        "headline": headline,
        "status": status,
        "tone": tone,
        "badge": badge,
        "icon": icon,
        "summary": summary,
        "support_summary": support_summary,
        "why_summary": why_summary,
        "stance": stance,
        "guidance_summary": guidance_summary,
        "action_line": action_line,
        "executive_verdict": executive_verdict,
        "price_delta_label": price_delta_label,
        "price_delta_tone": price_delta_tone,
        "price_explanation": price_clause,
        "decision_positives": decision_positives,
        "decision_risks": decision_risks,
        "checklist": [step["text"] for step in next_steps],
        "next_steps": next_steps,
        "verdict_label": verdict_label,
        "verdict_detail": verdict_detail,
        "disclaimer": disclaimer,
        "deal_score": deal_score,
        "confidence_level": conf_level,
        "confidence_score": conf_score,
    }


def enrich_valuation_report(
    result: Mapping[str, Any],
    vehicle_features: Mapping[str, Any],
    *,
    dataset_context: Mapping[str, Any],
    reference_year: int | None = None,
) -> dict[str, Any]:
    """Extend a deal-analysis result with report sections for the UI."""
    ref_year = int(
        reference_year
        if reference_year is not None
        else dataset_context.get("reference_year", 2026)
    )
    fair = float(result["predicted_fair_value"])
    ask = float(result["asking_price"])
    pct = float(result["percentage_difference"])

    report = dict(result)
    report["deal_score"] = compute_deal_score(pct)
    report["deal_assessment_summary"] = deal_assessment_summary(pct)
    report["market_range"] = compute_market_range(fair)
    report["negotiation"] = compute_negotiation_guidance(fair)
    report["negotiation_summary"] = negotiation_guidance_summary(
        ask, fair, percentage_difference=pct
    )
    report["confidence"] = compute_prediction_confidence(
        vehicle_features,
        dataset_context=dataset_context,
    )
    report["valuation_factors"] = build_valuation_factors(
        vehicle_features,
        reference_year=ref_year,
        dataset_context=dataset_context,
    )
    report["vehicle_signals"] = build_vehicle_signals(
        vehicle_features,
        result,
        reference_year=ref_year,
        dataset_context=dataset_context,
    )
    report["purchase_recommendation"] = build_purchase_recommendation(
        report,
        vehicle_features,
        reference_year=ref_year,
    )
    return report


def analyze_vehicle_deal(
    vehicle_features: Mapping[str, Any] | pd.DataFrame,
    asking_price: float,
    **predict_kwargs: Any,
) -> dict[str, Any]:
    """Predict fair value for a vehicle and return the full deal analysis."""
    fair_value = predict_fair_value(vehicle_features, **predict_kwargs)
    if isinstance(fair_value, list):
        if len(fair_value) != 1:
            raise ValueError(
                "analyze_vehicle_deal expects a single vehicle; "
                f"got {len(fair_value)} predictions."
            )
        fair_value = fair_value[0]
    return analyze_deal(fair_value, asking_price)


# ---------------------------------------------------------------------------
# Example / manual test
# ---------------------------------------------------------------------------


def _example_vehicle() -> dict[str, Any]:
    """Sample hatchback-style listing for a quick smoke test."""
    return {
        "yr_mfr": 2017,
        "kms_run": 45000,
        "total_owners": 1,
        "assured_buy": True,
        "warranty_avail": False,
        "fitness_certificate": True,
        "fuel_type": "petrol",
        "body_type": "hatchback",
        "transmission": "manual",
        "make": "maruti",
        "model": "swift",
        "city": "noida",
        "registered_state": "uttar pradesh",
    }


def main() -> None:
    """Demonstrate fair-value prediction and deal classification."""
    vehicle = _example_vehicle()
    asking_price = 350000

    print("Example vehicle:")
    for key, value in vehicle.items():
        print(f"  {key}: {value}")

    fair_value = predict_fair_value(vehicle)
    print(f"\nPredicted fair market value: Rs {fair_value:,.2f}")

    result = analyze_deal(fair_value, asking_price)
    print("\nDeal analysis:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
