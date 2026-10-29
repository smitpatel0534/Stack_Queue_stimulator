"""Main window: sidebar, top bar and page switching."""
from __future__ import annotations

from datetime import datetime
from typing import Dict

import customtkinter as ctk

from constants import APP_NAME, APP_VERSION
from . import theme
from .about_page import AboutPage
from .base_page import BasePage
from .components import make_button, make_label
from .dashboard import DashboardPage
from .history_page import HistoryPage
from .queue_page import QueuePage
from .settings_page import SettingsPage
from .stack_page import StackPage
from .visualizer_page import VisualizerPage

NAV_ITEMS = [
    ("dashboard", "Dashboard", "\u2302", DashboardPage),
    ("stack", "Stack Simulator", "\u25a4", StackPage),
    ("queue", "Queue Simulator", "\u25a5", QueuePage),
    ("history", "Operation History", "\u2630", HistoryPage),
    ("visualizer", "Data Structure Visualizer", "\u25c8", VisualizerPage),
    ("settings", "Settings", "\u2699", SettingsPage),
    ("about", "About", "\u24d8", AboutPage),
]


class App(ctk.CTk):
    def __init__(self, sim) -> None:
        super().__init__()
        self.sim = sim
        theme.set_mode(sim.settings.theme)
        ctk.set_appearance_mode(sim.settings.theme)
        self.title(APP_NAME)
        self._fit_window()
        self.configure(fg_color=theme.pair("bg"))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.pages: Dict[str, BasePage] = {}
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.current: str = ""
        self._clock_job = None

        self._build_sidebar()
        self._build_main()
        for key, _label, _icon, page_class in NAV_ITEMS:
            page = page_class(self.content, sim, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

        sim.subscribe(self._on_state_change)
        self._update_status()
        self._update_theme_button()
        self.show_page("dashboard")
        self._tick()
        self.protocol("WM_DELETE_WINDOW", self._handle_close)

    def _fit_window(self) -> None:
        """Pick a start size that fits the screen, including high-DPI scaling."""
        try:
            scale = float(self._get_window_scaling())
        except Exception:
            scale = 1.0
        width = int(min(1280, self.winfo_screenwidth() * 0.94 / scale))
        height = int(min(800, (self.winfo_screenheight() - 90) / scale))
        self.geometry(f"{width}x{height}")
        self.minsize(min(1080, width), min(680, height))

    # -- construction --------------------------------------------------
    def _build_sidebar(self) -> None:
        side = ctk.CTkFrame(self, width=268, corner_radius=0, fg_color=theme.pair("surface"))
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(side, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 22))
        make_label(brand, "P17", 34, "bold", color="cyan").grid(row=0, column=0, sticky="w")
        make_label(brand, "Stack & Queue\nOperations Simulator", 12, color="muted", justify="left").grid(
            row=1, column=0, sticky="w")
        ctk.CTkFrame(brand, height=3, width=56, corner_radius=2, fg_color=theme.pair("violet")).grid(
            row=2, column=0, sticky="w", pady=(10, 0))

        for i, (key, label, icon, _cls) in enumerate(NAV_ITEMS):
            button = ctk.CTkButton(side, text=f"{icon}   {label}", anchor="w", height=42, corner_radius=10,
                                   font=theme.font(14), fg_color="transparent", text_color=theme.pair("text"),
                                   hover_color=theme.pair("card_alt"), command=lambda k=key: self.show_page(k))
            button.grid(row=i + 1, column=0, sticky="ew", padx=14, pady=2)
            self.nav_buttons[key] = button

        side.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)
        make_label(side, f"Version {APP_VERSION}\nRuns offline on this computer", 11, color="muted",
                   justify="left").grid(row=len(NAV_ITEMS) + 2, column=0, sticky="w", padx=20, pady=(0, 20))

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(main, height=84, corner_radius=0, fg_color=theme.pair("surface"))
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        titles = ctk.CTkFrame(bar, fg_color="transparent")
        titles.grid(row=0, column=0, sticky="w", padx=26, pady=14)
        self.title_label = make_label(titles, "", 22, "bold")
        self.title_label.grid(row=0, column=0, sticky="w")
        self.description_label = make_label(titles, "", 12, color="muted")
        self.description_label.grid(row=1, column=0, sticky="w")

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e", padx=(0, 22))
        self.status_label = ctk.CTkLabel(right, text="", font=theme.font(12, "bold"), corner_radius=14,
                                         fg_color=theme.pair("card_alt"), height=28)
        self.status_label.grid(row=0, column=0, padx=(0, 12))
        self.clock_label = make_label(right, "", 12, color="muted", mono=True)
        self.clock_label.grid(row=0, column=1, padx=(0, 12))
        make_label(right, f"v{APP_VERSION}", 12, color="muted").grid(row=0, column=2, padx=(0, 12))
        self.theme_button = make_button(right, "", self.toggle_theme, "outline", height=32, width=130)
        self.theme_button.grid(row=0, column=3)

        self.content = ctk.CTkFrame(main, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=24, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    # -- navigation ----------------------------------------------------
    def show_page(self, key: str) -> None:
        page = self.pages[key]
        self.current = key
        page.tkraise()
        self.title_label.configure(text=page.title)
        self.description_label.configure(text=page.description)
        for name, button in self.nav_buttons.items():
            if name == key:
                button.configure(fg_color=theme.pair("nav_active"), text_color=theme.pair("cyan"))
            else:
                button.configure(fg_color="transparent", text_color=theme.pair("text"))
        page.on_show()

    # -- state ---------------------------------------------------------
    def _on_state_change(self) -> None:
        self._sync_theme()
        self._update_status()
        if self.current:
            self.pages[self.current].refresh()

    def _update_status(self) -> None:
        result = self.sim.last_result
        if result is None:
            text, tint = "  \u25cf  Ready  ", "success"
        elif result.success:
            text, tint = "  \u25cf  Last operation succeeded  ", "success"
        else:
            text, tint = "  \u25cf  Last operation failed  ", "danger"
        self.status_label.configure(text=text, text_color=theme.pair(tint))

    def _sync_theme(self) -> None:
        mode = self.sim.settings.theme
        if mode == theme.get_mode():
            return
        theme.set_mode(mode)
        ctk.set_appearance_mode(mode)
        self._update_theme_button()
        for page in self.pages.values():
            page.on_theme_changed()

    def _update_theme_button(self) -> None:
        self.theme_button.configure(text="\u25d0  Dark mode" if theme.get_mode() == "dark" else "\u25d1  Light mode")

    def toggle_theme(self) -> None:
        self.sim.set_theme("light" if theme.get_mode() == "dark" else "dark")

    def _tick(self) -> None:
        self.clock_label.configure(text=datetime.now().strftime("%a %d %b %Y  %H:%M:%S"))
        self._clock_job = self.after(1000, self._tick)

    def _handle_close(self) -> None:
        if self._clock_job is not None:
            try:
                self.after_cancel(self._clock_job)
            except Exception:
                pass
        self.sim.unsubscribe(self._on_state_change)
        self.destroy()
