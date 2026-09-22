"""Application helpers for the Used Vehicle Valuation & Deal Analyzer."""

__all__ = [
    "ModelLoadError",
    "analyze_deal",
    "analyze_vehicle_deal",
    "load_metadata",
    "load_model",
    "predict_fair_value",
]


def __getattr__(name: str):
    if name in __all__:
        from app import deal_analyzer

        return getattr(deal_analyzer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
