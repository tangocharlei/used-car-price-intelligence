"""
AutoValue AI — Used Vehicle Valuation & Deal Analyzer

Streamlit UI layer only. All ML logic lives in ``app.deal_analyzer``.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from app.deal_analyzer import (
    ModelLoadError,
    analyze_vehicle_deal,
    build_purchase_recommendation,
    enrich_valuation_report,
    load_metadata,
)
from app.ui_display import (
    format_inr,
    format_lakh,
    format_lakh_compact,
    format_signed_inr,
    format_signed_pct,
    verdict_summary,
)
from app.ui_formatting import (
    build_label_maps,
    build_owner_maps,
    format_category_label,
    format_owner_label,
)
from app.ui_theme import (
    COLORS,
    inject_global_styles,
    inject_scroll_layout_fix,
    render_app_branding,
    render_section_header,
)

st.set_page_config(
    page_title="AutoValue AI",
    page_icon="🚗",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "Used_Car_Price_Prediction.csv"

inject_global_styles()
inject_scroll_layout_fix()


def format_indian_number(value: int | float) -> str:
    """Format a positive integer amount using Indian grouping (e.g. 350000 -> 3,50,000)."""
    return format_inr(value)


def _migrate_wizard_asking_price_key() -> None:
    """Keep legacy session key in sync with the canonical wizard asking price key."""
    if "wizard_asking_price_input" in st.session_state and "wizard_asking_price" not in st.session_state:
        st.session_state["wizard_asking_price"] = st.session_state["wizard_asking_price_input"]


def _validation_fields_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Return only the vehicle fields consumed by validate_inputs()."""
    return {
        "yr_mfr": profile["yr_mfr"],
        "kms_run": profile["kms_run"],
        "total_owners": profile["total_owners"],
        "make": profile["make"],
        "model": profile["model"],
        "fuel_type": profile["fuel_type"],
        "transmission": profile["transmission"],
        "body_type": profile["body_type"],
        "city": profile["city"],
        "registered_state": profile["registered_state"],
    }


def _render_asking_price_preview() -> None:
    asking_price = int(st.session_state.get("wizard_asking_price", 0))
    formatted = format_indian_number(asking_price)
    st.markdown(
        f'<div class="asking-price-preview"><span class="asking-price-preview-label">Entered Amount</span><span class="asking-price-preview-value">₹{escape(formatted)}</span></div>',
        unsafe_allow_html=True,
    )


def _display_to_raw(display_value: str, raw_options: list[str], *, fallback: str) -> str:
    _, display_to_raw = build_label_maps(raw_options)
    return display_to_raw.get(str(display_value), fallback)


def _owner_display_to_raw(display_value: str, raw_options: list[int], *, fallback: int) -> int:
    _, display_to_raw = build_owner_maps(raw_options)
    return int(display_to_raw.get(str(display_value), fallback))


def _raw_make_from_session(options: dict[str, Any]) -> str:
    fallback = "maruti" if "maruti" in options["makes"] else options["makes"][0]
    return _display_to_raw(
        str(st.session_state.get("wizard_make_select", format_category_label(fallback))),
        options["makes"],
        fallback=fallback,
    )


def _model_options_for_make(options: dict[str, Any], make: str) -> list[str]:
    model_options = options["make_models"].get(make, [])
    return model_options if model_options else [make]


def _sync_wizard_model_for_make(options: dict[str, Any]) -> None:
    """Keep model selection valid when make changes; only reset if invalid."""
    make = _raw_make_from_session(options)
    model_options = _model_options_for_make(options, make)
    display_options, _ = build_label_maps(model_options)
    current = str(st.session_state.get("wizard_model_select", ""))
    if current in display_options:
        return
    preferred = "swift" if "swift" in model_options else model_options[0]
    st.session_state["wizard_model_select"] = format_category_label(preferred)


def init_wizard_state(options: dict[str, Any]) -> None:
    """Initialize every wizard widget key before widgets render or profile collection."""
    _migrate_wizard_asking_price_key()
    st.session_state.setdefault("wizard_yr_mfr", 2017)
    st.session_state.setdefault("wizard_kms_run", 45000)
    st.session_state.setdefault("wizard_owners_select", format_owner_label(1))

    make_default = "maruti" if "maruti" in options["makes"] else options["makes"][0]
    st.session_state.setdefault("wizard_make_select", format_category_label(make_default))

    make = _raw_make_from_session(options)
    model_options = _model_options_for_make(options, make)
    model_default = "swift" if "swift" in model_options else model_options[0]
    st.session_state.setdefault("wizard_model_select", format_category_label(model_default))
    _sync_wizard_model_for_make(options)

    fuel_default = "petrol" if "petrol" in options["fuel_types"] else options["fuel_types"][0]
    transmission_default = (
        "manual" if "manual" in options["transmissions"] else options["transmissions"][0]
    )
    body_default = (
        "hatchback" if "hatchback" in options["body_types"] else options["body_types"][0]
    )
    city_default = "noida" if "noida" in options["cities"] else options["cities"][0]
    state_default = (
        "uttar pradesh"
        if "uttar pradesh" in options["states"]
        else options["states"][0]
    )

    st.session_state.setdefault("wizard_fuel_select", format_category_label(fuel_default))
    st.session_state.setdefault(
        "wizard_transmission_select",
        format_category_label(transmission_default),
    )
    st.session_state.setdefault("wizard_body_select", format_category_label(body_default))
    st.session_state.setdefault("wizard_city_select", format_category_label(city_default))
    st.session_state.setdefault("wizard_state_select", format_category_label(state_default))

    st.session_state.setdefault("wizard_assured_buy", True)
    st.session_state.setdefault("wizard_warranty_avail", False)
    st.session_state.setdefault("wizard_fitness_certificate", True)
    st.session_state.setdefault("wizard_asking_price", 350000)


def get_valuation_form_defaults(options: dict[str, Any]) -> dict[str, Any]:
    """Default widget values for the New Valuation form."""
    make_default = "maruti" if "maruti" in options["makes"] else options["makes"][0]
    model_options = _model_options_for_make(options, make_default)
    model_default = "swift" if "swift" in model_options else model_options[0]
    fuel_default = "petrol" if "petrol" in options["fuel_types"] else options["fuel_types"][0]
    transmission_default = (
        "manual" if "manual" in options["transmissions"] else options["transmissions"][0]
    )
    body_default = (
        "hatchback" if "hatchback" in options["body_types"] else options["body_types"][0]
    )
    city_default = "noida" if "noida" in options["cities"] else options["cities"][0]
    state_default = (
        "uttar pradesh"
        if "uttar pradesh" in options["states"]
        else options["states"][0]
    )
    return {
        "wizard_yr_mfr": 2017,
        "wizard_kms_run": 45000,
        "wizard_owners_select": format_owner_label(1),
        "wizard_make_select": format_category_label(make_default),
        "wizard_model_select": format_category_label(model_default),
        "wizard_fuel_select": format_category_label(fuel_default),
        "wizard_transmission_select": format_category_label(transmission_default),
        "wizard_body_select": format_category_label(body_default),
        "wizard_city_select": format_category_label(city_default),
        "wizard_state_select": format_category_label(state_default),
        "wizard_assured_buy": True,
        "wizard_warranty_avail": False,
        "wizard_fitness_certificate": True,
        "wizard_asking_price": 350000,
    }


def reset_valuation_form(options: dict[str, Any]) -> None:
    """Reset New Valuation widget keys to defaults without deleting keys."""
    for key, value in get_valuation_form_defaults(options).items():
        st.session_state[key] = value
    _sync_wizard_model_for_make(options)


def store_latest_analysis(
    *,
    profile: dict[str, Any],
    result: dict[str, Any],
    report: dict[str, Any],
    vehicle_features: dict[str, Any],
    asking_price: float,
    reference_year: int | None = None,
) -> None:
    """Persist the latest completed analysis as the single source of truth."""
    st.session_state["latest_analysis"] = {
        "profile": profile,
        "result": result,
        "report": report,
        "vehicle_features": vehicle_features,
        "asking_price": float(asking_price),
        "reference_year": int(
            reference_year
            if reference_year is not None
            else max(int(vehicle_features.get("yr_mfr", 2020)) + 1, 2026)
        ),
        "analyzed_at": datetime.now().isoformat(),
    }
    st.session_state.current_result = result
    st.session_state.current_report = report
    st.session_state.current_vehicle_features = vehicle_features
    st.session_state.current_asking_price = float(asking_price)


def get_latest_analysis() -> dict[str, Any] | None:
    """Return the latest analysis bundle, or None if no analysis has been run."""
    latest = st.session_state.get("latest_analysis")
    if isinstance(latest, dict) and latest.get("result") and latest.get("vehicle_features"):
        return latest
    result = st.session_state.get("current_result")
    features = st.session_state.get("current_vehicle_features")
    report = st.session_state.get("current_report")
    if result and features and report:
        return {
            "profile": {},
            "result": result,
            "report": report,
            "vehicle_features": features,
            "asking_price": st.session_state.get("current_asking_price"),
            "analyzed_at": None,
        }
    return None


def _wizard_labeled_selectbox(
    label: str,
    raw_options: list[str],
    session_key: str,
    *,
    fallback_raw: str,
) -> str:
    """Selectbox bound to session state; preserves user selection across reruns."""
    display_options, display_to_raw = build_label_maps(raw_options)
    fallback_display = format_category_label(
        fallback_raw if fallback_raw in raw_options else raw_options[0]
    )
    st.session_state.setdefault(session_key, fallback_display)
    if st.session_state[session_key] not in display_options:
        st.session_state[session_key] = fallback_display
    st.selectbox(label, options=display_options, key=session_key)
    return display_to_raw[st.session_state[session_key]]


def _wizard_owner_selectbox(
    label: str,
    raw_options: list[int],
    session_key: str,
    *,
    fallback_raw: int = 1,
) -> int:
    display_options, display_to_raw = build_owner_maps(raw_options)
    fallback_display = format_owner_label(fallback_raw)
    st.session_state.setdefault(session_key, fallback_display)
    if st.session_state[session_key] not in display_options:
        st.session_state[session_key] = fallback_display
    st.selectbox(label, options=display_options, key=session_key)
    return int(display_to_raw[st.session_state[session_key]])


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "app_view": "dashboard",
        "recent_analyses": [],
        "latest_analysis": None,
        "current_result": None,
        "current_report": None,
        "current_vehicle_features": None,
        "current_asking_price": None,
        "save_notice": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _verdict_recent_class(verdict: str) -> str:
    mapping = {
        "Good Deal": "recent-verdict-good",
        "Fairly Priced": "recent-verdict-fair",
        "Overpriced": "recent-verdict-over",
    }
    return mapping.get(verdict, "recent-verdict-fair")


def render_app_navigation() -> None:
    render_app_branding()
    current_view = str(st.session_state.get("app_view", "dashboard"))
    nav1, nav2, nav3, nav4 = st.columns([1.2, 1.2, 1, 1])
    with nav1:
        if st.button(
            "Dashboard",
            use_container_width=True,
            type="primary" if current_view == "dashboard" else "secondary",
            key="nav_dashboard",
        ):
            st.session_state.app_view = "dashboard"
            st.session_state.save_notice = ""
            st.rerun()
    with nav2:
        if st.button(
            "New Valuation",
            use_container_width=True,
            type="primary" if current_view == "valuation" else "secondary",
            key="nav_new_valuation",
        ):
            st.session_state.app_view = "valuation"
            st.session_state.save_notice = ""
            st.rerun()
    with nav3:
        if st.button(
            "History",
            use_container_width=True,
            type="primary" if current_view == "history" else "secondary",
            key="nav_history",
        ):
            st.session_state.app_view = "history"
            st.session_state.save_notice = ""
            st.rerun()
    with nav4:
        if st.button(
            "About",
            use_container_width=True,
            type="primary" if current_view == "about" else "secondary",
            key="nav_about",
        ):
            st.session_state.app_view = "about"
            st.session_state.save_notice = ""
            st.rerun()


def render_recent_analyses(limit: int | None = None) -> None:
    items = list(st.session_state.recent_analyses)
    if limit is not None:
        items = items[:limit]

    if not items:
        st.markdown(
            '<p class="recent-empty">No saved analyses yet. Run a valuation and use Save Analysis to build your workspace history.</p>',
            unsafe_allow_html=True,
        )
        return

    rows: list[str] = []
    for item in items:
        make = escape(format_category_label(str(item.get("make", ""))))
        model = escape(format_category_label(str(item.get("model", ""))))
        year = int(item.get("yr_mfr", 0))
        fair = float(item.get("fair_value", 0))
        verdict = escape(str(item.get("verdict", "")))
        when = escape(str(item.get("display_time", "")))
        verdict_class = _verdict_recent_class(str(item.get("verdict", "")))
        rows.append(
            f'<div class="recent-item"><div><p class="recent-item-title">{make} {model}</p><p class="recent-item-meta">{year} · {when}</p></div><p class="recent-item-value">₹{format_lakh(fair)}</p><span class="recent-item-verdict {verdict_class}">{verdict}</span></div>'
        )

    st.markdown(
        f'<div class="recent-list">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def render_dashboard(
    *,
    model_name: str,
    listing_count: int,
    feature_count: int,
    r2_score: float,
) -> None:
    st.markdown('<p class="app-view-eyebrow">Dashboard</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-panel"><h1 class="dashboard-title">Vehicle intelligence, ready when you are.</h1><p class="dashboard-copy">Start a new valuation, review recent analyses, and generate a premium AI vehicle intelligence report in minutes.</p></div>',
        unsafe_allow_html=True,
    )

    if st.button("Start New Valuation →", type="primary", key="dashboard_start_valuation"):
        st.session_state.app_view = "valuation"
        st.rerun()

    st.markdown(
        f'<div class="dashboard-stats"><div><p class="dashboard-stat-value">{listing_count:,}+</p><p class="dashboard-stat-label">Training Listings</p></div><div><p class="dashboard-stat-value">{feature_count}</p><p class="dashboard-stat-label">Model Features</p></div><div><p class="dashboard-stat-value">{r2_score:.3f}</p><p class="dashboard-stat-label">Model R² · {escape(model_name)}</p></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="recent-panel"><p class="recent-title">Recent Analyses</p></div>', unsafe_allow_html=True)
    render_recent_analyses(limit=5)


def render_about_page(*, model_name: str, listing_count: int, r2_score: float) -> None:
    st.markdown('<p class="app-view-eyebrow">About</p>', unsafe_allow_html=True)
    st.markdown(
        f"""<div class="about-panel"><h2 class="about-title">AutoValue AI</h2><p class="about-copy">AutoValue AI is a used vehicle valuation workspace powered by machine learning. It estimates fair market value, compares asking prices, and generates structured market intelligence from vehicle listing characteristics.</p><p class="about-copy">Current model: {escape(model_name)} · {listing_count:,}+ training listings · R² {r2_score:.3f}</p><p class="about-copy">Valuation outputs include deal assessment, indicative market range, confidence heuristics, negotiation guidance, and vehicle signals. These are decision-support insights — not guarantees of transaction outcomes.</p></div>""",
        unsafe_allow_html=True,
    )


def render_history_page() -> None:
    st.markdown('<p class="app-view-eyebrow">History</p>', unsafe_allow_html=True)
    st.markdown('<div class="recent-panel"><p class="recent-title">Saved Analyses</p></div>', unsafe_allow_html=True)
    render_recent_analyses()


@st.cache_data(show_spinner=False)
def load_form_options() -> dict[str, Any]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    make_models = (
        df.groupby("make")["model"]
        .apply(lambda s: sorted(s.dropna().unique().tolist()))
        .to_dict()
    )
    return {
        "makes": sorted(df["make"].dropna().unique().tolist()),
        "make_models": make_models,
        "fuel_types": sorted(df["fuel_type"].dropna().unique().tolist()),
        "transmissions": sorted(df["transmission"].dropna().unique().tolist()),
        "body_types": sorted(df["body_type"].dropna().unique().tolist()),
        "cities": sorted(df["city"].dropna().unique().tolist()),
        "states": sorted(df["registered_state"].dropna().unique().tolist()),
        "year_min": int(df["yr_mfr"].min()),
        "year_max": int(df["yr_mfr"].max()),
        "owners": sorted(int(x) for x in df["total_owners"].dropna().unique()),
        "listing_count": len(df),
        "kms_p25": float(df["kms_run"].quantile(0.25)),
        "kms_p75": float(df["kms_run"].quantile(0.75)),
        "kms_median": float(df["kms_run"].median()),
    }


def validate_inputs(
    *,
    yr_mfr: int,
    kms_run: int,
    total_owners: int,
    make: str,
    model: str,
    fuel_type: str,
    transmission: str,
    body_type: str,
    city: str,
    registered_state: str,
    asking_price: float,
    options: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if yr_mfr < options["year_min"] or yr_mfr > options["year_max"]:
        errors.append(
            f"Manufacturing year must be between {options['year_min']} and {options['year_max']}."
        )
    if kms_run <= 0:
        errors.append("Kilometers driven must be greater than zero.")
    if total_owners <= 0:
        errors.append("Number of previous owners must be at least 1.")
    if not make:
        errors.append("Please select a vehicle make.")
    if not model:
        errors.append("Please select a vehicle model.")
    if not fuel_type:
        errors.append("Please select a fuel type.")
    if not transmission:
        errors.append("Please select a transmission type.")
    if not body_type:
        errors.append("Please select a body type.")
    if not city:
        errors.append("Please select a city.")
    if not registered_state:
        errors.append("Please select a registered state.")
    if asking_price <= 0:
        errors.append("Asking price must be greater than zero.")

    return errors


def build_vehicle_features(
    *,
    yr_mfr: int,
    kms_run: int,
    total_owners: int,
    make: str,
    model: str,
    fuel_type: str,
    transmission: str,
    body_type: str,
    city: str,
    registered_state: str,
    assured_buy: bool,
    warranty_avail: bool,
    fitness_certificate: bool,
) -> dict[str, Any]:
    return {
        "yr_mfr": int(yr_mfr),
        "kms_run": int(kms_run),
        "total_owners": int(total_owners),
        "make": make,
        "model": model,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "body_type": body_type,
        "city": city,
        "registered_state": registered_state,
        "assured_buy": bool(assured_buy),
        "warranty_avail": bool(warranty_avail),
        "fitness_certificate": bool(fitness_certificate),
    }


def verdict_styles(verdict: str) -> tuple[str, str, str]:
    """Return symbol, accent color, and CSS verdict class suffix."""
    mapping = {
        "Good Deal": ("✓", COLORS["positive"], "good"),
        "Fairly Priced": ("=", COLORS["caution"], "fair"),
        "Overpriced": ("!", COLORS["negative"], "over"),
    }
    return mapping.get(verdict, ("·", COLORS["caution"], "fair"))


def _delta_tone_class(percentage_difference: float) -> tuple[str, str]:
    """Return CSS classes for difference value and percentage (buyer perspective)."""
    pct = float(percentage_difference)
    if pct < -0.05:
        return "report-metric-value-favorable", "report-delta-positive"
    if pct > 0.05:
        return "report-metric-value-unfavorable", "report-delta-negative"
    return "", "report-delta-neutral"


def _deal_score_class(deal_score: int) -> str:
    if deal_score >= 80:
        return "report-deal-score-strong"
    if deal_score >= 50:
        return "report-deal-score-moderate"
    return "report-deal-score-weak"


def _confidence_class(level: str) -> str:
    normalized = level.strip().upper()
    if normalized == "HIGH":
        return "report-confidence-high"
    if normalized == "LIMITED":
        return "report-confidence-limited"
    return "report-confidence-moderate"


def build_dataset_context(options: dict[str, Any], reference_year: int) -> dict[str, Any]:
    """Dataset coverage context for confidence heuristics."""
    return {
        "reference_year": reference_year,
        "year_min": options["year_min"],
        "year_max": options["year_max"],
        "make_models": options["make_models"],
        "fuel_types": options["fuel_types"],
        "transmissions": options["transmissions"],
        "body_types": options["body_types"],
        "cities": options["cities"],
        "kms_p25": options.get("kms_p25", 0.0),
        "kms_p75": options.get("kms_p75", 0.0),
        "kms_median": options.get("kms_median", 0.0),
    }


def collect_valuation_profile(options: dict[str, Any]) -> dict[str, Any]:
    """Read the current New Valuation form values from session state."""
    init_wizard_state(options)

    make = _raw_make_from_session(options)
    model_options = _model_options_for_make(options, make)
    model = _display_to_raw(
        str(st.session_state.get("wizard_model_select", "")),
        model_options,
        fallback=model_options[0],
    )

    return {
        "yr_mfr": int(st.session_state.get("wizard_yr_mfr", 2017)),
        "kms_run": int(st.session_state.get("wizard_kms_run", 45000)),
        "total_owners": _owner_display_to_raw(
            str(st.session_state.get("wizard_owners_select", format_owner_label(1))),
            options["owners"],
            fallback=1,
        ),
        "make": make,
        "model": model,
        "fuel_type": _display_to_raw(
            str(st.session_state.get("wizard_fuel_select", "")),
            options["fuel_types"],
            fallback=options["fuel_types"][0],
        ),
        "transmission": _display_to_raw(
            str(st.session_state.get("wizard_transmission_select", "")),
            options["transmissions"],
            fallback=options["transmissions"][0],
        ),
        "body_type": _display_to_raw(
            str(st.session_state.get("wizard_body_select", "")),
            options["body_types"],
            fallback=options["body_types"][0],
        ),
        "city": _display_to_raw(
            str(st.session_state.get("wizard_city_select", "")),
            options["cities"],
            fallback=options["cities"][0],
        ),
        "registered_state": _display_to_raw(
            str(st.session_state.get("wizard_state_select", "")),
            options["states"],
            fallback=options["states"][0],
        ),
        "assured_buy": bool(st.session_state.get("wizard_assured_buy", True)),
        "warranty_avail": bool(st.session_state.get("wizard_warranty_avail", False)),
        "fitness_certificate": bool(st.session_state.get("wizard_fitness_certificate", True)),
    }


def render_valuation_page(
    options: dict[str, Any],
    *,
    dataset_context: dict[str, Any],
    reference_year: int,
) -> None:
    """Single scrollable New Valuation page with all form sections."""
    init_wizard_state(options)
    st.markdown('<p class="app-view-eyebrow">New Valuation</p>', unsafe_allow_html=True)

    render_section_header("01", "Vehicle Basics", "Tell us about the vehicle's history and usage.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.number_input(
            "Manufacturing Year",
            min_value=options["year_min"],
            max_value=options["year_max"],
            step=1,
            key="wizard_yr_mfr",
        )
    with c2:
        st.number_input(
            "Kilometers Driven",
            min_value=1,
            max_value=1_000_000,
            step=500,
            key="wizard_kms_run",
        )
    c3, _ = st.columns(2, gap="large")
    with c3:
        _wizard_owner_selectbox(
            "Previous Owners",
            options["owners"],
            "wizard_owners_select",
            fallback_raw=1,
        )

    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    render_section_header("02", "Vehicle Configuration", "Define the vehicle and registration details.")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        make = _wizard_labeled_selectbox(
            "Make",
            options["makes"],
            "wizard_make_select",
            fallback_raw="maruti" if "maruti" in options["makes"] else options["makes"][0],
        )
    with c2:
        _sync_wizard_model_for_make(options)
        model_options = _model_options_for_make(options, make)
        model_fallback = "swift" if "swift" in model_options else model_options[0]
        _wizard_labeled_selectbox(
            "Model",
            model_options,
            "wizard_model_select",
            fallback_raw=model_fallback,
        )

    c3, c4 = st.columns(2, gap="large")
    with c3:
        _wizard_labeled_selectbox(
            "Fuel Type",
            options["fuel_types"],
            "wizard_fuel_select",
            fallback_raw="petrol" if "petrol" in options["fuel_types"] else options["fuel_types"][0],
        )
    with c4:
        _wizard_labeled_selectbox(
            "Transmission",
            options["transmissions"],
            "wizard_transmission_select",
            fallback_raw="manual" if "manual" in options["transmissions"] else options["transmissions"][0],
        )

    c5, _ = st.columns(2, gap="large")
    with c5:
        _wizard_labeled_selectbox(
            "Body Type",
            options["body_types"],
            "wizard_body_select",
            fallback_raw="hatchback" if "hatchback" in options["body_types"] else options["body_types"][0],
        )

    c6, c7 = st.columns(2, gap="large")
    with c6:
        _wizard_labeled_selectbox(
            "City",
            options["cities"],
            "wizard_city_select",
            fallback_raw="noida" if "noida" in options["cities"] else options["cities"][0],
        )
    with c7:
        _wizard_labeled_selectbox(
            "Registered State",
            options["states"],
            "wizard_state_select",
            fallback_raw=(
                "uttar pradesh"
                if "uttar pradesh" in options["states"]
                else options["states"][0]
            ),
        )

    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    render_section_header("03", "Listing & Pricing", "Condition indicators and the seller's asking price.")
    b1, b2, b3 = st.columns(3, gap="large")
    with b1:
        st.checkbox("Assured Buy", key="wizard_assured_buy")
    with b2:
        st.checkbox("Warranty Available", key="wizard_warranty_avail")
    with b3:
        st.checkbox("Fitness Certificate", key="wizard_fitness_certificate")

    st.number_input(
        "Asking Price (₹)",
        min_value=0,
        step=5000,
        format="%d",
        key="wizard_asking_price",
    )
    _render_asking_price_preview()

    st.markdown('<div class="valuation-actions" role="presentation"></div>', unsafe_allow_html=True)
    clear_col, analyze_col = st.columns(2, gap="large")
    with clear_col:
        if st.button("Clear Page", use_container_width=True, key="valuation_clear"):
            reset_valuation_form(options)
            st.rerun()
    with analyze_col:
        if st.button("Analyze Vehicle", type="primary", use_container_width=True, key="valuation_analyze"):
            profile = collect_valuation_profile(options)
            asking_price = float(st.session_state.get("wizard_asking_price", 0))
            errors = validate_inputs(
                asking_price=asking_price,
                options=options,
                **_validation_fields_from_profile(profile),
            )
            if errors:
                for err in errors:
                    st.error(err)
            else:
                pipeline_errors, result, report, features = run_analysis_pipeline(
                    profile=profile,
                    asking_price=asking_price,
                    options=options,
                    dataset_context=dataset_context,
                    reference_year=reference_year,
                )
                if pipeline_errors:
                    for err in pipeline_errors:
                        st.error(err)
                elif result and report and features:
                    store_latest_analysis(
                        profile=profile,
                        result=result,
                        report=report,
                        vehicle_features=features,
                        asking_price=asking_price,
                        reference_year=reference_year,
                    )
                    st.session_state.app_view = "results"
                    st.session_state.save_notice = ""
                    st.rerun()


def run_analysis_pipeline(
    *,
    profile: dict[str, Any],
    asking_price: float,
    options: dict[str, Any],
    dataset_context: dict[str, Any],
    reference_year: int,
) -> tuple[list[str], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    errors = validate_inputs(
        asking_price=asking_price,
        options=options,
        **_validation_fields_from_profile(profile),
    )
    if errors:
        return errors, None, None, None

    vehicle_features = build_vehicle_features(**profile)

    with st.status("Analysing vehicle...", expanded=True) as status:
        st.write("Validating vehicle data")
        st.write("Processing vehicle characteristics")
        st.write("Running valuation model")
        try:
            result = analyze_vehicle_deal(vehicle_features, asking_price)
        except ModelLoadError as exc:
            status.update(label="Analysis failed", state="error")
            return [str(exc)], None, None, None
        except (KeyError, ValueError, RuntimeError) as exc:
            status.update(label="Analysis failed", state="error")
            return [f"Could not analyze this vehicle: {exc}"], None, None, None
        except Exception as exc:  # noqa: BLE001
            status.update(label="Analysis failed", state="error")
            return [f"An unexpected error occurred during prediction: {exc}"], None, None, None

        st.write("Generating market intelligence")
        report = enrich_valuation_report(
            result,
            vehicle_features,
            dataset_context=dataset_context,
            reference_year=reference_year,
        )
        status.update(label="Analysis complete", state="complete")

    return [], result, report, vehicle_features


def save_current_analysis() -> None:
    analysis = get_latest_analysis()
    if not analysis:
        st.session_state.save_notice = "Nothing to save yet. Run an analysis first."
        return

    report = analysis["report"]
    features = analysis["vehicle_features"]

    entry = {
        "display_time": datetime.now().strftime("%b %d, %Y · %I:%M %p"),
        "make": features["make"],
        "model": features["model"],
        "yr_mfr": int(features["yr_mfr"]),
        "fair_value": float(report["predicted_fair_value"]),
        "verdict": str(report["verdict"]),
        "deal_score": int(report.get("deal_score", 0)),
    }
    st.session_state.recent_analyses.insert(0, entry)
    st.session_state.recent_analyses = st.session_state.recent_analyses[:20]
    st.session_state.save_notice = "Analysis saved to your workspace history."


def render_vehicle_identity(vehicle_features: dict[str, Any]) -> None:
    make = escape(format_category_label(str(vehicle_features["make"])))
    model = escape(format_category_label(str(vehicle_features["model"])))
    fuel = escape(format_category_label(str(vehicle_features["fuel_type"])))
    transmission = escape(format_category_label(str(vehicle_features["transmission"])))
    body = escape(format_category_label(str(vehicle_features["body_type"])))
    city = escape(format_category_label(str(vehicle_features["city"])))
    state = escape(format_category_label(str(vehicle_features["registered_state"])))
    owners = int(vehicle_features["total_owners"])
    owner_label = "1 Owner" if owners == 1 else f"{owners} Owners"
    kms = int(vehicle_features["kms_run"])
    year = int(vehicle_features["yr_mfr"])

    st.markdown(
        f"""<div class="vehicle-identity"><p class="app-view-eyebrow">Vehicle Intelligence Report</p><h2 class="vehicle-identity-title">{make} {model}</h2><p class="vehicle-identity-subtitle">{year} · {city}, {state}</p><div class="vehicle-identity-grid"><div><p class="vehicle-identity-item-label">Fuel</p><p class="vehicle-identity-item-value">{fuel}</p></div><div><p class="vehicle-identity-item-label">Transmission</p><p class="vehicle-identity-item-value">{transmission}</p></div><div><p class="vehicle-identity-item-label">Body Type</p><p class="vehicle-identity-item-value">{body}</p></div><div><p class="vehicle-identity-item-label">Kilometers</p><p class="vehicle-identity-item-value">{kms:,} km</p></div><div><p class="vehicle-identity-item-label">Ownership</p><p class="vehicle-identity-item-value">{owner_label}</p></div><div><p class="vehicle-identity-item-label">Assured Buy</p><p class="vehicle-identity-item-value">{"Yes" if vehicle_features.get("assured_buy") else "No"}</p></div><div><p class="vehicle-identity-item-label">Warranty</p><p class="vehicle-identity-item-value">{"Yes" if vehicle_features.get("warranty_avail") else "No"}</p></div><div><p class="vehicle-identity-item-label">Fitness Certificate</p><p class="vehicle-identity-item-value">{"Yes" if vehicle_features.get("fitness_certificate") else "No"}</p></div></div></div>""",
        unsafe_allow_html=True,
    )


def render_result_actions() -> None:
    st.markdown('<div class="result-actions">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            "New Valuation",
            use_container_width=True,
            type="primary",
            key="results_new_valuation",
        ):
            st.session_state.app_view = "valuation"
            st.session_state.save_notice = ""
            st.rerun()
    with c2:
        if st.button("Save Analysis", use_container_width=True, key="results_save_analysis"):
            save_current_analysis()
            st.rerun()
    with c3:
        if st.button("Back to Dashboard", use_container_width=True, key="results_back_dashboard"):
            st.session_state.app_view = "dashboard"
            st.session_state.save_notice = ""
            st.rerun()


def render_results_page(
    *,
    dataset_context: dict[str, Any],
    reference_year: int,
) -> None:
    analysis = get_latest_analysis()
    if not analysis:
        st.warning("No analysis available yet. Start a new valuation.")
        if st.button("Go to Dashboard", key="results_empty_go_dashboard"):
            st.session_state.app_view = "dashboard"
            st.rerun()
        return

    features = analysis["vehicle_features"]
    report = analysis["report"]

    if st.session_state.save_notice:
        st.success(st.session_state.save_notice)

    st.markdown('<div class="results-page">', unsafe_allow_html=True)
    render_results(report, vehicle_features=features)
    render_result_actions()


def _signal_badge(signal: str) -> str:
    mapping = {
        "positive": "↑ POSITIVE",
        "negative": "↓ NEGATIVE",
        "neutral": "• NEUTRAL",
    }
    return mapping.get(signal, "• NEUTRAL")



def render_results(
    report: dict[str, Any],
    *,
    vehicle_features: dict[str, Any],
) -> None:
    """Render the Vehicle Intelligence Report with progressive disclosure."""
    fair = float(report["predicted_fair_value"])
    ask = float(report["asking_price"])
    diff = float(report["price_difference"])
    pct = float(report["percentage_difference"])
    deal_score = int(report.get("deal_score", 0))
    deal_score_class = _deal_score_class(deal_score)
    diff_value_class, diff_pct_class = _delta_tone_class(pct)

    market = report.get("market_range") or {}
    low = float(market.get("low", fair * 0.95))
    high = float(market.get("high", fair * 1.05))
    range_pct = float(market.get("range_pct", 0.05)) * 100

    negotiation = report.get("negotiation") or {}
    opening = float(negotiation.get("opening_offer", fair * 0.97))
    target = float(negotiation.get("target_price", fair))
    max_price = float(negotiation.get("max_recommended", fair * 1.03))
    neg_summary = escape(str(report.get("negotiation_summary", "")))

    confidence = report.get("confidence") or {}
    conf_level = escape(str(confidence.get("level", "MODERATE")))
    conf_score = int(confidence.get("score", 0))
    conf_explanation = escape(str(confidence.get("explanation", "")))
    confidence_class = _confidence_class(str(confidence.get("level", "MODERATE")))

    make = escape(format_category_label(str(vehicle_features.get("make", ""))))
    model = escape(format_category_label(str(vehicle_features.get("model", ""))))
    year = int(vehicle_features.get("yr_mfr", 0))
    city = escape(format_category_label(str(vehicle_features.get("city", ""))))
    fuel = escape(format_category_label(str(vehicle_features.get("fuel_type", ""))))
    transmission = escape(format_category_label(str(vehicle_features.get("transmission", ""))))
    body = escape(format_category_label(str(vehicle_features.get("body_type", ""))))
    kms = int(vehicle_features.get("kms_run", 0))
    owners = int(vehicle_features.get("total_owners", 1))
    owner_label = "1 Owner" if owners == 1 else f"{owners} Owners"
    assured = "Yes" if vehicle_features.get("assured_buy") else "No"
    warranty = "Yes" if vehicle_features.get("warranty_avail") else "No"
    fitness = "Yes" if vehicle_features.get("fitness_certificate") else "No"

    recommendation = report.get("purchase_recommendation")
    if not isinstance(recommendation, dict) or not recommendation.get("badge"):
        latest = get_latest_analysis() or {}
        reference_year = int(
            latest.get("reference_year")
            or max(int(vehicle_features.get("yr_mfr", 2020)) + 1, 2026)
        )
        recommendation = build_purchase_recommendation(
            report,
            vehicle_features,
            reference_year=reference_year,
        )

    rec_tone = escape(str(recommendation.get("tone", "caution")))
    rec_badge = escape(str(recommendation.get("badge", "CONSIDER")))
    rec_icon = escape(str(recommendation.get("icon", "!")))
    executive_verdict = escape(
        str(
            recommendation.get(
                "executive_verdict",
                recommendation.get("verdict_label", "Review Carefully"),
            )
        )
    )
    # Short verdict support line (not the full guidance paragraph).
    verdict_support = escape(
        str(
            recommendation.get(
                "stance",
                recommendation.get("support_summary", ""),
            )
        )
    )
    guidance_summary = escape(
        str(
            recommendation.get(
                "guidance_summary",
                recommendation.get("summary", ""),
            )
        )
    )
    action_line = escape(
        str(
            recommendation.get(
                "action_line",
                recommendation.get("verdict_detail", ""),
            )
        )
    )
    disclaimer = escape(
        str(
            recommendation.get(
                "disclaimer",
                "Important: This recommendation is generated from available listing data "
                "and AI valuation signals. It is intended as decision support and does not "
                "replace a professional mechanical inspection, legal verification, or "
                "independent vehicle assessment.",
            )
        )
    )

    decision_positives = recommendation.get("decision_positives") or []
    decision_risks = recommendation.get("decision_risks") or []

    if decision_positives:
        positives_html = "".join(
            f'<div class="vir-signal vir-signal-positive">'
            f'<span class="vir-signal-mark" aria-hidden="true">✓</span>'
            f"<span>{escape(str(item))}</span></div>"
            for item in decision_positives
        )
    else:
        positives_html = (
            '<div class="vir-signal-empty">No standout positive signals identified.</div>'
        )

    if decision_risks:
        risks_html = "".join(
            f'<div class="vir-signal vir-signal-{escape(str(item.get("severity", "caution")))}">'
            f'<span class="vir-signal-mark" aria-hidden="true">'
            f'{"✕" if str(item.get("severity")) == "critical" else "⚠"}'
            f"</span>"
            f"<span>{escape(str(item.get('text', '')))}</span></div>"
            for item in decision_risks
            if isinstance(item, dict)
        )
    else:
        risks_html = (
            '<div class="vir-signal-empty">'
            "No major valuation concerns detected from the available vehicle data."
            "</div>"
        )

    next_steps = recommendation.get("next_steps") or []
    if not next_steps and recommendation.get("checklist"):
        next_steps = [
            {"icon": "✓", "text": str(item)} for item in recommendation["checklist"]
        ]
    steps_html = "".join(
        f'<div class="vir-step">'
        f'<span class="vir-step-mark" aria-hidden="true">✓</span>'
        f"<span>{escape(str(step.get('text', '')))}</span></div>"
        for step in next_steps
        if isinstance(step, dict) and step.get("text")
    )
    if not steps_html:
        steps_html = (
            '<div class="vir-step"><span class="vir-step-mark" aria-hidden="true">✓</span>'
            "<span>Inspect the vehicle physically before purchase</span></div>"
        )

    factor_rows = []
    for factor in report.get("valuation_factors") or []:
        label = escape(str(factor.get("label", "")))
        signal = str(factor.get("signal", "neutral"))
        text = escape(str(factor.get("text", "")))
        badge = _signal_badge(signal)
        factor_rows.append(
            '<div class="report-factor"><div class="report-factor-head">'
            f'<span class="report-factor-label">{label}</span>'
            f'<span class="report-factor-signal signal-{signal}">{badge}</span>'
            f'</div><p class="report-factor-text">{text}</p></div>'
        )
    factors_html = "".join(factor_rows) or (
        '<p class="report-body-copy">No valuation factor signals available for this listing.</p>'
    )

    if ask > high:
        ask_vs_range = "The asking price sits above the indicative market range."
    elif ask < low:
        ask_vs_range = "The asking price sits below the indicative market range."
    else:
        ask_vs_range = (
            "The asking price falls within the indicative market range around the AI estimate."
        )

    report_html = (
        f'<div class="valuation-report vir-report">'
        f'<section class="vir-exec vir-tone-{rec_tone}" aria-label="Executive summary">'
        f'<p class="vir-eyebrow">Vehicle Intelligence Report</p>'
        f'<h2 class="vir-title">{make} {model}</h2>'
        f'<p class="vir-subtitle">{year} · {city} · {fuel} · {transmission}</p>'
        f'<div class="vir-metric-grid">'
        f'<div class="vir-metric vir-metric-primary">'
        f'<p class="vir-metric-label">AI Fair Value</p>'
        f'<p class="vir-metric-value">₹{format_lakh(fair)}</p>'
        f'<p class="vir-metric-sub">{format_inr(fair)}</p>'
        f"</div>"
        f'<div class="vir-metric">'
        f'<p class="vir-metric-label">Asking Price</p>'
        f'<p class="vir-metric-value">{format_lakh_compact(ask)}</p>'
        f'<p class="vir-metric-sub">{format_inr(ask)}</p>'
        f"</div>"
        f'<div class="vir-metric">'
        f'<p class="vir-metric-label">Difference</p>'
        f'<p class="vir-metric-value {diff_value_class}">{format_signed_inr(diff)}</p>'
        f'<p class="vir-metric-sub {diff_pct_class}">{format_signed_pct(pct)}</p>'
        f"</div>"
        f'<div class="vir-metric vir-metric-score">'
        f'<p class="vir-metric-label">Deal Score</p>'
        f'<p class="vir-metric-value {deal_score_class}">'
        f'<span class="vir-score-num">{deal_score}</span>'
        f'<span class="vir-score-denom">/100</span>'
        f"</p>"
        f"</div>"
        f"</div>"
        f'<div class="vir-verdict-strip" role="status">'
        f'<span class="vir-badge"><span aria-hidden="true">{rec_icon}</span> {rec_badge}</span>'
        f'<p class="vir-verdict-title">{executive_verdict}</p>'
        f"</div>"
        f"</section>"
        f'<section class="vir-block" aria-labelledby="vir-verdict-heading">'
        f'<p class="vir-block-eyebrow" id="vir-verdict-heading">AI Verdict</p>'
        f'<p class="vir-verdict-headline vir-tone-text-{rec_tone}">{executive_verdict}</p>'
        f'<p class="vir-verdict-copy">{verdict_support}</p>'
        f"</section>"
        f'<section class="vir-block" aria-labelledby="vir-signals-heading">'
        f'<p class="vir-block-eyebrow" id="vir-signals-heading">Key Decision Signals</p>'
        f'<div class="vir-signals-grid">'
        f'<div class="vir-signals-col">'
        f'<p class="vir-signals-label">Positive Signals</p>'
        f'<div class="vir-signals-list">{positives_html}</div>'
        f"</div>"
        f'<div class="vir-signals-col">'
        f'<p class="vir-signals-label">Risks / Attention Required</p>'
        f'<div class="vir-signals-list">{risks_html}</div>'
        f"</div>"
        f"</div>"
        f"</section>"
        f'<section class="vir-block vir-guidance" aria-labelledby="vir-guidance-heading">'
        f'<p class="vir-block-eyebrow" id="vir-guidance-heading">AI Purchase Guidance</p>'
        f'<p class="vir-guidance-copy">{guidance_summary}</p>'
        f'<p class="vir-action-line">{action_line}</p>'
        f'<p class="vir-steps-label">Next Steps Before Purchase</p>'
        f'<div class="vir-steps">{steps_html}</div>'
        f"</section>"
        f"</div>"
    )
    st.markdown(report_html, unsafe_allow_html=True)

    st.markdown(
        '<div class="vir-detail-sections" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )

    valuation_detail_html = (
        f'<div class="vir-detail">'
        f'<p class="vir-detail-note">Indicative market range (±{range_pct:.0f}%) around the AI estimate — '
        f"not a statistically calibrated prediction interval.</p>"
        f'<div class="report-range-grid">'
        f'<div class="report-range-point"><p class="report-range-label">Low Estimate</p>'
        f'<p class="report-range-value">{format_lakh_compact(low)}</p></div>'
        f'<div class="report-range-point report-range-point-mid"><p class="report-range-label">AI Estimate</p>'
        f'<p class="report-range-value">{format_lakh_compact(fair)}</p></div>'
        f'<div class="report-range-point"><p class="report-range-label">High Estimate</p>'
        f'<p class="report-range-value">{format_lakh_compact(high)}</p></div>'
        f"</div>"
        f'<div class="report-range-track">'
        f'<div class="report-range-line"></div>'
        f'<div class="report-range-marker report-range-low"></div>'
        f'<div class="report-range-marker report-range-mid"></div>'
        f'<div class="report-range-marker report-range-high"></div>'
        f"</div>"
        f'<p class="report-body-copy">{escape(ask_vs_range)} Asking {format_lakh_compact(ask)} versus '
        f"AI fair value {format_lakh_compact(fair)} ({format_signed_pct(pct)}).</p>"
        f"</div>"
    )

    factors_detail_html = (
        f'<div class="vir-detail">'
        f'<p class="vir-detail-note">Heuristic factor signals based on submitted vehicle characteristics — '
        f"not exact model feature importance.</p>"
        f'<div class="vir-spec-chip-row">'
        f'<span class="vir-chip">{body}</span>'
        f'<span class="vir-chip">{kms:,} km</span>'
        f'<span class="vir-chip">{owner_label}</span>'
        f'<span class="vir-chip">Assured Buy: {assured}</span>'
        f'<span class="vir-chip">Warranty: {warranty}</span>'
        f'<span class="vir-chip">Fitness: {fitness}</span>'
        f"</div>"
        f'<div class="report-factor-list">{factors_html}</div>'
        f"</div>"
    )

    negotiation_detail_html = (
        f'<div class="vir-detail">'
        f'<p class="vir-detail-note">AI-generated negotiation anchors — not guarantees of transaction outcomes.</p>'
        f'<div class="report-negotiation-grid">'
        f'<div class="report-negotiation-item"><p class="report-metric-label">Opening Offer</p>'
        f'<p class="report-metric-value">{format_lakh_compact(opening)}</p></div>'
        f'<div class="report-negotiation-item"><p class="report-metric-label">Target Price</p>'
        f'<p class="report-metric-value">{format_lakh_compact(target)}</p></div>'
        f'<div class="report-negotiation-item"><p class="report-metric-label">Max Recommended</p>'
        f'<p class="report-metric-value">{format_lakh_compact(max_price)}</p></div>'
        f"</div>"
        f'<p class="report-body-copy">{neg_summary}</p>'
        f"</div>"
    )

    confidence_detail_html = (
        f'<div class="vir-detail">'
        f'<p class="report-section-label">Prediction Confidence</p>'
        f'<div class="report-confidence-row">'
        f'<p class="report-confidence-level {confidence_class}">{conf_level}</p>'
        f'<p class="report-confidence-score">{conf_score}%</p>'
        f"</div>"
        f'<p class="report-body-copy">{conf_explanation}</p>'
        f'<p class="report-body-copy">Valuations are model estimates derived from historical listing '
        f"characteristics. Local demand, condition, accident history, and documentation quality can "
        f"move realised prices outside this range.</p>"
        f"</div>"
    )

    disclaimer_html = (
        f'<div class="vir-disclaimer" role="note">'
        f'<span class="vir-disclaimer-icon" aria-hidden="true">ⓘ</span>'
        f"<p>{disclaimer}</p>"
        f"</div>"
    )

    with st.expander("Detailed Valuation Analysis", expanded=False):
        st.markdown(valuation_detail_html, unsafe_allow_html=True)

    with st.expander("What's Driving This Valuation?", expanded=False):
        st.markdown(factors_detail_html, unsafe_allow_html=True)

    with st.expander("Negotiation Guidance", expanded=False):
        st.markdown(negotiation_detail_html, unsafe_allow_html=True)

    with st.expander("Confidence & Methodology", expanded=False):
        st.markdown(confidence_detail_html, unsafe_allow_html=True)

    st.markdown(disclaimer_html, unsafe_allow_html=True)



def main() -> None:
    init_session_state()
    render_app_navigation()

    try:
        metadata = load_metadata()
        options = load_form_options()
    except ModelLoadError as exc:
        st.error(str(exc))
        st.stop()
    except FileNotFoundError as exc:
        st.error(f"Configuration data missing: {exc}")
        st.stop()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unable to initialize the application: {exc}")
        st.stop()

    model_name = str(metadata.get("selected_model_name", "XGBRegressor"))
    r2_score = float(metadata.get("evaluation_metrics", {}).get("R2", 0.912))
    feature_count = len(metadata.get("feature_list", []))
    listing_count = int(options.get("listing_count", 7400))
    reference_year = int(metadata.get("reference_year", 2026))
    dataset_context = build_dataset_context(options, reference_year)
    init_wizard_state(options)

    view = str(st.session_state.app_view)

    if view == "dashboard":
        render_dashboard(
            model_name=model_name,
            listing_count=listing_count,
            feature_count=feature_count,
            r2_score=r2_score,
        )
    elif view == "about":
        render_about_page(model_name=model_name, listing_count=listing_count, r2_score=r2_score)
    elif view == "history":
        render_history_page()
    elif view == "valuation":
        render_valuation_page(
            options,
            dataset_context=dataset_context,
            reference_year=reference_year,
        )
    elif view == "results":
        render_results_page(dataset_context=dataset_context, reference_year=reference_year)
    else:
        st.session_state.app_view = "dashboard"
        render_dashboard(
            model_name=model_name,
            listing_count=listing_count,
            feature_count=feature_count,
            r2_score=r2_score,
        )


if __name__ == "__main__":
    main()
