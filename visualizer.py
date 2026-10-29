"""Pure layout maths for drawing the stack and queue (no GUI imports, so it is unit-testable).

Large structures never overflow the canvas: the stack shows its top elements and
a "more below" marker; the queue shows elements near the front and rear with an
ellipsis cell in between.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Cell:
    kind: str       # "item" or "gap"
    index: int      # element index, -1 for a gap marker
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class Layout:
    cells: Tuple[Cell, ...]
    hidden: int = 0


def shorten(text: str, max_chars: int) -> str:
    """Truncate with an ellipsis so text always fits its cell."""
    if len(text) <= max_chars:
        return text
    return text[: max(1, max_chars - 1)] + "\u2026"


def compute_stack_layout(count: int, width: float, height: float, *, pad: float = 18, gap: float = 4,
                         max_cell: float = 46, min_cell: float = 28, label_space: float = 96,
                         max_width: float = 300) -> Layout:
    """Cells are stacked from the bottom; index 0 is the bottom element."""
    if count <= 0 or width <= 0 or height <= 0:
        return Layout(())
    avail_h = max(float(height) - 2 * pad, float(min_cell))
    slots = max(1, int((avail_h + gap) // (min_cell + gap)))
    if count <= slots:
        shown = list(range(count))
        hidden = 0
        cell_h = min(float(max_cell), (avail_h - gap * (count - 1)) / count)
    else:
        n_items = max(1, slots - 1)
        shown = list(range(count - n_items, count))
        hidden = count - n_items
        cell_h = float(min_cell)
    cell_w = float(min(max_width, max(80.0, width - 2 * pad - label_space)))
    x0 = max(float(pad), (width - (cell_w + label_space)) / 2)
    bottom = float(height) - pad
    cells = []
    row = 0
    if hidden:
        y1 = bottom
        cells.append(Cell("gap", -1, x0, y1 - cell_h, x0 + cell_w, y1))
        row = 1
    for index in shown:
        y1 = bottom - row * (cell_h + gap)
        cells.append(Cell("item", index, x0, y1 - cell_h, x0 + cell_w, y1))
        row += 1
    return Layout(tuple(cells), hidden)


def compute_queue_layout(count: int, width: float, height: float, *, pad: float = 22, gap: float = 26,
                         cell_w: float = 78, cell_h: float = 58) -> Layout:
    """Cells run left to right; index 0 is the front, the last index is the rear."""
    if count <= 0 or width <= 0 or height <= 0:
        return Layout(())
    avail = max(float(width) - 2 * pad, 120.0)
    slots = max(1, int((avail + gap) // (cell_w + gap)))
    if count <= slots:
        entries = [("item", i) for i in range(count)]
        hidden = 0
    else:
        slots = max(slots, 3)
        tail = (slots - 1) // 2
        head = slots - 1 - tail
        entries = ([("item", i) for i in range(head)] + [("gap", -1)]
                   + [("item", i) for i in range(count - tail, count)])
        hidden = count - head - tail
    n = len(entries)
    w = float(cell_w)
    if n * w + (n - 1) * gap > avail:
        w = (avail - (n - 1) * gap) / n
    total = n * w + (n - 1) * gap
    x = (width - total) / 2
    cy = height / 2 + 6
    cells = []
    for kind, index in entries:
        cells.append(Cell(kind, index, x, cy - cell_h / 2, x + w, cy + cell_h / 2))
        x += w + gap
    return Layout(tuple(cells), hidden)
