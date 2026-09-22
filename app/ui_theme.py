"""
Premium editorial theme for AutoValue AI.

Typography-led monochrome aesthetic — Space Grotesk + Inter.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "images" / "hero_car.jpg"

COLORS = {
    "bg": "#0A0A0F",
    "surface": "#12121A",
    "surface_hover": "#161622",
    "text": "#F5F5F5",
    "text_soft": "#E8E6E1",
    "muted": "#777782",
    "label": "#A0A0A0",
    "border": "#22222D",
    "border_hover": "#33333F",
    "accent": "#F5F5F5",
    "accent_text": "#0A0A0F",
    "positive": "#22C55E",
    "negative": "#FF4D4F",
    "caution": "#F59E0B",
    "informational": "#38BDF8",
    "neutral": "#F59E0B",
}

FONT_DISPLAY = '"Space Grotesk", sans-serif'
FONT_BODY = '"Inter", sans-serif'

TRANSITION = (
    "transform 0.25s ease, border-color 0.25s ease, "
    "background-color 0.25s ease, box-shadow 0.25s ease"
)

REVEAL_EASING = "cubic-bezier(0.22, 1, 0.36, 1)"
REVEAL_DURATION = "650ms"


def _hero_background() -> str:
    if not HERO_IMAGE_PATH.exists():
        return f"linear-gradient(180deg, {COLORS['surface']} 0%, {COLORS['bg']} 100%)"
    encoded = base64.b64encode(HERO_IMAGE_PATH.read_bytes()).decode("utf-8")
    return (
        "linear-gradient(115deg, rgba(10,10,15,0.94) 0%, rgba(10,10,15,0.88) 55%, "
        "rgba(10,10,15,0.96) 100%), "
        f"url('data:image/jpeg;base64,{encoded}')"
    )


def inject_global_styles() -> None:
    c = COLORS
    hero_bg = _hero_background()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        html {{
            height: auto !important;
            max-height: none !important;
            min-height: 100%;
            overflow-x: clip;
            overflow-y: scroll !important;
        }}

        body {{
            font-family: {FONT_BODY};
            height: auto !important;
            max-height: none !important;
            min-height: 100%;
            overflow-x: clip;
            overflow-y: visible !important;
        }}

        [class*="css"] {{
            font-family: {FONT_BODY};
        }}

        .stApp,
        div[data-testid="stApp"] {{
            background: {c['bg']};
            color: {c['text_soft']};
            height: auto !important;
            min-height: 100vh;
            max-height: none !important;
            overflow: visible !important;
        }}

        section[data-testid="stAppViewContainer"],
        section[data-testid="stMain"],
        div[data-testid="stMainBlockContainer"],
        section.main,
        .main,
        .main .block-container {{
            background: {c['bg']} !important;
        }}

        section[data-testid="stAppViewContainer"],
        .appview-container {{
            overflow: visible !important;
            height: auto !important;
            min-height: 100vh;
            max-height: none !important;
        }}

        section[data-testid="stMain"],
        section.main,
        .main,
        div[data-testid="stMainBlockContainer"] {{
            height: auto !important;
            min-height: auto !important;
            max-height: none !important;
            overflow: visible !important;
            flex: 1 1 auto !important;
        }}

        div[data-testid="stVerticalBlock"],
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
        }}

        /* Collapsed Streamlit chrome only — must not clip page content */
        header[data-testid="stHeader"] {{
            background: {c['bg']} !important;
            border-bottom: none;
            height: 0 !important;
            min-height: 0 !important;
            overflow: hidden;
            visibility: hidden;
            pointer-events: none !important;
        }}

        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {{
            display: none !important;
            pointer-events: none !important;
        }}

        .block-container {{
            padding-top: 1rem;
            padding-bottom: 120px !important;
            max-width: 980px;
            min-height: 100vh;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
        }}

        .stCaption {{ color: {c['muted']} !important; font-family: {FONT_BODY}; }}

        /* ── Header ── */
        .site-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 0 0.75rem;
            margin-bottom: 0.5rem;
        }}
        .brand-mark {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}
        .brand-right {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.65rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
        }}

        /* ── Hero ── */
        .hero {{
            position: relative;
            padding: 3.5rem 0 3rem;
            margin-bottom: 2.5rem;
            background: {hero_bg};
            background-size: cover;
            background-position: center right;
            border-bottom: 1px solid {c['border']};
        }}
        .hero-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.68rem;
            font-weight: 500;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin: 0 0 1.25rem 0;
        }}
        .hero-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(2.6rem, 6.5vw, 4.25rem);
            font-weight: 500;
            line-height: 1.04;
            letter-spacing: -0.035em;
            margin: 0 0 1.35rem 0;
            max-width: 720px;
        }}
        .hero-copy {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 1.02rem;
            line-height: 1.7;
            margin: 0 0 1.5rem 0;
            max-width: 560px;
        }}
        .hero-meta {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.72rem;
            letter-spacing: 0.04em;
            margin: 0 0 2rem 0;
        }}
        .hero-cta {{
            display: inline-block;
            font-family: {FONT_BODY};
            color: {c['accent_text']};
            background: {c['accent']};
            padding: 0.82rem 1.45rem;
            border-radius: 8px;
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            text-decoration: none;
            transition: {TRANSITION};
        }}
        .hero-cta:hover {{
            transform: translateY(-2px);
            background: #FFFFFF;
            box-shadow: 0 8px 24px rgba(255, 255, 255, 0.06);
        }}

        /* ── Stats strip ── */
        .stats-strip {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            padding: 2.5rem 0 3rem;
            border-bottom: 1px solid {c['border']};
            margin-bottom: 1rem;
        }}
        .stat-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.6rem, 3vw, 2rem);
            font-weight: 500;
            letter-spacing: -0.03em;
            margin: 0 0 0.35rem 0;
        }}
        .stat-label {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }}

        /* ── Form sections ── */
        .form-shell {{
            scroll-margin-top: 2rem;
        }}
        .section-head {{
            margin: 1.5rem 0 1.1rem;
        }}
        .section-number {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.78rem;
            font-weight: 500;
            letter-spacing: 0.08em;
            margin: 0 0 0.45rem 0;
        }}
        .section-title {{
            font-family: {FONT_DISPLAY};
            font-size: clamp(1.6rem, 2vw, 2.2rem);
            font-weight: 500;
            letter-spacing: -0.03em;
            color: {c['text']};
            line-height: 1.12;
            margin: 0 0 0.55rem 0;
        }}
        .section-desc {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.92rem;
            line-height: 1.6;
            margin: 0;
            max-width: 520px;
        }}
        .section-rule {{
            border: none;
            border-top: 1px solid {c['border']};
            margin: 0 0 1.5rem 0;
        }}

        /* ── Form labels ── */
        label[data-testid="stWidgetLabel"] p,
        .stSelectbox label p,
        .stNumberInput label p {{
            font-family: {FONT_BODY} !important;
            color: {c['label']} !important;
            font-size: 0.88rem !important;
            letter-spacing: 0.02em !important;
            font-weight: 500 !important;
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            font-family: {FONT_BODY};
            background-color: {c['surface']} !important;
            border: 1px solid {c['border']} !important;
            border-radius: 8px !important;
            min-height: 2.65rem;
            transition: {TRANSITION};
        }}

        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="input"] > div:hover {{
            background-color: {c['surface_hover']} !important;
            border-color: {c['border_hover']} !important;
        }}

        div[data-baseweb="select"]:focus-within > div,
        div[data-baseweb="input"]:focus-within > div {{
            border-color: {c['text']} !important;
            box-shadow: 0 0 0 1px rgba(245, 245, 245, 0.12) !important;
        }}

        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] input {{
            font-family: {FONT_BODY} !important;
            color: {c['text_soft']} !important;
        }}

        div[data-testid="stCheckbox"] label p {{
            font-family: {FONT_BODY} !important;
            color: {c['text_soft']} !important;
            font-size: 0.88rem !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}

        /* ── Primary button ── */
        div[data-testid="stButton"] > button[kind="primary"] {{
            font-family: {FONT_BODY} !important;
            background: {c['accent']} !important;
            color: {c['accent_text']} !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.85rem 1.65rem !important;
            font-weight: 600 !important;
            font-size: 0.74rem !important;
            letter-spacing: 0.1em !important;
            text-transform: uppercase !important;
            transition: {TRANSITION} !important;
        }}
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            transform: translateY(-2px);
            background: #FFFFFF !important;
            box-shadow: 0 8px 24px rgba(255, 255, 255, 0.06);
        }}

        div[data-testid="stButton"] > button[kind="secondary"],
        div[data-testid="stButton"] > button:not([kind="primary"]) {{
            font-family: {FONT_BODY} !important;
            background: {c['surface']} !important;
            color: {c['text_soft']} !important;
            border: 1px solid {c['border']} !important;
            border-radius: 8px !important;
            padding: 0.85rem 1.65rem !important;
            font-weight: 500 !important;
            font-size: 0.74rem !important;
            letter-spacing: 0.08em !important;
            transition: {TRANSITION} !important;
        }}
        div[data-testid="stButton"] > button[kind="secondary"]:hover,
        div[data-testid="stButton"] > button:not([kind="primary"]):hover {{
            background: {c['surface_hover']} !important;
            border-color: {c['border_hover']} !important;
            transform: translateY(-2px);
        }}

        .action-row {{
            margin: 3.25rem 0 1.5rem;
            padding-top: 2rem;
            border-top: 1px solid {c['border']};
        }}

        /* ── Results ── */
        .result-block {{
            margin-top: 4.5rem;
            padding-top: 3.5rem;
            border-top: 1px solid {c['border']};
        }}
        .result-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.68rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 500;
            margin: 0 0 1.75rem 0;
        }}
        .result-value-large {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(2.8rem, 7vw, 4.5rem);
            font-weight: 500;
            letter-spacing: -0.04em;
            line-height: 1;
            margin: 0 0 0.65rem 0;
        }}
        .result-value-label {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.74rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin: 0 0 2.5rem 0;
        }}
        .result-asking {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin: 0 0 0.35rem 0;
        }}
        .result-asking-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 1.35rem;
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0 0 2.5rem 0;
        }}

        /* Price indicator */
        .price-indicator {{
            margin: 0 0 2.75rem 0;
        }}
        .price-indicator-track {{
            position: relative;
            height: 2px;
            background: {c['border']};
            border-radius: 999px;
            margin: 1.25rem 0 0.85rem;
        }}
        .price-indicator-fair {{
            position: absolute;
            top: -5px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: {c['text']};
            transform: translateX(-50%);
            border: 2px solid {c['bg']};
        }}
        .price-indicator-ask {{
            position: absolute;
            top: -5px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            transform: translateX(-50%);
            border: 2px solid {c['bg']};
        }}
        .price-indicator-labels {{
            display: flex;
            justify-content: space-between;
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.68rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        /* Verdict */
        .verdict-large {{
            padding-top: 0.5rem;
        }}
        .verdict-good .verdict-symbol,
        .verdict-good .verdict-title {{
            color: {c['positive']};
            text-shadow: 0 0 22px rgba(34, 197, 94, 0.18);
        }}
        .verdict-fair .verdict-symbol,
        .verdict-fair .verdict-title {{
            color: {c['caution']};
            text-shadow: 0 0 22px rgba(245, 158, 11, 0.16);
        }}
        .verdict-over .verdict-symbol,
        .verdict-over .verdict-title,
        .verdict-bad .verdict-symbol,
        .verdict-bad .verdict-title {{
            color: {c['negative']};
            text-shadow: 0 0 22px rgba(255, 77, 79, 0.16);
        }}
        .verdict-symbol {{
            font-family: {FONT_DISPLAY};
            font-size: 1.5rem;
            font-weight: 500;
            margin: 0 0 0.35rem 0;
        }}
        .verdict-title {{
            font-family: {FONT_DISPLAY};
            font-size: clamp(1.4rem, 3vw, 1.85rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0 0 0.5rem 0;
        }}
        .verdict-summary {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 1rem;
            margin: 0;
        }}

        .info-section {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid {c['border']};
        }}
        .info-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 1rem;
            font-weight: 500;
            letter-spacing: -0.01em;
            margin: 0 0 1rem 0;
        }}
        .info-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.4rem 1.25rem;
            margin: 0;
            padding: 0;
            list-style: none;
        }}
        .info-list li {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.86rem;
        }}

        @media (max-width: 768px) {{
            .stats-strip {{
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }}
            .hero {{
                padding: 2.5rem 0 2rem;
            }}
            .section-title {{
                font-size: clamp(1.45rem, 5vw, 1.85rem);
            }}
        }}

        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within {{
            outline: none !important;
        }}

        div[data-testid="stNumberInput"] input:focus,
        div[data-baseweb="select"] input:focus {{
            outline: none !important;
            box-shadow: none !important;
        }}

        div[data-testid="stButton"] > button[kind="primary"]:focus {{
            outline: none !important;
            box-shadow: 0 0 0 1px rgba(245, 245, 245, 0.12) !important;
        }}

        .price-indicator:hover,
        .verdict-large:hover {{
            transform: translateY(-2px);
            transition: {TRANSITION};
        }}

        .av-zone-start,
        .av-zone-end {{
            display: none;
        }}

        /* ── Valuation Report ── */
        .valuation-report {{
            margin-top: 1.25rem;
            padding-top: 0;
            border-top: none;
        }}
        .valuation-report > .report-section:first-child,
        .valuation-report .report-hero {{
            padding-top: 0.25rem;
        }}

        /* Progressive Vehicle Intelligence Report */
        .vir-report {{
            --vir-section-gap: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: var(--vir-section-gap);
        }}
        .vir-exec {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 14px;
            padding: 1.35rem 1.4rem 1.2rem;
            border-left: 3px solid {c['caution']};
        }}
        .vir-tone-buy {{ border-left-color: #10B981; }}
        .vir-tone-caution {{ border-left-color: #D97706; }}
        .vir-tone-avoid {{ border-left-color: #EF4444; }}
        .vir-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.66rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin: 0 0 0.55rem 0;
        }}
        .vir-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.45rem, 3vw, 1.9rem);
            font-weight: 500;
            letter-spacing: -0.025em;
            margin: 0 0 0.35rem 0;
            line-height: 1.15;
        }}
        .vir-subtitle {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.88rem;
            margin: 0 0 1.15rem 0;
        }}
        .vir-metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        .vir-metric {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid {c['border']};
            border-radius: 10px;
            padding: 0.8rem 0.85rem;
        }}
        .vir-metric-primary {{
            border-color: rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.03);
        }}
        .vir-metric-score .vir-metric-value {{
            letter-spacing: -0.03em;
        }}
        .vir-guidance {{
            border-color: rgba(255, 255, 255, 0.1);
        }}
        .vir-signals-col {{
            min-width: 0;
        }}
        .vir-metric-label {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.62rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin: 0 0 0.35rem 0;
        }}
        .vir-metric-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.05rem, 2vw, 1.35rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0;
            line-height: 1.2;
        }}
        .vir-metric-primary .vir-metric-value {{
            font-size: clamp(1.25rem, 2.4vw, 1.6rem);
        }}
        .vir-metric-sub {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.75rem;
            margin: 0.25rem 0 0 0;
        }}
        .vir-score-denom {{
            color: {c['muted']};
            font-size: 0.72em;
            margin-left: 0.1rem;
        }}
        .vir-verdict-strip {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            flex-wrap: wrap;
            padding-top: 0.15rem;
        }}
        .vir-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            border: 1px solid {c['border']};
            font-family: {FONT_BODY};
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: {c['text_soft']};
            background: rgba(255, 255, 255, 0.03);
            white-space: nowrap;
        }}
        .vir-tone-buy .vir-badge {{
            color: #34D399;
            border-color: rgba(16, 185, 129, 0.35);
            background: rgba(16, 185, 129, 0.1);
        }}
        .vir-tone-caution .vir-badge {{
            color: #FBBF24;
            border-color: rgba(217, 119, 6, 0.4);
            background: rgba(217, 119, 6, 0.12);
        }}
        .vir-tone-avoid .vir-badge {{
            color: #FB7185;
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.12);
        }}
        .vir-verdict-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.05rem, 2vw, 1.25rem);
            font-weight: 500;
            margin: 0;
            letter-spacing: -0.02em;
        }}
        .vir-block {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 12px;
            padding: 1.1rem 1.25rem 1.05rem;
        }}
        .vir-block-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.64rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.65rem 0;
        }}
        .vir-verdict-headline {{
            font-family: {FONT_DISPLAY};
            font-size: clamp(1.15rem, 2.2vw, 1.4rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0 0 0.45rem 0;
            line-height: 1.25;
        }}
        .vir-tone-text-buy {{ color: #34D399; }}
        .vir-tone-text-caution {{ color: #FBBF24; }}
        .vir-tone-text-avoid {{ color: #FB7185; }}
        .vir-verdict-copy,
        .vir-guidance-copy {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
            max-width: 46rem;
        }}
        .vir-action-line {{
            font-family: {FONT_BODY};
            color: {c['text']};
            font-size: 0.9rem;
            font-weight: 500;
            margin: 0.75rem 0 0.9rem 0;
        }}
        .vir-steps-label,
        .vir-signals-label {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 0 0.55rem 0;
        }}
        .vir-signals-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.85rem;
        }}
        .vir-signals-list,
        .vir-steps {{
            display: grid;
            gap: 0.4rem;
        }}
        .vir-signal,
        .vir-step {{
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            padding: 0.55rem 0.65rem;
            border-radius: 8px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.015);
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.84rem;
            line-height: 1.4;
        }}
        .vir-signal-mark,
        .vir-step-mark {{
            flex-shrink: 0;
            width: 1rem;
            text-align: center;
            margin-top: 0.05rem;
            font-size: 0.78rem;
        }}
        .vir-signal-positive {{
            border-color: rgba(16, 185, 129, 0.22);
            background: rgba(16, 185, 129, 0.05);
        }}
        .vir-signal-positive .vir-signal-mark {{ color: #34D399; }}
        .vir-signal-caution {{
            border-color: rgba(217, 119, 6, 0.28);
            background: rgba(217, 119, 6, 0.06);
        }}
        .vir-signal-caution .vir-signal-mark {{ color: #FBBF24; }}
        .vir-signal-critical {{
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.07);
        }}
        .vir-signal-critical .vir-signal-mark {{ color: #FB7185; }}
        .vir-signal-empty {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.84rem;
            line-height: 1.5;
            padding: 0.55rem 0.65rem;
            border-radius: 8px;
            border: 1px dashed {c['border']};
        }}
        .vir-step-mark {{ color: {c['informational']}; }}
        .vir-detail {{
            padding: 0.25rem 0 0.5rem;
        }}
        .vir-detail-note {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.82rem;
            line-height: 1.5;
            margin: 0 0 0.9rem 0;
        }}
        .vir-spec-chip-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: 0.9rem;
        }}
        .vir-chip {{
            display: inline-flex;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.02);
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.75rem;
        }}
        .vir-disclaimer {{
            display: flex;
            align-items: flex-start;
            gap: 0.55rem;
            margin-top: 0;
            padding: 0.85rem 0.95rem;
            border-radius: 10px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.015);
        }}
        .vir-disclaimer-icon {{
            color: {c['muted']};
            flex-shrink: 0;
            margin-top: 0.05rem;
        }}
        .vir-disclaimer p {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.76rem;
            line-height: 1.55;
            margin: 0;
            max-width: 48rem;
        }}
        /* Consistent vertical rhythm: executive blocks + detail expanders */
        div[data-testid="stElementContainer"]:has(.vir-report) {{
            margin-bottom: var(--vir-section-gap, 1.25rem) !important;
        }}
        div[data-testid="stElementContainer"]:has(.vir-detail-sections) {{
            margin: 0 !important;
            padding: 0 !important;
            min-height: 0 !important;
            height: 0 !important;
            overflow: hidden !important;
        }}
        div[data-testid="stElementContainer"]:has(.vir-detail-sections) .vir-detail-sections {{
            display: none;
        }}
        div[data-testid="stElementContainer"]:has(.vir-detail-sections)
            ~ div[data-testid="stElementContainer"]:has([data-testid="stExpander"]) {{
            margin-top: 0 !important;
            margin-bottom: var(--vir-section-gap, 1.25rem) !important;
        }}
        div[data-testid="stElementContainer"]:has(.vir-disclaimer) {{
            margin-top: 0 !important;
        }}
        div[data-testid="stExpander"] {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 12px;
        }}
        div[data-testid="stExpander"] details {{
            border: none !important;
        }}
        div[data-testid="stExpander"] summary {{
            font-family: {FONT_BODY} !important;
            color: {c['text_soft']} !important;
            font-size: 0.9rem !important;
            letter-spacing: 0.01em;
        }}
        @media (max-width: 900px) {{
            .vir-metric-grid,
            .vir-signals-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        @media (max-width: 640px) {{
            .vir-metric-grid,
            .vir-signals-grid {{
                grid-template-columns: 1fr;
            }}
            .vir-exec,
            .vir-block {{
                padding: 1rem 1rem 0.95rem;
            }}
        }}
        .report-section {{
            padding: 2.75rem 0;
            border-bottom: 1px solid {c['border']};
        }}
        .report-section-last {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        .report-section-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.68rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-weight: 500;
            margin: 0 0 1.25rem 0;
        }}
        .report-section-label {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin: 0 0 0.5rem 0;
        }}
        .report-section-note {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.86rem;
            line-height: 1.6;
            margin: 0 0 1.75rem 0;
            max-width: 640px;
        }}
        .report-body-copy {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.95rem;
            line-height: 1.65;
            margin: 1.25rem 0 0 0;
            max-width: 680px;
        }}
        .report-metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            margin-top: 2.5rem;
            padding-top: 2rem;
            border-top: 1px solid {c['border']};
        }}
        .report-metric-label {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.5rem 0;
        }}
        .report-metric-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.35rem, 2.5vw, 1.75rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0 0 0.3rem 0;
        }}
        .report-metric-sub {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.82rem;
            margin: 0;
        }}
        .report-metric-delta {{
            letter-spacing: 0.04em;
            font-weight: 500;
        }}
        .report-delta-positive,
        .report-metric-value-favorable {{
            color: {c['positive']};
            text-shadow: 0 0 16px rgba(34, 197, 94, 0.14);
        }}
        .report-delta-negative,
        .report-metric-value-unfavorable {{
            color: {c['negative']};
            text-shadow: 0 0 16px rgba(255, 77, 79, 0.14);
        }}
        .report-delta-neutral {{
            color: {c['caution']};
            text-shadow: 0 0 16px rgba(245, 158, 11, 0.12);
        }}
        .report-deal-row {{
            display: grid;
            grid-template-columns: 1fr 1.4fr;
            gap: 2.5rem;
            align-items: start;
        }}
        .report-deal-score {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(2.4rem, 5vw, 3.2rem);
            font-weight: 500;
            letter-spacing: -0.03em;
            line-height: 1;
            margin: 0;
        }}
        .report-deal-score-strong {{
            color: {c['positive']};
            text-shadow: 0 0 24px rgba(34, 197, 94, 0.16);
        }}
        .report-deal-score-moderate {{
            color: {c['caution']};
            text-shadow: 0 0 24px rgba(245, 158, 11, 0.14);
        }}
        .report-deal-score-weak {{
            color: {c['negative']};
            text-shadow: 0 0 24px rgba(255, 77, 79, 0.14);
        }}
        .report-deal-score span {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 1rem;
            letter-spacing: 0.02em;
            margin-left: 0.15rem;
        }}
        .report-range-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .report-range-label {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.66rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.45rem 0;
        }}
        .report-range-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 1.25rem;
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0;
        }}
        .report-range-point-mid .report-range-value {{
            color: {c['informational']};
            font-size: 1.45rem;
            text-shadow: 0 0 18px rgba(56, 189, 248, 0.14);
        }}
        .report-range-track {{
            position: relative;
            height: 28px;
            margin-top: 0.5rem;
        }}
        .report-range-line {{
            position: absolute;
            top: 13px;
            left: 0;
            right: 0;
            height: 2px;
            background: {c['border']};
            border-radius: 999px;
        }}
        .report-range-marker {{
            position: absolute;
            top: 8px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: {c['muted']};
            border: 2px solid {c['bg']};
            transform: translateX(-50%);
        }}
        .report-range-low {{ left: 0%; }}
        .report-range-mid {{
            left: 50%;
            background: {c['informational']};
            box-shadow: 0 0 14px rgba(56, 189, 248, 0.28);
            width: 12px;
            height: 12px;
            top: 7px;
        }}
        .report-range-high {{ left: 100%; }}
        .report-factor-list {{
            display: grid;
            gap: 1.25rem;
        }}
        .report-factor {{
            padding-bottom: 1.25rem;
            border-bottom: 1px solid {c['border']};
        }}
        .report-factor:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        .report-factor-head {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 1rem;
            margin-bottom: 0.45rem;
        }}
        .report-factor-label {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 0.98rem;
            font-weight: 500;
        }}
        .report-factor-signal {{
            font-family: {FONT_BODY};
            font-size: 0.62rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
            padding: 0.22rem 0.58rem;
            border-radius: 999px;
            border: 1px solid transparent;
        }}
        .signal-positive {{
            color: {c['positive']};
            border-color: rgba(34, 197, 94, 0.35);
            box-shadow: 0 0 18px rgba(34, 197, 94, 0.12);
        }}
        .signal-negative {{
            color: {c['negative']};
            border-color: rgba(255, 77, 79, 0.35);
            box-shadow: 0 0 18px rgba(255, 77, 79, 0.12);
        }}
        .signal-neutral {{
            color: {c['caution']};
            border-color: rgba(245, 158, 11, 0.35);
            box-shadow: 0 0 18px rgba(245, 158, 11, 0.1);
        }}
        .report-factor-text {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.88rem;
            line-height: 1.55;
            margin: 0;
        }}
        .report-confidence-row {{
            display: flex;
            align-items: baseline;
            gap: 1.25rem;
            margin-bottom: 0.25rem;
        }}
        .report-confidence-level {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.6rem, 3vw, 2rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0;
        }}
        .report-confidence-high {{
            color: {c['positive']};
            text-shadow: 0 0 20px rgba(34, 197, 94, 0.14);
        }}
        .report-confidence-moderate {{
            color: {c['caution']};
            text-shadow: 0 0 20px rgba(245, 158, 11, 0.12);
        }}
        .report-confidence-limited {{
            color: {c['negative']};
            text-shadow: 0 0 20px rgba(255, 77, 79, 0.12);
        }}
        .report-confidence-score {{
            font-family: {FONT_BODY};
            color: {c['informational']};
            font-size: 0.95rem;
            margin: 0;
        }}
        .report-negotiation-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }}
        .report-negotiation-item {{
            padding-top: 0.25rem;
        }}
        .report-signals-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2.5rem;
        }}
        .report-signals-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 0.95rem;
            font-weight: 500;
            margin: 0 0 1rem 0;
        }}
        .report-signals-list {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .report-signals-list li {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.88rem;
            line-height: 1.55;
            margin: 0 0 0.65rem 0;
            display: flex;
            align-items: flex-start;
            gap: 0.55rem;
        }}
        .signal-mark {{
            font-family: {FONT_DISPLAY};
            font-size: 0.82rem;
            line-height: 1.4;
            flex-shrink: 0;
            width: 1.1rem;
            text-align: center;
        }}
        .positive-mark {{
            color: {c['positive']};
            text-shadow: 0 0 12px rgba(34, 197, 94, 0.2);
        }}
        .consider-mark,
        .negative-mark {{
            color: {c['negative']};
            text-shadow: 0 0 12px rgba(255, 77, 79, 0.18);
        }}
        .report-signals-col-positive .report-signals-title {{
            color: {c['positive']};
        }}
        .report-signals-col-consider .report-signals-title {{
            color: {c['negative']};
        }}
        .report-signal-empty {{
            color: {c['muted']};
        }}

        /* ── AI Purchase Recommendation ── */
        .purchase-recommendation {{
            padding-top: 2rem;
        }}
        .purchase-panel {{
            background: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 14px;
            padding: 1.35rem 1.45rem 1.2rem;
            border-left: 3px solid {c['caution']};
        }}
        .purchase-tone-buy {{
            border-left-color: #10B981;
            box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.06);
        }}
        .purchase-tone-caution {{
            border-left-color: #D97706;
            box-shadow: 0 0 0 1px rgba(217, 119, 6, 0.06);
        }}
        .purchase-tone-avoid {{
            border-left-color: #EF4444;
            box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.06);
        }}
        .purchase-hero {{
            margin-bottom: 1.35rem;
            padding-bottom: 1.2rem;
            border-bottom: 1px solid {c['border']};
        }}
        .purchase-hero-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.85rem;
            flex-wrap: wrap;
            margin-bottom: 0.85rem;
        }}
        .purchase-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.66rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0;
        }}
        .purchase-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.03);
            font-family: {FONT_BODY};
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: {c['text_soft']};
        }}
        .purchase-badge-icon {{
            font-size: 0.78rem;
            line-height: 1;
        }}
        .purchase-tone-buy .purchase-badge {{
            color: #34D399;
            border-color: rgba(16, 185, 129, 0.35);
            background: rgba(16, 185, 129, 0.1);
        }}
        .purchase-tone-caution .purchase-badge {{
            color: #FBBF24;
            border-color: rgba(217, 119, 6, 0.4);
            background: rgba(217, 119, 6, 0.12);
        }}
        .purchase-tone-avoid .purchase-badge {{
            color: #FB7185;
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.12);
        }}
        .purchase-headline {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.35rem, 2.6vw, 1.75rem);
            font-weight: 500;
            letter-spacing: -0.025em;
            margin: 0 0 0.45rem 0;
            line-height: 1.2;
        }}
        .purchase-tone-buy .purchase-headline {{
            color: #6EE7B7;
        }}
        .purchase-tone-caution .purchase-headline {{
            color: #FCD34D;
        }}
        .purchase-tone-avoid .purchase-headline {{
            color: #FDA4AF;
        }}
        .purchase-support {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.92rem;
            line-height: 1.55;
            margin: 0;
            max-width: 46rem;
        }}
        .purchase-block {{
            margin-bottom: 1.25rem;
        }}
        .purchase-block-title {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.66rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.7rem 0;
        }}
        .purchase-stance {{
            font-family: {FONT_BODY};
            color: {c['text']};
            font-size: 0.95rem;
            line-height: 1.55;
            margin: 0 0 0.85rem 0;
            max-width: 46rem;
        }}
        .purchase-metric {{
            display: inline-flex;
            flex-direction: column;
            gap: 0.28rem;
            padding: 0.75rem 0.95rem;
            border-radius: 10px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.02);
            margin-bottom: 0.85rem;
            max-width: 100%;
        }}
        .purchase-metric-below {{
            border-color: rgba(16, 185, 129, 0.35);
            background: rgba(16, 185, 129, 0.08);
        }}
        .purchase-metric-above {{
            border-color: rgba(239, 68, 68, 0.35);
            background: rgba(239, 68, 68, 0.08);
        }}
        .purchase-metric-aligned {{
            border-color: rgba(56, 189, 248, 0.3);
            background: rgba(56, 189, 248, 0.07);
        }}
        .purchase-metric-value {{
            font-family: {FONT_DISPLAY};
            font-size: clamp(1.05rem, 2vw, 1.25rem);
            font-weight: 600;
            letter-spacing: 0.04em;
            margin: 0;
            color: {c['text']};
        }}
        .purchase-metric-below .purchase-metric-value {{
            color: #34D399;
        }}
        .purchase-metric-above .purchase-metric-value {{
            color: #FB7185;
        }}
        .purchase-metric-aligned .purchase-metric-value {{
            color: #7DD3FC;
        }}
        .purchase-metric-note {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.82rem;
            line-height: 1.45;
            margin: 0;
        }}
        .purchase-why {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.86rem;
            line-height: 1.6;
            margin: 0;
            max-width: 46rem;
        }}
        .purchase-signals-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.85rem;
        }}
        .purchase-signals-col {{
            min-width: 0;
        }}
        .purchase-signals-label {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.78rem;
            font-weight: 500;
            margin: 0 0 0.55rem 0;
        }}
        .purchase-signals-list {{
            display: grid;
            gap: 0.45rem;
        }}
        .purchase-signal-row {{
            display: flex;
            align-items: flex-start;
            gap: 0.55rem;
            padding: 0.65rem 0.75rem;
            border-radius: 10px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.02);
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.84rem;
            line-height: 1.45;
        }}
        .purchase-signal-icon {{
            flex-shrink: 0;
            width: 1rem;
            text-align: center;
            margin-top: 0.05rem;
            font-size: 0.78rem;
        }}
        .purchase-signal-positive {{
            border-color: rgba(16, 185, 129, 0.22);
            background: rgba(16, 185, 129, 0.05);
        }}
        .purchase-signal-positive .purchase-signal-icon {{
            color: #34D399;
        }}
        .purchase-signal-caution {{
            border-color: rgba(217, 119, 6, 0.28);
            background: rgba(217, 119, 6, 0.06);
        }}
        .purchase-signal-caution .purchase-signal-icon {{
            color: #FBBF24;
        }}
        .purchase-signal-critical {{
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.07);
        }}
        .purchase-signal-critical .purchase-signal-icon {{
            color: #FB7185;
        }}
        .purchase-signal-empty {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.84rem;
            line-height: 1.5;
            padding: 0.7rem 0.75rem;
            border-radius: 10px;
            border: 1px dashed {c['border']};
        }}
        .purchase-steps {{
            display: grid;
            gap: 0.45rem;
        }}
        .purchase-step-row {{
            display: flex;
            align-items: flex-start;
            gap: 0.7rem;
            padding: 0.7rem 0.8rem;
            border-radius: 10px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.015);
        }}
        .purchase-step-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.55rem;
            height: 1.55rem;
            border-radius: 8px;
            flex-shrink: 0;
            font-size: 0.78rem;
            color: {c['informational']};
            background: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.22);
        }}
        .purchase-step-text {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.88rem;
            line-height: 1.45;
            padding-top: 0.15rem;
        }}
        .purchase-verdict {{
            margin: 0.15rem 0 1rem 0;
            padding: 1rem 1.05rem;
            border-radius: 12px;
            border: 1px solid {c['border']};
            background: rgba(255, 255, 255, 0.025);
        }}
        .purchase-tone-buy .purchase-verdict {{
            border-color: rgba(16, 185, 129, 0.28);
            background: rgba(16, 185, 129, 0.06);
        }}
        .purchase-tone-caution .purchase-verdict {{
            border-color: rgba(217, 119, 6, 0.3);
            background: rgba(217, 119, 6, 0.07);
        }}
        .purchase-tone-avoid .purchase-verdict {{
            border-color: rgba(239, 68, 68, 0.3);
            background: rgba(239, 68, 68, 0.07);
        }}
        .purchase-verdict-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.64rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.4rem 0;
        }}
        .purchase-verdict-label {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.15rem, 2.2vw, 1.4rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0 0 0.35rem 0;
            line-height: 1.2;
        }}
        .purchase-tone-buy .purchase-verdict-label {{
            color: #34D399;
        }}
        .purchase-tone-caution .purchase-verdict-label {{
            color: #FBBF24;
        }}
        .purchase-tone-avoid .purchase-verdict-label {{
            color: #FB7185;
        }}
        .purchase-verdict-detail {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.88rem;
            line-height: 1.55;
            margin: 0;
            max-width: 42rem;
        }}
        .purchase-disclaimer {{
            display: flex;
            align-items: flex-start;
            gap: 0.55rem;
            padding-top: 0.85rem;
            border-top: 1px solid {c['border']};
        }}
        .purchase-disclaimer-icon {{
            color: {c['muted']};
            flex-shrink: 0;
            margin-top: 0.1rem;
            font-size: 0.85rem;
        }}
        .purchase-disclaimer p {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.76rem;
            line-height: 1.55;
            margin: 0;
            max-width: 48rem;
        }}
        .purchase-panel:focus-within {{
            outline: 2px solid {c['informational']};
            outline-offset: 3px;
        }}
        @media (max-width: 720px) {{
            .purchase-panel {{
                padding: 1.15rem 1.05rem 1.05rem;
            }}
            .purchase-signals-grid {{
                grid-template-columns: 1fr;
            }}
            .purchase-hero-top {{
                align-items: flex-start;
            }}
            .purchase-support,
            .purchase-stance,
            .purchase-why {{
                font-size: 0.88rem;
            }}
        }}

        /* ── Application Shell ── */
        .app-shell {{
            border-bottom: 1px solid {c['border']};
            margin: 0 0 1.5rem 0;
            padding: 0.25rem 0 1rem;
        }}
        .app-brand-block {{
            margin-bottom: 0.35rem;
        }}
        .app-brand-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin: 0;
        }}
        .app-brand-subtitle {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.78rem;
            margin: 0.35rem 0 0 0;
        }}
        .app-view-eyebrow {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.66rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            margin: 0 0 0.75rem 0;
        }}
        .dashboard-panel {{
            padding: 2rem 0 1rem;
        }}
        .dashboard-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(2rem, 4vw, 2.75rem);
            font-weight: 500;
            letter-spacing: -0.03em;
            margin: 0 0 0.75rem 0;
        }}
        .dashboard-copy {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 1rem;
            line-height: 1.65;
            max-width: 620px;
            margin: 0 0 2rem 0;
        }}
        .dashboard-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin: 0 0 2.5rem 0;
            padding: 1.5rem 0;
            border-top: 1px solid {c['border']};
            border-bottom: 1px solid {c['border']};
        }}
        .dashboard-stat-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: 1.45rem;
            font-weight: 500;
            margin: 0 0 0.25rem 0;
        }}
        .dashboard-stat-label {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.66rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0;
        }}
        .recent-panel {{
            margin-top: 1rem;
        }}
        .recent-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 1.05rem;
            font-weight: 500;
            margin: 0 0 1rem 0;
        }}
        .recent-list {{
            display: grid;
            gap: 0.75rem;
        }}
        .recent-item {{
            display: grid;
            grid-template-columns: 1.4fr 1fr 1fr auto;
            gap: 1rem;
            align-items: center;
            padding: 1rem 1.1rem;
            border: 1px solid {c['border']};
            border-radius: 10px;
            background: {c['surface']};
        }}
        .recent-item-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: 0.98rem;
            margin: 0 0 0.2rem 0;
        }}
        .recent-item-meta {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.78rem;
            margin: 0;
        }}
        .recent-item-value {{
            font-family: {FONT_DISPLAY};
            color: {c['text_soft']};
            font-size: 0.95rem;
            margin: 0;
        }}
        .recent-item-verdict {{
            font-family: {FONT_BODY};
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            border: 1px solid transparent;
            white-space: nowrap;
        }}
        .recent-verdict-good {{
            color: {c['positive']};
            border-color: rgba(34, 197, 94, 0.35);
            box-shadow: 0 0 14px rgba(34, 197, 94, 0.1);
        }}
        .recent-verdict-fair {{
            color: {c['caution']};
            border-color: rgba(245, 158, 11, 0.35);
        }}
        .recent-verdict-over {{
            color: {c['negative']};
            border-color: rgba(255, 77, 79, 0.35);
        }}
        .recent-empty {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.9rem;
            padding: 1.25rem 0;
        }}
        .wizard-progress {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin: 0 0 2rem 0;
            padding-bottom: 1.25rem;
            border-bottom: 1px solid {c['border']};
        }}
        .wizard-step {{
            font-family: {FONT_DISPLAY};
            color: {c['muted']};
            font-size: 0.95rem;
            letter-spacing: 0.06em;
            padding: 0.35rem 0.75rem;
            border: 1px solid {c['border']};
            border-radius: 999px;
        }}
        .wizard-step-active {{
            color: {c['text']};
            border-color: {c['text']};
            box-shadow: 0 0 16px rgba(245, 245, 245, 0.06);
        }}
        .wizard-step-done {{
            color: {c['informational']};
            border-color: rgba(56, 189, 248, 0.35);
        }}
        .wizard-step-sep {{
            color: {c['muted']};
            font-size: 0.85rem;
        }}
        .wizard-nav,
        .valuation-actions {{
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid {c['border']};
        }}
        .asking-price-preview {{
            margin: 0.35rem 0 0 0;
            padding: 0.85rem 1rem;
            border: 1px solid {c['border']};
            border-radius: 8px;
            background: {c['surface']};
        }}
        .asking-price-preview-label {{
            display: block;
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.35rem 0;
        }}
        .asking-price-preview-value {{
            display: block;
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: 1.15rem;
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0;
        }}
        .vehicle-identity {{
            margin: 1rem 0 0.75rem 0;
            padding: 1.5rem 0 1.25rem;
            border-bottom: 1px solid {c['border']};
        }}
        .vehicle-identity-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: clamp(1.5rem, 3vw, 2rem);
            font-weight: 500;
            letter-spacing: -0.02em;
            margin: 0 0 0.35rem 0;
        }}
        .vehicle-identity-subtitle {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.82rem;
            margin: 0 0 1.1rem 0;
        }}
        .vehicle-identity-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem 1.5rem;
        }}
        .vehicle-identity-item-label {{
            font-family: {FONT_BODY};
            color: {c['label']};
            font-size: 0.62rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 0 0 0.25rem 0;
        }}
        .vehicle-identity-item-value {{
            font-family: {FONT_BODY};
            color: {c['text_soft']};
            font-size: 0.88rem;
            margin: 0;
        }}
        .results-page .valuation-report {{
            margin-top: 2rem;
            padding-top: 0.5rem;
            border-top: none;
        }}
        .results-page .valuation-report > .report-section:first-child,
        .results-page .valuation-report .report-hero {{
            padding-top: 0.25rem;
        }}
        .result-actions {{
            margin: 2.5rem 0 1rem;
            padding-top: 1.5rem;
            border-top: 1px solid {c['border']};
        }}
        .about-panel {{
            padding: 2rem 0;
            max-width: 680px;
        }}
        .about-title {{
            font-family: {FONT_DISPLAY};
            color: {c['text']};
            font-size: 1.75rem;
            margin: 0 0 1rem 0;
        }}
        .about-copy {{
            font-family: {FONT_BODY};
            color: {c['muted']};
            font-size: 0.95rem;
            line-height: 1.7;
            margin: 0 0 1rem 0;
        }}

        @media (max-width: 768px) {{
            .dashboard-stats,
            .vehicle-identity-grid {{
                grid-template-columns: 1fr;
            }}
            .recent-item {{
                grid-template-columns: 1fr;
            }}
            .report-metrics-grid,
            .report-range-grid,
            .report-negotiation-grid {{
                grid-template-columns: 1fr;
                gap: 1.25rem;
            }}
            .report-deal-row,
            .report-signals-grid {{
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_scroll_layout_fix() -> None:
    """Remove Streamlit viewport clipping so the full page scrolls freely."""
    st.markdown(
        """
        <style>
        /* Document is the only scroll root */
        html {
            height: auto !important;
            max-height: none !important;
            overflow-y: scroll !important;
            overflow-x: clip !important;
        }

        body {
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
        }

        /* Disable nested scroll traps / fixed viewport heights */
        .stApp,
        div[data-testid="stApp"],
        section[data-testid="stAppViewContainer"],
        .appview-container,
        section[data-testid="stMain"],
        section.main,
        .main,
        div[data-testid="stMainBlockContainer"],
        .main .block-container,
        .block-container,
        div[data-testid="stVerticalBlock"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="element-container"],
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stHorizontalBlock"] {
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
            overscroll-behavior: auto !important;
        }

        .stApp,
        div[data-testid="stApp"],
        section[data-testid="stAppViewContainer"],
        .appview-container {
            min-height: 100vh !important;
            position: relative !important;
        }

        .main .block-container,
        .block-container,
        div[data-testid="stMainBlockContainer"] {
            min-height: 100vh !important;
            padding-bottom: 120px !important;
        }

        /* Streamlit chrome must not capture wheel / pointer events */
        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
            pointer-events: none !important;
        }

        .stApp > div[style*="position: fixed"],
        .stApp > div[style*="position:fixed"] {
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_branding() -> None:
    """Persistent product branding block."""
    st.markdown(
        """
        <div class="app-shell"><div class="app-brand-block"><p class="app-brand-title">AutoValue AI</p><p class="app-brand-subtitle">AI-powered used vehicle intelligence</p></div></div>
        """,
        unsafe_allow_html=True,
    )


def render_wizard_progress(current_step: int) -> None:
    """Render the 01 → 02 → 03 valuation progress indicator."""
    step_class = {
        1: ("wizard-step wizard-step-active", "wizard-step", "wizard-step"),
        2: ("wizard-step wizard-step-done", "wizard-step wizard-step-active", "wizard-step"),
        3: ("wizard-step wizard-step-done", "wizard-step wizard-step-done", "wizard-step wizard-step-active"),
    }
    classes = step_class.get(current_step, step_class[1])
    st.markdown(
        f'<div class="wizard-progress"><span class="{classes[0]}">01</span><span class="wizard-step-sep">→</span><span class="{classes[1]}">02</span><span class="wizard-step-sep">→</span><span class="{classes[2]}">03</span></div>',
        unsafe_allow_html=True,
    )


def render_site_header() -> None:
    st.markdown(
        """
        <div class="site-header av-reveal">
            <span class="brand-mark">AV · AutoValue AI</span>
            <span class="brand-right">AI Powered</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(
    *,
    model_name: str,
    listing_count: int,
    r2_score: float,
) -> None:
    listings_label = f"{listing_count:,}+"
    st.markdown(
        f"""
        <div class="hero av-reveal">
            <p class="hero-eyebrow">AI-Powered Vehicle Valuation</p>
            <h1 class="hero-title">Know what your vehicle<br>is actually worth.</h1>
            <p class="hero-copy">
                Estimate fair market value using machine learning and understand
                whether the seller's asking price represents a good deal.
            </p>
            <p class="hero-meta">
                Model: {model_name} · {listings_label} listings · R² {r2_score:.3f}
            </p>
            <a href="#valuation-form" class="hero-cta">Start Valuation →</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats_strip(
    *,
    listing_count: int,
    feature_count: int,
    r2_score: float,
) -> None:
    st.markdown(
        f"""
        <div class="stats-strip av-reveal">
            <div>
                <p class="stat-value">{listing_count:,}+</p>
                <p class="stat-label">Vehicle Listings</p>
            </div>
            <div>
                <p class="stat-value">{feature_count}</p>
                <p class="stat-label">Model Features</p>
            </div>
            <div>
                <p class="stat-value">{r2_score:.3f}</p>
                <p class="stat-label">Model R²</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(number: str, title: str, description: str) -> None:
    """Render a major form section with strong editorial hierarchy."""
    st.markdown(
        f"""
        <div class="section-head av-reveal">
            <p class="section-number">{number}</p>
            <h2 class="section-title">{title}</h2>
            <p class="section-desc">{description}</p>
        </div>
        <hr class="section-rule">
        """,
        unsafe_allow_html=True,
    )


def render_zone_start(section_id: str) -> None:
    """Mark the start of a form section for scroll-reveal field binding."""
    st.markdown(
        f'<div class="av-zone-start" data-zone="{section_id}"></div>',
        unsafe_allow_html=True,
    )


def render_zone_end(section_id: str) -> None:
    """Mark the end of a form section for scroll-reveal field binding."""
    st.markdown(
        f'<div class="av-zone-end" data-zone="{section_id}"></div>',
        unsafe_allow_html=True,
    )
