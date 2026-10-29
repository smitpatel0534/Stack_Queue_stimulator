"""Shared constants for the P17 Stack & Queue Operations Simulator."""
from __future__ import annotations

APP_NAME = "P17 Stack & Queue Operations Simulator"
APP_SHORT = "P17"
APP_VERSION = "1.0.0"

STACK = "Stack"
QUEUE = "Queue"
STRUCTURES = (STACK, QUEUE)

STACK_OPERATIONS = ("Push", "Pop", "Peek", "Is Empty", "Clear")
QUEUE_OPERATIONS = ("Enqueue", "Dequeue", "Peek Front", "Peek Rear", "Is Empty", "Clear")
ALL_OPERATIONS = (
    "Push", "Pop", "Peek",
    "Enqueue", "Dequeue", "Peek Front", "Peek Rear",
    "Is Empty", "Clear",
)

MAX_VALUE_LENGTH = 20
