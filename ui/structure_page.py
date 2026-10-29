"""Shared layout for the Stack and Queue simulator pages."""
from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

import customtkinter as ctk

from . import theme
from .base_page import BasePage
from .components import Card, MessageBar, WrapLabel, make_button, make_entry, make_label
from .structure_canvas import StructureCanvas

ButtonSpec = Tuple[str, Callable[[], None], str]  # (label, handler, style)


class StructurePage(BasePage):
    canvas_kind = "stack"
    heading = ""
    blurb = ""
    placeholder = "Enter a value"
    visual_title = ""
    visual_subtitle = ""
    elements_caption = ""
    empty_elements_text = "No elements yet."

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, sim, app)
        self.grid_columnconfigure(0, weight=0, minsize=360)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_controls()
        self._build_visual()

    # -- hooks implemented by subclasses ------------------------------
    def button_specs(self) -> List[ButtonSpec]:
        raise NotImplementedError

    def info_rows(self) -> List[Tuple[str, str]]:
        raise NotImplementedError

    def items(self) -> list:
        raise NotImplementedError

    def capacity(self) -> Optional[int]:
        raise NotImplementedError

    # -- construction --------------------------------------------------
    def _build_controls(self) -> None:
        card = Card(self)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        card.grid_columnconfigure((0, 1), weight=1, uniform="buttons")
        make_label(card, self.heading, 18, "bold").grid(row=0, column=0, columnspan=2, sticky="w",
                                                        padx=20, pady=(18, 0))
        WrapLabel(card, self.blurb, 12, color="muted", pad=40).grid(row=1, column=0, columnspan=2,
                                                                    sticky="w", padx=20, pady=(2, 12))
        self.entry = make_entry(card, self.placeholder)
        self.entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 12))

        specs = self.button_specs()
        row = 3
        for i, (label, handler, style) in enumerate(specs):
            is_last_odd = i == len(specs) - 1 and len(specs) % 2 == 1
            button = make_button(card, label, handler, style)
            if is_last_odd:
                button.grid(row=row + i // 2, column=0, columnspan=2, sticky="ew", padx=20, pady=4)
            else:
                button.grid(row=row + i // 2, column=i % 2, sticky="ew",
                            padx=(20, 4) if i % 2 == 0 else (4, 20), pady=4)
        row += (len(specs) + 1) // 2
        self._primary_handler = specs[0][1]
        self.entry.bind("<Return>", lambda _event: self._primary_handler())

        self.message = MessageBar(card)
        self.message.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 4))

        info = ctk.CTkFrame(card, fg_color=theme.pair("card_alt"), corner_radius=10)
        info.grid(row=row + 1, column=0, columnspan=2, sticky="ew", padx=20, pady=(4, 8))
        info.grid_columnconfigure(1, weight=1)
        self._info_values: List[ctk.CTkLabel] = []
        for i, (label, _value) in enumerate(self.info_rows()):
            make_label(info, label, 12, color="muted").grid(row=i, column=0, sticky="w", padx=(14, 8),
                                                            pady=(10 if i == 0 else 2, 2))
            value = make_label(info, "", 13, "bold", mono=True, anchor="e")
            value.grid(row=i, column=1, sticky="e", padx=(8, 14), pady=(10 if i == 0 else 2, 2))
            self._info_values.append(value)
        info.grid_rowconfigure(len(self._info_values), minsize=8)

        make_label(card, self.elements_caption, 12, color="muted").grid(
            row=row + 2, column=0, columnspan=2, sticky="w", padx=20, pady=(6, 0))
        self.elements_label = WrapLabel(card, "", 12, mono=True, pad=40)
        self.elements_label.grid(row=row + 3, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 16))

    def _build_visual(self) -> None:
        card = Card(self)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)
        make_label(card, self.visual_title, 18, "bold").grid(row=0, column=0, sticky="w", padx=20, pady=(18, 0))
        make_label(card, self.visual_subtitle, 12, color="muted").grid(row=1, column=0, sticky="w",
                                                                       padx=20, pady=(0, 8))
        self.canvas = StructureCanvas(card, self.canvas_kind)
        self.canvas.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))

    # -- behaviour -----------------------------------------------------
    def refresh(self) -> None:
        items = self.items()
        self.canvas.set_data(items, self.capacity())
        for label, (_name, value) in zip(self._info_values, self.info_rows()):
            label.configure(text=value)
        self.elements_label.configure(text=self._elements_text(items))

    def on_theme_changed(self) -> None:
        self.canvas.apply_theme()
        self.refresh()

    def _elements_text(self, items: Sequence) -> str:
        if not items:
            return self.empty_elements_text
        text = ", ".join(str(i) for i in items)
        if len(text) > 220:
            text = text[:220].rsplit(",", 1)[0] + f", \u2026 ({len(items)} total)"
        return text

    def run(self, call: Callable, clear_entry: bool = False, highlight: Optional[str] = None) -> None:
        """Run an operation, show its message and flash the affected element."""
        result = call()
        self.message.show(result.message, result.success)
        if result.success:
            if clear_entry:
                self.entry.delete(0, "end")
            items = self.items()
            if highlight and items:
                self.canvas.flash({"front": 0, "top": len(items) - 1, "rear": len(items) - 1}[highlight])
        self.entry.focus()

    def run_clear(self, noun: str, items: Sequence, call: Callable) -> None:
        if items and not self.confirm_clear(f"the {noun} ({len(items)} element(s))"):
            return
        self.run(call)
