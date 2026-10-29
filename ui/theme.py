"""Design tokens: one palette, one type scale, one set of button styles.

Every colour is a (light, dark) pair. CustomTkinter widgets accept the pair
directly and switch automatically; plain Tk widgets (canvas, ttk) use
``color()`` which resolves the pair for the current mode.
"""
from __future__ import annotations

from typing import Dict, Tuple

import customtkinter as ctk

PALETTE: Dict[str, Tuple[str, str]] = {
    # surfaces
    "bg": ("#EEF1F8", "#0D1017"),
    "surface": ("#E3E8F3", "#121827"),
    "card": ("#FFFFFF", "#161D2D"),
    "card_alt": ("#EDF1F9", "#1C2539"),
    "input": ("#F6F8FD", "#0F1522"),
    "border": ("#CBD4E6", "#2B3652"),
    "nav_active": ("#D3E3F6", "#172A44"),
    # text
    "text": ("#141B2D", "#E6ECF8"),
    "muted": ("#5A6684", "#8A97B8"),
    # accents
    "cyan": ("#0891B2", "#22D3EE"),
    "blue": ("#2563EB", "#4C8DFF"),
    "violet": ("#7C3AED", "#A78BFA"),
    "success": ("#15803D", "#34D399"),
    "danger": ("#DC2626", "#FB7185"),
    "warning": ("#B45309", "#FBBF24"),
    # data-structure cells
    "cell_fill": ("#E6ECFB", "#1E2A4A"),
    "cell_border": ("#8DA2E8", "#5B6CF0"),
    "top_fill": ("#CFF3FA", "#0E3B4C"),
    "top_border": ("#0891B2", "#22D3EE"),
    "rear_fill": ("#E9E0FD", "#2A1F4D"),
    "rear_border": ("#7C3AED", "#A78BFA"),
    "flash_fill": ("#0891B2", "#22D3EE"),
    "flash_text": ("#FFFFFF", "#04141C"),
}

FONT_FAMILY = "Segoe UI"
MONO_FAMILY = "Consolas"

_mode = "dark"
_fonts: Dict[tuple, ctk.CTkFont] = {}


def set_mode(mode: str) -> None:
    global _mode
    _mode = "light" if str(mode).lower() == "light" else "dark"


def get_mode() -> str:
    return _mode


def pair(name: str) -> Tuple[str, str]:
    return PALETTE[name]


def color(name: str) -> str:
    light, dark = PALETTE[name]
    return light if _mode == "light" else dark


def font(size: int = 13, weight: str = "normal", mono: bool = False) -> ctk.CTkFont:
    key = (size, weight, mono)
    if key not in _fonts:
        _fonts[key] = ctk.CTkFont(family=MONO_FAMILY if mono else FONT_FAMILY, size=size, weight=weight)
    return _fonts[key]


def tk_font(size: int = 12, weight: str = "normal", mono: bool = False) -> tuple:
    """Font tuple for plain Tk widgets (canvas, ttk)."""
    return (MONO_FAMILY if mono else FONT_FAMILY, size, weight)


BUTTON_STYLES = {
    "primary": dict(fg_color=pair("cyan"), hover_color=("#0E7490", "#67E8F9"),
                    text_color=("#FFFFFF", "#04141C"), border_width=0),
    "secondary": dict(fg_color=("#7C3AED", "#8B5CF6"), hover_color=("#6D28D9", "#A78BFA"),
                      text_color=("#FFFFFF", "#0E0A1F"), border_width=0),
    "outline": dict(fg_color="transparent", hover_color=pair("card_alt"), text_color=pair("cyan"),
                    border_width=1, border_color=pair("cyan")),
    "danger": dict(fg_color="transparent", hover_color=("#FDE8E8", "#3A1822"), text_color=pair("danger"),
                   border_width=1, border_color=pair("danger")),
    "ghost": dict(fg_color="transparent", hover_color=pair("card_alt"), text_color=pair("muted"),
                  border_width=0),
}
