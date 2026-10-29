"""Queue simulator page (FIFO)."""
from __future__ import annotations

from typing import List, Optional, Tuple

from .structure_page import ButtonSpec, StructurePage


class QueuePage(StructurePage):
    title = "Queue Simulator"
    description = "Enqueue and dequeue on a First In, First Out queue."
    canvas_kind = "queue"
    heading = "Queue controls"
    blurb = "Type a value, then add it at the rear of the queue. Press Enter to enqueue."
    placeholder = "Value to enqueue, e.g. job-7"
    visual_title = "Queue (FIFO)"
    visual_subtitle = "The first element enqueued is the first one dequeued."
    elements_caption = "Elements (front to rear)"
    empty_elements_text = "The queue is empty. Enqueue a value to begin."

    def button_specs(self) -> List[ButtonSpec]:
        return [
            ("Enqueue", self.do_enqueue, "primary"),
            ("Dequeue", self.do_dequeue, "secondary"),
            ("Peek Front", self.do_front, "outline"),
            ("Peek Rear", self.do_rear, "outline"),
            ("Is Empty?", self.do_is_empty, "outline"),
            ("Clear Queue", self.do_clear, "danger"),
        ]

    def items(self) -> list:
        return self.sim.queue.to_list()

    def capacity(self) -> Optional[int]:
        return self.sim.queue.max_capacity

    def info_rows(self) -> List[Tuple[str, str]]:
        queue = self.sim.queue
        items = queue.to_list()
        capacity = queue.max_capacity
        return [
            ("Size", f"{queue.size} / {capacity}" if capacity else str(queue.size)),
            ("Front element", items[0] if items else "\u2014"),
            ("Rear element", items[-1] if items else "\u2014"),
            ("Empty", "Yes" if queue.is_empty() else "No"),
        ]

    def do_enqueue(self) -> None:
        self.run(lambda: self.sim.enqueue(self.entry.get()), clear_entry=True, highlight="rear")

    def do_dequeue(self) -> None:
        self.run(self.sim.dequeue)

    def do_front(self) -> None:
        self.run(self.sim.peek_front, highlight="front")

    def do_rear(self) -> None:
        self.run(self.sim.peek_rear, highlight="rear")

    def do_is_empty(self) -> None:
        self.run(self.sim.queue_is_empty)

    def do_clear(self) -> None:
        self.run_clear("queue", self.items(), self.sim.clear_queue)
