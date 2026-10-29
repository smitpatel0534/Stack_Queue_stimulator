"""Settings: theme, capacities, history limit and confirmation behaviour."""
from __future__ import annotations

import customtkinter as ctk

from settings_manager import LIMITS, MAX_DEVELOPER_INFO
from .base_page import BasePage
from .components import Card, MessageBar, WrapLabel, make_button, make_entry, make_label, make_switch


class SettingsPage(BasePage):
    title = "Settings"
    description = "Changes are validated, applied immediately and saved on this computer."

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, sim, app)
        self.grid_columnconfigure(0, weight=1)
        card = Card(self)
        card.grid(row=0, column=0, sticky="new")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)

        self.theme_switch = make_switch(card, "Dark mode", self.on_theme_switch)
        self._row(card, 0, "Appearance", "Switch between the dark and light theme.", self.theme_switch)
        self.stack_entry = make_entry(card, width=120)
        self._row(card, 1, "Maximum stack capacity",
                  f"Whole number from {LIMITS['max_stack_capacity'][0]} to {LIMITS['max_stack_capacity'][1]}.",
                  self.stack_entry)
        self.queue_entry = make_entry(card, width=120)
        self._row(card, 2, "Maximum queue capacity",
                  f"Whole number from {LIMITS['max_queue_capacity'][0]} to {LIMITS['max_queue_capacity'][1]}.",
                  self.queue_entry)
        self.history_entry = make_entry(card, width=120)
        self._row(card, 3, "History display limit",
                  f"Rows shown in the history table ({LIMITS['history_limit'][0]} to {LIMITS['history_limit'][1]}). "
                  "Totals always count every operation.", self.history_entry)
        self.confirm_switch = make_switch(card, "Ask first")
        self._row(card, 4, "Confirm before clearing",
                  "Show a confirmation before clearing the stack, queue or history.", self.confirm_switch)
        self.developer_entry = make_entry(card, width=300)
        self._row(card, 5, "Developer information",
                  f"Shown on the About page, up to {MAX_DEVELOPER_INFO} characters.", self.developer_entry)

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=6, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))
        make_button(buttons, "Save settings", self.do_apply, "primary", width=150).grid(row=0, column=0, padx=(0, 10))
        make_button(buttons, "Reset to defaults", self.do_reset, "outline", width=160).grid(row=0, column=1)
        self.message = MessageBar(card, "Edit a value, then choose Save settings.", height=70)
        self.message.grid(row=7, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 14))
        self.load_form()

    def _row(self, card, row: int, title: str, hint: str, widget) -> None:
        text = ctk.CTkFrame(card, fg_color="transparent")
        text.grid(row=row, column=0, sticky="ew", padx=(20, 10), pady=(14 if row == 0 else 8, 6))
        make_label(text, title, 14, "bold").grid(row=0, column=0, sticky="w")
        WrapLabel(text, hint, 12, color="muted", pad=10).grid(row=1, column=0, sticky="w")
        widget.grid(row=row, column=1, sticky="e", padx=(10, 20), pady=(14 if row == 0 else 8, 6))

    # -- behaviour -----------------------------------------------------
    def load_form(self) -> None:
        s = self.sim.settings
        self.theme_switch.select() if s.theme == "dark" else self.theme_switch.deselect()
        self.confirm_switch.select() if s.confirm_before_clear else self.confirm_switch.deselect()
        for entry, value in ((self.stack_entry, s.max_stack_capacity), (self.queue_entry, s.max_queue_capacity),
                             (self.history_entry, s.history_limit), (self.developer_entry, s.developer_info)):
            entry.delete(0, "end")
            entry.insert(0, str(value))

    def refresh(self) -> None:
        # Keep the theme switch in step with the top-bar toggle without touching text being edited.
        self.theme_switch.select() if self.sim.settings.theme == "dark" else self.theme_switch.deselect()

    def on_show(self) -> None:
        self.load_form()
        self.message.reset()

    def on_theme_switch(self) -> None:
        errors = self.sim.set_theme("dark" if self.theme_switch.get() else "light")
        if errors:
            self.message.show("\n".join(errors), False)
        else:
            self.message.show(f"Theme changed to {self.sim.settings.theme} mode.")

    def do_apply(self) -> None:
        raw = {
            "theme": "dark" if self.theme_switch.get() else "light",
            "max_stack_capacity": self.stack_entry.get(),
            "max_queue_capacity": self.queue_entry.get(),
            "history_limit": self.history_entry.get(),
            "confirm_before_clear": bool(self.confirm_switch.get()),
            "developer_info": self.developer_entry.get(),
        }
        errors = self.sim.apply_settings(raw)
        if errors:
            self.message.show("\n".join(errors), False)
            return
        self.load_form()
        self.message.show("Settings saved.")

    def do_reset(self) -> None:
        errors = self.sim.reset_settings()
        if errors:
            self.message.show("\n".join(errors), False)
            return
        self.load_form()
        self.message.show("Settings reset to defaults.")
