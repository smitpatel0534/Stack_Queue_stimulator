"""Dashboard: statistics, quick actions, structure overview and recent activity."""
from __future__ import annotations

from typing import List

import customtkinter as ctk

from . import theme
from .base_page import BasePage
from .components import Card, MessageBar, StatCard, WrapLabel, make_button, make_entry, make_label
from .structure_canvas import StructureCanvas

RECENT_ROWS = 8


class DashboardPage(BasePage):
    title = "Dashboard"
    description = "A live overview of your stack, queue and operation activity."

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, sim, app)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self._build_stats()
        self._build_left()
        self._build_activity()

    # -- construction --------------------------------------------------
    def _build_stats(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        specs = [("stack_size", "Stack size", "cyan"), ("queue_size", "Queue size", "violet"),
                 ("total", "Total operations", "blue"), ("successful", "Successful", "success"),
                 ("failed", "Failed", "danger")]
        self.stat_cards = {}
        for i, (key, title, accent) in enumerate(specs):
            row.grid_columnconfigure(i, weight=1, uniform="stat")
            card = StatCard(row, title, accent)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == len(specs) - 1 else 7))
            self.stat_cards[key] = card

    def _build_left(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 14))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        quick = Card(left)
        quick.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        quick.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="quick")
        make_label(quick, "Quick actions", 16, "bold").grid(row=0, column=0, columnspan=4, sticky="w",
                                                            padx=20, pady=(16, 8))
        self.entry = make_entry(quick, "Value for Push or Enqueue")
        self.entry.grid(row=1, column=0, columnspan=4, sticky="ew", padx=20, pady=(0, 10))
        buttons = [("Push", self.do_push, "primary"), ("Pop", self.do_pop, "secondary"),
                   ("Enqueue", self.do_enqueue, "primary"), ("Dequeue", self.do_dequeue, "secondary")]
        for i, (label, handler, style) in enumerate(buttons):
            make_button(quick, label, handler, style).grid(row=2, column=i, sticky="ew",
                                                           padx=(20 if i == 0 else 4, 20 if i == 3 else 4))
        self.message = MessageBar(quick, "Use the buttons above to run an operation.")
        self.message.grid(row=3, column=0, columnspan=4, sticky="ew", padx=20, pady=(8, 8))
        self.entry.bind("<Return>", lambda _event: self.do_push())

        overview = Card(left)
        overview.grid(row=1, column=0, sticky="nsew")
        overview.grid_columnconfigure(0, weight=2)
        overview.grid_columnconfigure(1, weight=3)
        overview.grid_rowconfigure(2, weight=1)
        make_label(overview, "Structure overview", 16, "bold").grid(row=0, column=0, columnspan=2, sticky="w",
                                                                    padx=20, pady=(16, 8))
        self.stack_caption = make_label(overview, "Stack (LIFO)", 12, color="muted")
        self.stack_caption.grid(row=1, column=0, sticky="w", padx=20)
        self.queue_caption = make_label(overview, "Queue (FIFO)", 12, color="muted")
        self.queue_caption.grid(row=1, column=1, sticky="w", padx=20)
        self.stack_canvas = StructureCanvas(overview, "stack", bg_name="card", height=180)
        self.stack_canvas.grid(row=2, column=0, sticky="nsew", padx=(16, 6), pady=(4, 16))
        self.queue_canvas = StructureCanvas(overview, "queue", bg_name="card", height=180)
        self.queue_canvas.grid(row=2, column=1, sticky="nsew", padx=(6, 16), pady=(4, 16))

    def _build_activity(self) -> None:
        card = Card(self)
        card.grid(row=1, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        make_label(card, "Recent activity", 16, "bold").grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        self.empty_state = WrapLabel(card, "No operations yet. Use the quick actions to push, pop, enqueue "
                                           "or dequeue, and each step will appear here.",
                                     13, color="muted", pad=40)
        self.empty_state.grid(row=1, column=0, sticky="nw", padx=20, pady=8)

        self.rows_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.rows_frame.grid_columnconfigure(0, weight=1)
        self.row_widgets: List[tuple] = []
        for i in range(RECENT_ROWS):
            line = ctk.CTkFrame(self.rows_frame, fg_color=theme.pair("card_alt"), corner_radius=10, height=40)
            line.grid(row=i, column=0, sticky="ew", pady=3)
            line.grid_columnconfigure(1, weight=1)
            dot = make_label(line, "\u25cf", 12, anchor="center", width=22)
            dot.grid(row=0, column=0, padx=(10, 0), pady=9)
            text = make_label(line, "", 13)
            text.grid(row=0, column=1, sticky="w", padx=(4, 6), pady=9)
            stamp = make_label(line, "", 11, color="muted", mono=True, anchor="e")
            stamp.grid(row=0, column=2, sticky="e", padx=(0, 12), pady=9)
            self.row_widgets.append((line, dot, text, stamp))

    # -- behaviour -----------------------------------------------------
    def refresh(self) -> None:
        stats = self.sim.stats()
        stack_cap, queue_cap = self.sim.stack.max_capacity, self.sim.queue.max_capacity
        self.stat_cards["stack_size"].set_value(stats["stack_size"], f"of {stack_cap} capacity")
        self.stat_cards["queue_size"].set_value(stats["queue_size"], f"of {queue_cap} capacity")
        self.stat_cards["total"].set_value(stats["total"], "stack and queue actions")
        rate = f"{round(100 * stats['successful'] / stats['total'])}% success rate" if stats["total"] else "no operations yet"
        self.stat_cards["successful"].set_value(stats["successful"], rate)
        self.stat_cards["failed"].set_value(stats["failed"], "underflow, overflow, bad input")

        self.stack_canvas.set_data(self.sim.stack.to_list(), stack_cap)
        self.queue_canvas.set_data(self.sim.queue.to_list(), queue_cap)

        records = self.sim.history.recent(RECENT_ROWS)
        if not records:
            self.rows_frame.grid_remove()
            self.empty_state.grid()
            return
        self.empty_state.grid_remove()
        self.rows_frame.grid(row=1, column=0, sticky="new", padx=16, pady=(0, 12))
        for i, (line, dot, text, stamp) in enumerate(self.row_widgets):
            if i >= len(records):
                line.grid_remove()
                continue
            record = records[i]
            line.grid()
            dot.configure(text_color=theme.pair("success" if record.success else "danger"))
            detail = f"'{record.value}'" if record.value else ""
            suffix = "" if record.success else " (failed)"
            text.configure(text=f"{record.structure} \u00b7 {record.operation} {detail}{suffix}".strip())
            stamp.configure(text=record.timestamp.strftime("%H:%M:%S"))

    def on_theme_changed(self) -> None:
        self.stack_canvas.apply_theme()
        self.queue_canvas.apply_theme()
        self.refresh()

    def _run(self, call, clear_entry: bool = False) -> None:
        result = call()
        self.message.show(result.message, result.success)
        if result.success and clear_entry:
            self.entry.delete(0, "end")
        self.entry.focus()

    def do_push(self) -> None:
        self._run(lambda: self.sim.push(self.entry.get()), clear_entry=True)

    def do_pop(self) -> None:
        self._run(self.sim.pop)

    def do_enqueue(self) -> None:
        self._run(lambda: self.sim.enqueue(self.entry.get()), clear_entry=True)

    def do_dequeue(self) -> None:
        self._run(self.sim.dequeue)
