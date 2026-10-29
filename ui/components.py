"""Reusable widgets so every page shares the same look."""
from __future__ import annotations

from typing import Callable, Optional, Sequence

import customtkinter as ctk

from . import theme


def _apply_justify(label: ctk.CTkLabel, justify: Optional[str]) -> None:
    """CTkLabel has no ``justify`` option, so set it on the inner Tk label."""
    if justify:
        try:
            label._label.configure(justify=justify)
        except Exception:
            pass


def make_label(parent, text: str = "", size: int = 13, weight: str = "normal", color: str = "text",
               mono: bool = False, **kwargs) -> ctk.CTkLabel:
    kwargs.setdefault("anchor", "w")
    justify = kwargs.pop("justify", None)
    label = ctk.CTkLabel(parent, text=text, font=theme.font(size, weight, mono),
                         text_color=theme.pair(color), **kwargs)
    _apply_justify(label, justify)
    return label


def make_button(parent, text: str, command: Optional[Callable] = None, kind: str = "primary",
                height: int = 36, **kwargs) -> ctk.CTkButton:
    style = dict(theme.BUTTON_STYLES[kind])
    style.update(kwargs)
    return ctk.CTkButton(parent, text=text, command=command, height=height, corner_radius=10,
                         font=theme.font(13, "bold"), **style)


def make_entry(parent, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
    return ctk.CTkEntry(parent, placeholder_text=placeholder, height=40, corner_radius=10,
                        font=theme.font(14), fg_color=theme.pair("input"),
                        border_color=theme.pair("border"), text_color=theme.pair("text"),
                        placeholder_text_color=theme.pair("muted"), **kwargs)


def make_option(parent, values: Sequence[str], command: Optional[Callable] = None,
                width: int = 150) -> ctk.CTkOptionMenu:
    return ctk.CTkOptionMenu(parent, values=list(values), command=command, width=width, height=36,
                             corner_radius=10, font=theme.font(13), dropdown_font=theme.font(13),
                             fg_color=theme.pair("input"), button_color=theme.pair("card_alt"),
                             button_hover_color=theme.pair("border"), text_color=theme.pair("text"),
                             dropdown_fg_color=theme.pair("card"), dropdown_text_color=theme.pair("text"),
                             dropdown_hover_color=theme.pair("card_alt"), dynamic_resizing=False)


def make_switch(parent, text: str, command: Optional[Callable] = None) -> ctk.CTkSwitch:
    return ctk.CTkSwitch(parent, text=text, command=command, font=theme.font(13),
                         text_color=theme.pair("text"), progress_color=theme.pair("cyan"),
                         button_color=("#FFFFFF", "#E6ECF8"), fg_color=theme.pair("border"))


class Card(ctk.CTkFrame):
    """Rounded surface with a subtle border."""

    def __init__(self, master, alt: bool = False, **kwargs) -> None:
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", theme.pair("border"))
        kwargs.setdefault("fg_color", theme.pair("card_alt" if alt else "card"))
        super().__init__(master, **kwargs)


class WrapLabel(ctk.CTkLabel):
    """Label whose wrap width follows the width of its container."""

    def __init__(self, master, text: str = "", size: int = 13, weight: str = "normal",
                 color: str = "text", pad: int = 0, mono: bool = False, **kwargs) -> None:
        kwargs.setdefault("anchor", "w")
        justify = kwargs.pop("justify", "left")
        super().__init__(master, text=text, font=theme.font(size, weight, mono),
                         text_color=theme.pair(color), wraplength=280, **kwargs)
        _apply_justify(self, justify)
        self._wrap_pad = pad
        self._wrap_width = 280
        master.bind("<Configure>", self._on_container_resize, add="+")

    def _on_container_resize(self, event) -> None:
        scale = 1.0
        try:
            scale = float(self._get_widget_scaling())
        except Exception:
            pass
        wrap = max(120, int(event.width / scale) - self._wrap_pad)
        if abs(wrap - self._wrap_width) > 4:
            self._wrap_width = wrap
            self.configure(wraplength=wrap)


class MessageBar(WrapLabel):
    """Inline success / error feedback."""

    def __init__(self, master, idle_text: str = "Results appear here.", height: int = 48, **kwargs) -> None:
        super().__init__(master, idle_text, size=12, color="muted", pad=8, height=height, **kwargs)
        self._idle_text = idle_text

    def show(self, message: str, success: bool = True) -> None:
        mark = "\u2713" if success else "\u2715"
        self.configure(text=f"{mark}  {message}", text_color=theme.pair("success" if success else "danger"))

    def reset(self) -> None:
        self.configure(text=self._idle_text, text_color=theme.pair("muted"))


class StatCard(Card):
    """Headline number with a coloured accent line."""

    def __init__(self, master, title: str, accent: str = "cyan") -> None:
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkFrame(self, height=3, corner_radius=2, fg_color=theme.pair(accent)).grid(
            row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
        make_label(self, title, 12, color="muted").grid(row=1, column=0, sticky="w", padx=18, pady=(8, 0))
        self.value_label = make_label(self, "0", 30, "bold", color=accent)
        self.value_label.grid(row=2, column=0, sticky="w", padx=18)
        self.hint_label = make_label(self, "", 11, color="muted")
        self.hint_label.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 14))

    def set_value(self, value, hint: str = "") -> None:
        self.value_label.configure(text=str(value))
        self.hint_label.configure(text=hint)
