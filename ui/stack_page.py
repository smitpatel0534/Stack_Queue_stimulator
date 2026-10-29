"""Stack simulator page (LIFO)."""
from __future__ import annotations

from typing import List, Optional, Tuple

from .structure_page import ButtonSpec, StructurePage


class StackPage(StructurePage):
    title = "Stack Simulator"
    description = "Push, pop and peek on a Last In, First Out stack."
    canvas_kind = "stack"
    heading = "Stack controls"
    blurb = "Type a value, then push it onto the top of the stack. Press Enter to push."
    placeholder = "Value to push, e.g. 42"
    visual_title = "Stack (LIFO)"
    visual_subtitle = "The last element pushed is the first one popped."
    elements_caption = "Elements (bottom to top)"
    empty_elements_text = "The stack is empty. Push a value to begin."

    def button_specs(self) -> List[ButtonSpec]:
        return [
            ("Push", self.do_push, "primary"),
            ("Pop", self.do_pop, "secondary"),
            ("Peek", self.do_peek, "outline"),
            ("Is Empty?", self.do_is_empty, "outline"),
            ("Clear Stack", self.do_clear, "danger"),
        ]

    def items(self) -> list:
        return self.sim.stack.to_list()

    def capacity(self) -> Optional[int]:
        return self.sim.stack.max_capacity

    def info_rows(self) -> List[Tuple[str, str]]:
        stack = self.sim.stack
        items = stack.to_list()
        capacity = stack.max_capacity
        return [
            ("Size", f"{stack.size} / {capacity}" if capacity else str(stack.size)),
            ("Top element", items[-1] if items else "\u2014"),
            ("Empty", "Yes" if stack.is_empty() else "No"),
            ("Full", "Yes" if stack.is_full() else "No"),
        ]

    def do_push(self) -> None:
        self.run(lambda: self.sim.push(self.entry.get()), clear_entry=True, highlight="top")

    def do_pop(self) -> None:
        self.run(self.sim.pop)

    def do_peek(self) -> None:
        self.run(self.sim.peek, highlight="top")

    def do_is_empty(self) -> None:
        self.run(self.sim.stack_is_empty)

    def do_clear(self) -> None:
        self.run_clear("stack", self.items(), self.sim.clear_stack)
