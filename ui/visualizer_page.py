"""Data Structure Visualizer: large live views of the stack and queue."""
from __future__ import annotations

import customtkinter as ctk

from . import theme
from .base_page import BasePage
from .components import Card, make_label
from .structure_canvas import StructureCanvas


class VisualizerPage(BasePage):
    title = "Data Structure Visualizer"
    description = "Both structures, updated live after every operation."

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, sim, app)
        self.grid_columnconfigure(0, weight=2, uniform="viz")
        self.grid_columnconfigure(1, weight=3, uniform="viz")
        self.grid_rowconfigure(0, weight=1)

        self.stack_canvas, self.stack_info = self._panel(
            0, "Stack (LIFO)", "stack", (0, 14), "Push and pop happen at the top.")
        self.queue_canvas, self.queue_info = self._panel(
            1, "Queue (FIFO)", "queue", (0, 0), "Enqueue at the rear, dequeue from the front.")
        self._add_legend(self.queue_canvas.master)

    def _panel(self, column: int, title: str, kind: str, padx, subtitle: str):
        card = Card(self)
        card.grid(row=0, column=column, sticky="nsew", padx=padx)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)
        make_label(card, title, 18, "bold").grid(row=0, column=0, sticky="w", padx=20, pady=(18, 0))
        info = make_label(card, subtitle, 12, color="muted")
        info.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 8))
        canvas = StructureCanvas(card, kind)
        canvas.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        return canvas, info

    def _add_legend(self, card) -> None:
        legend = ctk.CTkFrame(card, fg_color="transparent")
        legend.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 14))
        for i, (label, tint) in enumerate([("Top / front", "cyan"), ("Rear", "violet"), ("Other elements", "cell_border")]):
            ctk.CTkFrame(legend, width=12, height=12, corner_radius=3, fg_color=theme.pair(tint)).grid(
                row=0, column=i * 2, padx=(0 if i == 0 else 14, 6))
            make_label(legend, label, 12, color="muted").grid(row=0, column=i * 2 + 1)

    def refresh(self) -> None:
        stack, queue = self.sim.stack, self.sim.queue
        stack_items, queue_items = stack.to_list(), queue.to_list()
        self.stack_canvas.set_data(stack_items, stack.max_capacity)
        self.queue_canvas.set_data(queue_items, queue.max_capacity)
        self.stack_info.configure(
            text=f"Size {stack.size} \u00b7 Top: {stack_items[-1]}" if stack_items else "Empty. Push a value to begin.")
        self.queue_info.configure(
            text=(f"Size {queue.size} \u00b7 Front: {queue_items[0]} \u00b7 Rear: {queue_items[-1]}"
                  if queue_items else "Empty. Enqueue a value to begin."))

    def on_theme_changed(self) -> None:
        self.stack_canvas.apply_theme()
        self.queue_canvas.apply_theme()
        self.refresh()
