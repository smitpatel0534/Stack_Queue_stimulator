"""Exception hierarchy used by the simulator."""
from __future__ import annotations


class SimulatorError(Exception):
    """Base class for every expected, user-facing error."""


class InvalidInputError(SimulatorError):
    """The value typed by the user cannot be used."""


class StructureOverflowError(SimulatorError):
    """An element was added to a structure that is already full."""


class StructureUnderflowError(SimulatorError):
    """An element was requested from an empty structure."""
