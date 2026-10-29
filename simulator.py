"""Application service layer: owns the stack, queue, history and settings.

The GUI talks only to this class, so every operation is recorded exactly once
and every listener is told when something changed.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from constants import MAX_VALUE_LENGTH, QUEUE, STACK
from errors import InvalidInputError, SimulatorError
from history_manager import HistoryManager, OperationRecord
from queue_structure import Queue
from settings_manager import DEFAULTS, Settings, SettingsManager
from stack import Stack

log = logging.getLogger(__name__)


class OperationResult:
    """Outcome of one operation."""

    __slots__ = ("success", "message", "value", "record")

    def __init__(self, success: bool, message: str, value: str = "",
                 record: Optional[OperationRecord] = None) -> None:
        self.success = success
        self.message = message
        self.value = value
        self.record = record

    def __repr__(self) -> str:
        return f"OperationResult(success={self.success!r}, message={self.message!r})"


class Simulator:
    def __init__(self, settings_manager: Optional[SettingsManager] = None,
                 history: Optional[HistoryManager] = None) -> None:
        self.settings_manager = settings_manager or SettingsManager()
        settings = self.settings_manager.settings
        self.stack = Stack(settings.max_stack_capacity)
        self.queue = Queue(settings.max_queue_capacity)
        self.history = history or HistoryManager()
        self.last_result: Optional[OperationResult] = None
        self._listeners: List[Callable[[], None]] = []

    # -- observers -----------------------------------------------------
    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    @property
    def settings(self) -> Settings:
        return self.settings_manager.settings

    # -- core runner ---------------------------------------------------
    @staticmethod
    def _clean_value(raw: Any) -> str:
        if raw is None:
            raise InvalidInputError("Enter a value first: the input is empty.")
        text = (raw if isinstance(raw, str) else str(raw)).strip()
        if not text:
            raise InvalidInputError("Enter a value first: the input is empty.")
        if len(text) > MAX_VALUE_LENGTH:
            raise InvalidInputError(
                f"Value is too long ({len(text)} characters). Use at most {MAX_VALUE_LENGTH}."
            )
        if not text.isprintable():
            raise InvalidInputError("Value contains characters that cannot be displayed.")
        return text

    def _execute(self, structure: str, operation: str,
                 action: Callable[[], Tuple[str, str]], typed: str = "") -> OperationResult:
        """Run ``action`` (returns message, value), record the outcome and notify."""
        try:
            message, value = action()
            success = True
        except SimulatorError as exc:
            message, value, success = str(exc), typed, False
        except Exception as exc:  # last-resort guard: the GUI must never crash
            log.exception("Unexpected error during %s %s", structure, operation)
            message, value, success = f"Unexpected error: {exc}", typed, False
        record = self.history.add(structure, operation, value, success, message)
        result = OperationResult(success, message, value, record)
        self.last_result = result
        self._notify()
        return result

    @staticmethod
    def _typed(raw: Any) -> str:
        return str(raw).strip()[:40] if raw is not None else ""

    # -- stack ---------------------------------------------------------
    def push(self, raw: Any) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self._clean_value(raw)
            self.stack.push(value)
            return f"Pushed '{value}' onto the stack. Size is now {self.stack.size}.", value
        return self._execute(STACK, "Push", action, self._typed(raw))

    def pop(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self.stack.pop()
            return f"Popped '{value}' from the stack. Size is now {self.stack.size}.", str(value)
        return self._execute(STACK, "Pop", action)

    def peek(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self.stack.peek()
            return f"Top element is '{value}'.", str(value)
        return self._execute(STACK, "Peek", action)

    def stack_is_empty(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            if self.stack.is_empty():
                return "The stack is empty.", ""
            return f"The stack is not empty ({self.stack.size} elements).", ""
        return self._execute(STACK, "Is Empty", action)

    def clear_stack(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            removed = self.stack.clear()
            return f"Stack cleared. {removed} element(s) removed.", ""
        return self._execute(STACK, "Clear", action)

    # -- queue ---------------------------------------------------------
    def enqueue(self, raw: Any) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self._clean_value(raw)
            self.queue.enqueue(value)
            return f"Enqueued '{value}' at the rear. Size is now {self.queue.size}.", value
        return self._execute(QUEUE, "Enqueue", action, self._typed(raw))

    def dequeue(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self.queue.dequeue()
            return f"Dequeued '{value}' from the front. Size is now {self.queue.size}.", str(value)
        return self._execute(QUEUE, "Dequeue", action)

    def peek_front(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self.queue.front()
            return f"Front element is '{value}'.", str(value)
        return self._execute(QUEUE, "Peek Front", action)

    def peek_rear(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            value = self.queue.rear()
            return f"Rear element is '{value}'.", str(value)
        return self._execute(QUEUE, "Peek Rear", action)

    def queue_is_empty(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            if self.queue.is_empty():
                return "The queue is empty.", ""
            return f"The queue is not empty ({self.queue.size} elements).", ""
        return self._execute(QUEUE, "Is Empty", action)

    def clear_queue(self) -> OperationResult:
        def action() -> Tuple[str, str]:
            removed = self.queue.clear()
            return f"Queue cleared. {removed} element(s) removed.", ""
        return self._execute(QUEUE, "Clear", action)

    # -- statistics and history ---------------------------------------
    def stats(self) -> Dict[str, int]:
        return {
            "stack_size": self.stack.size,
            "queue_size": self.queue.size,
            "total": self.history.total_operations,
            "successful": self.history.successful_operations,
            "failed": self.history.failed_operations,
        }

    def query_history(self, structure: Optional[str] = None, operation: Optional[str] = None,
                      search: Optional[str] = None, apply_limit: bool = True
                      ) -> Tuple[List[OperationRecord], int]:
        """Return (records to display, number of matching records)."""
        matches = self.history.query(structure, operation, search)
        shown = matches[: self.settings.history_limit] if apply_limit else matches
        return shown, len(matches)

    def clear_history(self) -> None:
        """Clear the activity log only; the stack and queue are untouched."""
        self.history.clear()
        self.last_result = None
        self._notify()

    def export_history(self, path: str, structure: Optional[str] = None,
                       operation: Optional[str] = None, search: Optional[str] = None
                       ) -> Tuple[bool, str]:
        records, _ = self.query_history(structure, operation, search, apply_limit=False)
        if not records:
            return False, "There are no history records to export."
        try:
            count = self.history.export_csv(path, list(reversed(records)))  # oldest first in the file
        except OSError as exc:
            return False, f"Export failed: {exc}"
        return True, f"Exported {count} record(s) to {path}"

    # -- settings ------------------------------------------------------
    def apply_settings(self, raw: Mapping[str, Any]) -> List[str]:
        """Validate and apply settings. Returns a list of error messages (empty on success)."""
        new, errors = self.settings_manager.validate(raw)
        if not errors:
            if new.max_stack_capacity < self.stack.size:
                errors.append(f"The stack holds {self.stack.size} elements. Pop or clear it before "
                              f"lowering the capacity to {new.max_stack_capacity}.")
            if new.max_queue_capacity < self.queue.size:
                errors.append(f"The queue holds {self.queue.size} elements. Dequeue or clear it before "
                              f"lowering the capacity to {new.max_queue_capacity}.")
        if errors:
            return errors
        try:
            self.settings_manager.commit(new)
        except OSError as exc:
            return [f"Settings could not be saved: {exc}"]
        self.stack.set_capacity(new.max_stack_capacity)
        self.queue.set_capacity(new.max_queue_capacity)
        self._notify()
        return []

    def set_theme(self, theme: str) -> List[str]:
        raw = self.settings.to_dict()
        raw["theme"] = theme
        return self.apply_settings(raw)

    def reset_settings(self) -> List[str]:
        return self.apply_settings(dict(DEFAULTS))
