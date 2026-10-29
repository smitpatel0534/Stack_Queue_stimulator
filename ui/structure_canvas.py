"""Canvas widget that draws a stack (vertical) or a queue (horizontal)."""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence

from visualizer import compute_queue_layout, compute_stack_layout, shorten

from . import theme


class StructureCanvas(tk.Canvas):
    FLASH_MS = 700

    def __init__(self, master, kind: str, bg_name: str = "card", **kwargs) -> None:
        super().__init__(master, bg=theme.color(bg_name), highlightthickness=0, bd=0, **kwargs)
        self.kind = kind  # "stack" or "queue"
        self._bg_name = bg_name
        self._items: list = []
        self._capacity: Optional[int] = None
        self._flash_index: Optional[int] = None
        self._flash_job = None
        self.bind("<Configure>", lambda _event: self.redraw())

    # -- public API ----------------------------------------------------
    def set_data(self, items: Sequence, capacity: Optional[int] = None) -> None:
        self._items = [str(i) for i in items]
        self._capacity = capacity
        self.redraw()

    def flash(self, index: int) -> None:
        """Highlight one element briefly so the change is easy to see."""
        self._cancel_flash()
        self._flash_index = index
        self.redraw()
        self._flash_job = self.after(self.FLASH_MS, self._end_flash)

    def apply_theme(self) -> None:
        self.configure(bg=theme.color(self._bg_name))
        self.redraw()

    # -- internals -----------------------------------------------------
    def _cancel_flash(self) -> None:
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except Exception:
                pass
            self._flash_job = None

    def _end_flash(self) -> None:
        self._flash_job = None
        self._flash_index = None
        try:
            self.redraw()
        except tk.TclError:
            pass  # widget was destroyed

    def _rounded(self, x0, y0, x1, y1, radius, **kwargs):
        r = max(2, min(radius, (x1 - x0) / 2, (y1 - y0) / 2))
        points = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
                  x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
        return self.create_polygon(points, smooth=True, **kwargs)

    def redraw(self) -> None:
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width < 80 or height < 80:
            return
        if self.kind == "stack":
            self._draw_stack(width, height)
        else:
            self._draw_queue(width, height)
        self._draw_footer(width, height)

    def _draw_empty(self, width: int, height: int, title: str, hint: str) -> None:
        pad_x, pad_y = width * 0.15, height * 0.3
        self._rounded(pad_x, pad_y, width - pad_x, height - pad_y, 14,
                      fill="", outline=theme.color("border"), width=2)
        self.create_text(width / 2, height / 2 - 12, text=title, fill=theme.color("text"),
                         font=theme.tk_font(15, "bold"))
        self.create_text(width / 2, height / 2 + 14, text=hint, fill=theme.color("muted"),
                         font=theme.tk_font(11))

    def _draw_footer(self, width: int, height: int) -> None:
        count = len(self._items)
        text = f"{count} / {self._capacity} used" if self._capacity else f"{count} element(s)"
        if self.kind == "queue":
            text += "   \u00b7   Dequeue leaves from the front, enqueue joins at the rear"
        self.create_text(14, height - 8, text=text, anchor="sw", fill=theme.color("muted"),
                         font=theme.tk_font(10))

    def _cell_style(self, flashing: bool, role: str):
        if flashing:
            return theme.color("flash_fill"), theme.color("flash_fill"), theme.color("flash_text")
        fill = {"top": "top_fill", "front": "top_fill", "rear": "rear_fill"}.get(role, "cell_fill")
        border = {"top": "top_border", "front": "top_border", "rear": "rear_border"}.get(role, "cell_border")
        return theme.color(fill), theme.color(border), theme.color("text")

    def _draw_stack(self, width: int, height: int) -> None:
        count = len(self._items)
        layout = compute_stack_layout(count, width, height - 14)
        if not layout.cells:
            self._draw_empty(width, height, "Stack is empty", "Push a value to see it here.")
            return
        for cell in layout.cells:
            cy = (cell.y0 + cell.y1) / 2
            if cell.kind == "gap":
                self.create_text((cell.x0 + cell.x1) / 2, cy, text=f"\u22ee  {layout.hidden} more below",
                                 fill=theme.color("muted"), font=theme.tk_font(11))
                continue
            index = cell.index
            is_top = index == count - 1
            fill, border, text_color = self._cell_style(index == self._flash_index, "top" if is_top else "")
            self._rounded(cell.x0, cell.y0, cell.x1, cell.y1, 10, fill=fill, outline=border,
                          width=2 if is_top else 1)
            self.create_text(cell.x0 + 14, cy, text=str(index), anchor="w", fill=theme.color("muted"),
                             font=theme.tk_font(10, mono=True))
            self.create_text((cell.x0 + cell.x1) / 2, cy, text=shorten(self._items[index], 26),
                             fill=text_color, font=theme.tk_font(13, "bold", mono=True))
            if is_top:
                self.create_text(cell.x1 + 12, cy, text="\u25c4 Top", anchor="w",
                                 fill=theme.color("cyan"), font=theme.tk_font(12, "bold"))
            elif index == 0:
                self.create_text(cell.x1 + 12, cy, text="Bottom", anchor="w",
                                 fill=theme.color("muted"), font=theme.tk_font(11))

    def _draw_queue(self, width: int, height: int) -> None:
        count = len(self._items)
        layout = compute_queue_layout(count, width, height)
        if not layout.cells:
            self._draw_empty(width, height, "Queue is empty", "Enqueue a value to see it here.")
            return
        previous = None
        for cell in layout.cells:
            cy = (cell.y0 + cell.y1) / 2
            if previous is not None:
                self.create_line(previous.x1 + 4, cy, cell.x0 - 4, cy, arrow="last", width=2,
                                 fill=theme.color("muted"))
            previous = cell
            if cell.kind == "gap":
                self._rounded(cell.x0, cell.y0, cell.x1, cell.y1, 10, fill="", outline=theme.color("border"),
                              width=1, dash=(3, 3))
                self.create_text((cell.x0 + cell.x1) / 2, cy, text=f"\u2026 +{layout.hidden}",
                                 fill=theme.color("muted"), font=theme.tk_font(12, "bold"))
                continue
            index = cell.index
            role = "front" if index == 0 else ("rear" if index == count - 1 else "")
            fill, border, text_color = self._cell_style(index == self._flash_index, role)
            self._rounded(cell.x0, cell.y0, cell.x1, cell.y1, 10, fill=fill, outline=border,
                          width=2 if role else 1)
            self.create_text((cell.x0 + cell.x1) / 2, cy, text=shorten(self._items[index], 9),
                             fill=text_color, font=theme.tk_font(13, "bold", mono=True))
            self.create_text(cell.x0 + 6, cell.y1 - 8, text=str(index), anchor="sw",
                             fill=theme.color("muted"), font=theme.tk_font(9, mono=True))
            label = None
            if count == 1:
                label, tint = "Front \u00b7 Rear", "cyan"
            elif index == 0:
                label, tint = "Front", "cyan"
            elif index == count - 1:
                label, tint = "Rear", "violet"
            if label:
                self.create_text((cell.x0 + cell.x1) / 2, cell.y0 - 20, text=label, fill=theme.color(tint),
                                 font=theme.tk_font(12, "bold"))
                self.create_text((cell.x0 + cell.x1) / 2, cell.y0 - 6, text="\u25bc", fill=theme.color(tint),
                                 font=theme.tk_font(8))
