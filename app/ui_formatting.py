"""
UI formatting helpers for AutoValue AI.

Maps professional display labels to raw model values without changing
the inference schema expected by the trained pipeline.
"""

from __future__ import annotations

import streamlit as st

# Tokens that should render as uppercase acronyms in labels.
UPPERCASE_TOKENS = frozenset({"suv", "lpg", "cng", "bmw", "mg"})


def _format_word(word: str) -> str:
    lower = word.lower()
    if lower in UPPERCASE_TOKENS:
        return lower.upper()
    if any(ch.isdigit() for ch in word):
        return word.lower()
    return word.capitalize()


def format_category_label(raw: str) -> str:
    """
    Convert a raw categorical value to a user-facing label.

    Examples
    --------
    maruti -> Maruti
    grand i10 -> Grand i10
    petrol & lpg -> Petrol & LPG
    suv -> SUV
    uttar pradesh -> Uttar Pradesh
    """
    text = str(raw).strip()
    if not text:
        return text

    if "&" in text:
        parts = [format_category_label(part.strip()) for part in text.split("&")]
        return " & ".join(parts)

    words = text.split()
    formatted: list[str] = []
    for word in words:
        formatted.append(_format_word(word))
    return " ".join(formatted)


def format_owner_label(count: int) -> str:
    """Format owner count for display (e.g. 1 -> '1 Owner')."""
    count = int(count)
    suffix = "Owner" if count == 1 else "Owners"
    return f"{count} {suffix}"


def parse_owner_label(label: str) -> int:
    """Extract numeric owner count from a display label."""
    return int(str(label).split()[0])


def build_label_maps(raw_values: list[str]) -> tuple[list[str], dict[str, str]]:
    """
    Build display options and a display->raw mapping.

    Returns
    -------
    display_options, display_to_raw
    """
    display_to_raw = {format_category_label(value): value for value in raw_values}
    display_options = [format_category_label(value) for value in raw_values]
    return display_options, display_to_raw


def build_owner_maps(raw_values: list[int]) -> tuple[list[str], dict[str, int]]:
    """Build owner display options and display->numeric mapping."""
    display_to_raw = {format_owner_label(value): value for value in raw_values}
    display_options = [format_owner_label(value) for value in raw_values]
    return display_options, display_to_raw


def labeled_selectbox(
    label: str,
    raw_options: list[str],
    *,
    default_raw: str | None = None,
    key: str | None = None,
) -> str:
    """
    Render a selectbox with formatted labels; return the raw model value.
    """
    display_options, display_to_raw = build_label_maps(raw_options)
    index = 0
    if default_raw is not None and default_raw in raw_options:
        index = display_options.index(format_category_label(default_raw))

    selected_display = st.selectbox(label, options=display_options, index=index, key=key)
    return display_to_raw[selected_display]


def labeled_owner_selectbox(
    label: str,
    raw_options: list[int],
    *,
    default_raw: int | None = None,
    key: str | None = None,
) -> int:
    """Render owner selectbox with formatted labels; return numeric value."""
    display_options, display_to_raw = build_owner_maps(raw_options)
    index = 0
    if default_raw is not None and default_raw in raw_options:
        index = display_options.index(format_owner_label(default_raw))

    selected_display = st.selectbox(label, options=display_options, index=index, key=key)
    return display_to_raw[selected_display]
