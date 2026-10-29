"""About page."""
from __future__ import annotations

from constants import APP_NAME, APP_VERSION
from .base_page import BasePage
from .components import Card, WrapLabel, make_label


class AboutPage(BasePage):
    title = "About"
    description = "What this project is and the ideas behind it."

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, sim, app)
        self.grid_columnconfigure(0, weight=1, uniform="about")
        self.grid_columnconfigure(1, weight=1, uniform="about")
        left_rows = [
            ("Project", f"{APP_NAME}\nVersion {APP_VERSION}",
             "An interactive desktop simulator for two fundamental data structures. Run real push, pop, "
             "enqueue and dequeue operations, watch the structures change as you work, and review every "
             "action in a searchable history."),
            ("Technologies", "",
             "Python 3.11+, CustomTkinter, Tkinter and ttk, unittest. Settings are stored as JSON and "
             "history exports are CSV. Everything runs offline."),
        ]
        for row, (heading, sub, body) in enumerate(left_rows):
            self._card(0, row, heading, sub, body, padx=(0, 7))
        self.developer_label = self._card(0, 2, "Developer", "", "", padx=(0, 7))
        self._card(1, 0, "Stack: LIFO", "Last In, First Out",
                   "The most recently pushed element is the first one popped, like a pile of plates where "
                   "you only touch the top. Push, pop and peek all work at the top. Stacks power undo "
                   "history, function call tracking and expression evaluation.", padx=(7, 0))
        self._card(1, 1, "Queue: FIFO", "First In, First Out",
                   "Elements leave in the order they arrived, like people waiting in line. Enqueue adds at "
                   "the rear and dequeue removes from the front. Queues drive task scheduling, print jobs "
                   "and data buffering.", padx=(7, 0))
        self.grid_rowconfigure(3, weight=1)

    def _card(self, column: int, row: int, heading: str, sub: str, body: str, padx):
        card = Card(self)
        card.grid(row=row, column=column, sticky="new", padx=padx, pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)
        make_label(card, heading, 17, "bold").grid(row=0, column=0, sticky="w", padx=20, pady=(16, 2))
        if sub:
            make_label(card, sub, 13, color="cyan", justify="left").grid(row=1, column=0, sticky="w", padx=20)
        label = WrapLabel(card, body, 13, color="muted", pad=40)
        label.grid(row=2, column=0, sticky="w", padx=20, pady=(6, 16))
        return label

    def refresh(self) -> None:
        self.developer_label.configure(text=self.sim.settings.developer_info)
