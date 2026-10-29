"""Base class shared by every page."""
from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk


class BasePage(ctk.CTkFrame):
    title = ""
    description = ""

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.sim = sim
        self.app = app

    def refresh(self) -> None:
        """Re-read application state and update widgets."""

    def on_show(self) -> None:
        self.refresh()

    def on_theme_changed(self) -> None:
        self.refresh()

    def confirm_clear(self, what: str) -> bool:
        """Ask before clearing when the user has that option enabled."""
        if not self.sim.settings.confirm_before_clear:
            return True
        return bool(messagebox.askyesno("Confirm clear", f"Clear {what}? This cannot be undone.", parent=self))
