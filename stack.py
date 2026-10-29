"""A real LIFO stack with optional maximum capacity."""
from __future__ import annotations

from typing import Any, Iterator, List, Optional

from errors import StructureOverflowError, StructureUnderflowError


class StackOverflowError(StructureOverflowError):
    """Raised when pushing onto a full stack."""


class StackUnderflowError(StructureUnderflowError):
    """Raised when popping or peeking an empty stack."""


class Stack:
    """Last In, First Out container. The end of the list is the top."""

    def __init__(self, max_capacity: Optional[int] = None) -> None:
        self._items: List[Any] = []
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
                    f"Cannot set capacity to {max_capacity}: the stack already holds {len(self._items)} elements."
                )
        self._max_capacity = max_capacity

    # -- operations ----------------------------------------------------
    def push(self, value: Any) -> None:
        if self.is_full():
            raise StackOverflowError(f"Stack overflow: capacity of {self._max_capacity} reached.")
        self._items.append(value)

    def pop(self) -> Any:
        if not self._items:
            raise StackUnderflowError("Stack underflow: the stack is empty, nothing to pop.")
        return self._items.pop()

    def peek(self) -> Any:
        if not self._items:
            raise StackUnderflowError("The stack is empty, nothing to peek.")
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
        """Elements from bottom to top (a copy)."""
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items!r}, max_capacity={self._max_capacity!r})"
