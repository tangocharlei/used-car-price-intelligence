"""
Display formatting helpers for the AutoValue AI frontend.

UI-only — does not affect model inputs or predictions.
"""

from __future__ import annotations

from html import escape
from typing import Any, Mapping


def format_inr(value: float) -> str:
    """Format a number using Indian grouping (e.g. 4,73,544)."""
    rounded = int(round(float(value)))
    sign = "-" if rounded < 0 else ""
    digits = str(abs(rounded))
    if len(digits) <= 3:
        return f"{sign}{digits}"
    last3 = digits[-3:]
    rest = digits[:-3]
    groups: list[str] = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return f"{sign}{','.join(groups + [last3])}"


def format_lakh(value: float, *, decimals: int = 2) -> str:
    """Format rupee value in lakh notation (e.g. 473544 -> 4.73 Lakh)."""
    rounded_rupees = int(round(float(value)))
    lakh = abs(rounded_rupees) / 100_000.0
    formatted = f"{lakh:.{decimals}f}"
    prefix = "−" if rounded_rupees < 0 else ""
    return f"{prefix}{formatted} Lakh"


def format_lakh_compact(value: float, *, decimals: int = 2) -> str:
    """Compact lakh label for report grids (e.g. 828000 -> ₹8.28 L)."""
    rounded_rupees = int(round(float(value)))
    lakh = abs(rounded_rupees) / 100_000.0
    formatted = f"{lakh:.{decimals}f}"
    prefix = "−₹" if rounded_rupees < 0 else "₹"
    return f"{prefix}{formatted} L"


def format_signed_inr(value: float) -> str:
    """Signed rupee delta with Indian grouping."""
    rounded = int(round(float(value)))
    if rounded > 0:
        return f"+₹{format_inr(rounded)}"
    if rounded < 0:
        return f"−₹{format_inr(abs(rounded))}"
    return "₹0"


def format_signed_pct(value: float, *, decimals: int = 1) -> str:
    """Signed percentage string."""
    pct = float(value)
    if pct > 0:
        return f"+{pct:.{decimals}f}%"
    if pct < 0:
        return f"−{abs(pct):.{decimals}f}%"
    return f"{pct:.{decimals}f}%"


def verdict_summary(verdict: str, pct: float) -> str:
    """Short editorial summary line for the verdict."""
    magnitude = abs(round(pct))
    if verdict == "Good Deal":
        return f"{magnitude}% below estimated fair value"
    if verdict == "Overpriced":
        return f"{magnitude}% above estimated fair value"
    return f"{magnitude}% from estimated fair value"


def _signal_badge(signal: str) -> str:
    mapping = {
        "positive": "↑ POSITIVE",
        "negative": "↓ NEGATIVE",
        "neutral": "• NEUTRAL",
    }
    return mapping.get(signal, "• NEUTRAL")


def build_valuation_report_html(
    report: Mapping[str, Any],
    *,
    accent: str,
    verdict_class: str,
) -> str:
    """Render the full AI Valuation Report markup."""
    fair = float(report["predicted_fair_value"])
    ask = float(report["asking_price"])
    diff = float(report["price_difference"])
    pct = float(report["percentage_difference"])
    verdict = str(report["verdict"])
    summary = verdict_summary(verdict, pct)
    deal_score = int(report.get("deal_score", 0))
    deal_summary = escape(str(report.get("deal_assessment_summary", "")))

    market = report.get("market_range") or {}
    low = float(market.get("low", 0))
    high = float(market.get("high", 0))
    range_pct = float(market.get("range_pct", 0.05)) * 100

    negotiation = report.get("negotiation") or {}
    opening = float(negotiation.get("opening_offer", 0))
    target = float(negotiation.get("target_price", fair))
    max_price = float(negotiation.get("max_recommended", 0))
    neg_summary = escape(str(report.get("negotiation_summary", "")))

    confidence = report.get("confidence") or {}
    conf_level = escape(str(confidence.get("level", "MODERATE")))
    conf_score = int(confidence.get("score", 0))
    conf_explanation = escape(str(confidence.get("explanation", "")))

    factors = report.get("valuation_factors") or []
    factor_rows = []
    for factor in factors:
        label = escape(str(factor.get("label", "")))
        signal = str(factor.get("signal", "neutral"))
        text = escape(str(factor.get("text", "")))
        badge = _signal_badge(signal)
        factor_rows.append(
            f"""
            <div class="report-factor">
                <div class="report-factor-head">
                    <span class="report-factor-label">{label}</span>
                    <span class="report-factor-signal signal-{signal}">{badge}</span>
                </div>
                <p class="report-factor-text">{text}</p>
            </div>
            """
        )

    signals = report.get("vehicle_signals") or {}
    positive = signals.get("positive") or []
    considerations = signals.get("considerations") or []

    positive_html = "".join(
        f'<li><span class="signal-mark positive-mark">✓</span> {escape(str(item))}</li>'
        for item in positive
    )
    if not positive_html:
        positive_html = (
            '<li class="report-signal-empty">No standout positive signals identified.</li>'
        )

    if considerations:
        consider_html = "".join(
            f'<li><span class="signal-mark consider-mark">!</span> {escape(str(item))}</li>'
            for item in considerations
        )
    else:
        consider_html = (
            "<li class=\"report-signal-empty\">"
            "No major valuation concerns detected from the available inputs."
            "</li>"
        )

    symbol_map = {"Good Deal": "✓", "Fairly Priced": "=", "Overpriced": "!"}
    symbol = symbol_map.get(verdict, "·")

    return f"""
<div class="valuation-report">
    <section class="report-section report-hero">
        <p class="result-eyebrow">AI Valuation Result</p>
        <p class="result-value-large">₹{format_lakh(fair)}</p>
        <p class="result-value-label">Estimated Fair Market Value</p>

        <div class="report-metrics-grid">
            <div class="report-metric">
                <p class="report-metric-label">Asking Price</p>
                <p class="report-metric-value">{format_lakh_compact(ask)}</p>
                <p class="report-metric-sub">{format_inr(ask)}</p>
            </div>
            <div class="report-metric">
                <p class="report-metric-label">AI Fair Value</p>
                <p class="report-metric-value">{format_lakh_compact(fair)}</p>
                <p class="report-metric-sub">{format_inr(fair)}</p>
            </div>
            <div class="report-metric">
                <p class="report-metric-label">Difference</p>
                <p class="report-metric-value">{format_signed_inr(diff)}</p>
                <p class="report-metric-sub report-metric-delta">{format_signed_pct(pct)}</p>
            </div>
        </div>
    </section>

    <section class="report-section">
        <p class="report-section-eyebrow">Deal Assessment</p>
        <div class="report-deal-row">
            <div>
                <p class="report-section-label">Deal Score</p>
                <p class="report-deal-score">{deal_score}<span>/100</span></p>
            </div>
            <div class="verdict-large verdict-{verdict_class}">
                <p class="verdict-symbol" style="color:{accent};">{symbol}</p>
                <p class="verdict-title" style="color:{accent};">{escape(verdict)}</p>
                <p class="verdict-summary">{escape(summary)}</p>
            </div>
        </div>
        <p class="report-body-copy">{deal_summary}</p>
    </section>

    <section class="report-section">
        <p class="report-section-eyebrow">Market Value Range</p>
        <p class="report-section-note">
            Indicative market range (±{range_pct:.0f}%) around the AI estimate — not a
            statistically calibrated prediction interval.
        </p>
        <div class="report-range-grid">
            <div class="report-range-point">
                <p class="report-range-label">Low Estimate</p>
                <p class="report-range-value">{format_lakh_compact(low)}</p>
            </div>
            <div class="report-range-point report-range-point-mid">
                <p class="report-range-label">AI Estimate</p>
                <p class="report-range-value">{format_lakh_compact(fair)}</p>
            </div>
            <div class="report-range-point">
                <p class="report-range-label">High Estimate</p>
                <p class="report-range-value">{format_lakh_compact(high)}</p>
            </div>
        </div>
        <div class="report-range-track">
            <div class="report-range-line"></div>
            <div class="report-range-marker report-range-low"></div>
            <div class="report-range-marker report-range-mid"></div>
            <div class="report-range-marker report-range-high"></div>
        </div>
    </section>

    <section class="report-section">
        <p class="report-section-eyebrow">What's Driving This Valuation?</p>
        <p class="report-section-note">
            Heuristic factor signals based on submitted vehicle characteristics — not exact
            model feature importance.
        </p>
        <div class="report-factor-list">
            {''.join(factor_rows)}
        </div>
    </section>

    <section class="report-section">
        <p class="report-section-eyebrow">AI Confidence</p>
        <p class="report-section-label">Prediction Confidence</p>
        <div class="report-confidence-row">
            <p class="report-confidence-level">{conf_level}</p>
            <p class="report-confidence-score">{conf_score}%</p>
        </div>
        <p class="report-body-copy">{conf_explanation}</p>
    </section>

    <section class="report-section">
        <p class="report-section-eyebrow">Negotiation Guidance</p>
        <p class="report-section-note">
            AI-generated negotiation anchors — not guarantees of transaction outcomes.
        </p>
        <div class="report-negotiation-grid">
            <div class="report-negotiation-item">
                <p class="report-metric-label">Opening Offer</p>
                <p class="report-metric-value">{format_lakh_compact(opening)}</p>
            </div>
            <div class="report-negotiation-item">
                <p class="report-metric-label">Target Price</p>
                <p class="report-metric-value">{format_lakh_compact(target)}</p>
            </div>
            <div class="report-negotiation-item">
                <p class="report-metric-label">Max Recommended</p>
                <p class="report-metric-value">{format_lakh_compact(max_price)}</p>
            </div>
        </div>
        <p class="report-body-copy">{neg_summary}</p>
    </section>

    <section class="report-section report-section-last">
        <p class="report-section-eyebrow">Vehicle Signals</p>
        <div class="report-signals-grid">
            <div class="report-signals-col">
                <p class="report-signals-title">Positive Signals</p>
                <ul class="report-signals-list">{positive_html}</ul>
            </div>
            <div class="report-signals-col">
                <p class="report-signals-title">Things to Consider</p>
                <ul class="report-signals-list">{consider_html}</ul>
            </div>
        </div>
    </section>
</div>
"""
