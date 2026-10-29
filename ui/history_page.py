"""Operation History: searchable, filterable table with CSV export."""
from __future__ import annotations

from datetime import datetime
from tkinter import filedialog, ttk
from typing import Optional

import customtkinter as ctk

from constants import ALL_OPERATIONS, QUEUE, STACK
from . import theme
from .base_page import BasePage
from .components import Card, MessageBar, make_button, make_entry, make_label, make_option

ALL_STRUCTURES = "All structures"
ALL_OPS = "All operations"
COLUMNS = (
    ("number", "#", 60, "center"),
    ("structure", "Structure", 90, "w"),
    ("operation", "Operation", 110, "w"),
    ("value", "Value", 140, "w"),
    ("status", "Status", 90, "w"),
    ("details", "Details", 360, "w"),
    ("time", "Timestamp", 170, "w"),
)


class HistoryPage(BasePage):
    title = "Operation History"
    description = "Every stack and queue operation, including failed ones."

    def __init__(self, master, sim, app) -> None:
        super().__init__(master, sim, app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self) -> None:
        bar = Card(self)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        bar.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(bar, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        top.grid_columnconfigure(0, weight=1)
        self.search = make_entry(top, "Search value, operation, status or details")
        self.search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search.bind("<KeyRelease>", lambda _event: self.refresh())
        self.structure_filter = make_option(top, [ALL_STRUCTURES, STACK, QUEUE], lambda _v: self.refresh(), 150)
        self.structure_filter.grid(row=0, column=1, padx=4)
        self.operation_filter = make_option(top, [ALL_OPS, *ALL_OPERATIONS], lambda _v: self.refresh(), 150)
        self.operation_filter.grid(row=0, column=2, padx=4)

        actions = ctk.CTkFrame(bar, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 14))
        actions.grid_columnconfigure(3, weight=1)
        make_button(actions, "Refresh", self.refresh, "outline", width=110).grid(row=0, column=0, padx=(0, 8))
        make_button(actions, "Export CSV", self.do_export, "primary", width=130).grid(row=0, column=1, padx=(0, 8))
        make_button(actions, "Clear History", self.do_clear_history, "danger", width=130).grid(row=0, column=2)
        self.message = MessageBar(actions, "Clearing history never changes the stack or queue.", height=24)
        self.message.grid(row=0, column=3, sticky="ew", padx=(16, 0))

    def _build_table(self) -> None:
        card = Card(self)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(0, weight=1)
        holder = ctk.CTkFrame(card, fg_color="transparent")
        holder.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 4))
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(holder, columns=[c[0] for c in COLUMNS], show="headings",
                                 style="P17.Treeview", selectmode="browse")
        for key, heading, width, anchor in COLUMNS:
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, minwidth=50, anchor=anchor, stretch=(key == "details"))
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ctk.CTkScrollbar(holder, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.empty_label = make_label(holder, "", 13, color="muted", anchor="center")
        self.summary = make_label(card, "", 12, color="muted")
        self.summary.grid(row=1, column=0, sticky="w", padx=18, pady=(2, 12))
        self._style_table()

    def _style_table(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("P17.Treeview", background=theme.color("card"), fieldbackground=theme.color("card"),
                        foreground=theme.color("text"), borderwidth=0, rowheight=30, font=theme.tk_font(11))
        style.configure("P17.Treeview.Heading", background=theme.color("card_alt"), foreground=theme.color("text"),
                        relief="flat", borderwidth=0, font=theme.tk_font(11, "bold"))
        style.map("P17.Treeview", background=[("selected", theme.color("cell_fill"))],
                  foreground=[("selected", theme.color("text"))])
        style.map("P17.Treeview.Heading", background=[("active", theme.color("border"))])
        self.tree.tag_configure("ok", foreground=theme.color("text"))
        self.tree.tag_configure("failed", foreground=theme.color("danger"))

    # -- behaviour -----------------------------------------------------
    def _filters(self):
        structure = self.structure_filter.get()
        operation = self.operation_filter.get()
        return (None if structure == ALL_STRUCTURES else structure,
                None if operation == ALL_OPS else operation,
                self.search.get().strip() or None)

    def refresh(self) -> None:
        structure, operation, search = self._filters()
        records, matched = self.sim.query_history(structure, operation, search)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in records:
            self.tree.insert("", "end", values=record.as_row(), tags=("ok" if record.success else "failed",))
        total = self.sim.history.total_operations
        if not records:
            filtered = bool(structure or operation or search)
            self.empty_label.configure(text="No records match the current filters." if filtered else
                                       "No operations yet. Run an operation and it will be listed here.")
            self.empty_label.place(relx=0.5, rely=0.45, anchor="center")
        else:
            self.empty_label.place_forget()
        self.summary.configure(text=f"Showing {len(records)} of {matched} matching record(s)  \u00b7  "
                                    f"{total} operation(s) in total  \u00b7  display limit {self.sim.settings.history_limit}")

    def on_theme_changed(self) -> None:
        self._style_table()
        self.refresh()

    def do_clear_history(self) -> None:
        if self.sim.history.total_operations and not self.confirm_clear("the operation history"):
            return
        self.sim.clear_history()
        self.message.show("History cleared. The stack and queue were not changed.")

    def do_export(self) -> None:
        structure, operation, search = self._filters()
        _records, matched = self.sim.query_history(structure, operation, search, apply_limit=False)
        if not matched:
            self.message.show("There are no history records to export.", False)
            return
        default = f"p17_history_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path = filedialog.asksaveasfilename(parent=self, title="Export history", defaultextension=".csv",
                                            initialfile=default, filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        ok, message = self.sim.export_history(path, structure, operation, search)
        self.message.show(message, ok)
