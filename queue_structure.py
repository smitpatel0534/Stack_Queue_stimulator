"""A real FIFO queue with optional maximum capacity (named to avoid the stdlib ``queue``)."""
from __future__ import annotations

from collections import deque
from typing import Any, Deque, Iterator, List, Optional

from errors import StructureOverflowError, StructureUnderflowError


class QueueOverflowError(StructureOverflowError):
    """Raised when enqueueing into a full queue."""


class QueueUnderflowError(StructureUnderflowError):
    """Raised when dequeueing or peeking an empty queue."""


class Queue:
    """First In, First Out container. Index 0 is the front, the last index is the rear."""

    def __init__(self, max_capacity: Optional[int] = None) -> None:
        self._items: Deque[Any] = deque()
        self._max_capacity: Optional[int] = None
        self.set_capacity(max_capacity)

    # -- configuration -------------------------------------------------
    @property
    def max_capacity(self) -> Optional[int]:
        return self._max_capacity

    def set_capacity(self, max_capacity: Optional[int]) -> None:
        """Set the capacity (``None`` means unlimited)."""
        if max_capacity is not None:
            if isinstance(max_capacity, bool) or not isinstance(max_capacity, int) or max_capacity < 1:
                raise ValueError("Capacity must be a positive whole number or None.")
            if max_capacity < len(self._items):
                raise ValueError(
                    f"Cannot set capacity to {max_capacity}: the queue already holds {len(self._items)} elements."
                )
        self._max_capacity = max_capacity

    # -- operations ----------------------------------------------------
    def enqueue(self, value: Any) -> None:
        if self.is_full():
            raise QueueOverflowError(f"Queue overflow: capacity of {self._max_capacity} reached.")
        self._items.append(value)

    def dequeue(self) -> Any:
        if not self._items:
            raise QueueUnderflowError("Queue underflow: the queue is empty, nothing to dequeue.")
        return self._items.popleft()

    def front(self) -> Any:
        if not self._items:
            raise QueueUnderflowError("The queue is empty, so there is no front element.")
        return self._items[0]

    def rear(self) -> Any:
        if not self._items:
            raise QueueUnderflowError("The queue is empty, so there is no rear element.")
        return self._items[-1]

    def clear(self) -> int:
        """Remove every element and return how many were removed."""
        removed = len(self._items)
        self._items.clear()
        return removed

    # -- queries -------------------------------------------------------
    def is_empty(self) -> bool:
        return not self._items

    def is_full(self) -> bool:
        return self._max_capacity is not None and len(self._items) >= self._max_capacity

    @property
    def size(self) -> int:
        return len(self._items)

    def to_list(self) -> List[Any]:
        """Elements from front to rear (a copy)."""
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._items)

    def __repr__(self) -> str:
        return f"Queue({list(self._items)!r}, max_capacity={self._max_capacity!r})"
