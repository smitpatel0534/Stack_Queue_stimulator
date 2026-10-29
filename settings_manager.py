"""Validated, persistent application settings stored as JSON."""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

THEMES = ("dark", "light")
LIMITS = {
    "max_stack_capacity": (1, 100),
    "max_queue_capacity": (1, 100),
    "history_limit": (10, 1000),
}
LABELS = {
    "max_stack_capacity": "Maximum stack capacity",
    "max_queue_capacity": "Maximum queue capacity",
    "history_limit": "History display limit",
    "theme": "Theme",
    "confirm_before_clear": "Confirm before clear",
    "developer_info": "Developer information",
}
MAX_DEVELOPER_INFO = 120
DEFAULT_DEVELOPER_INFO = "Developer details not set yet. Add your name, course and institution in Settings."

DEFAULTS: Dict[str, Any] = {
    "theme": "dark",
    "max_stack_capacity": 10,
    "max_queue_capacity": 10,
    "history_limit": 100,
    "confirm_before_clear": True,
    "developer_info": DEFAULT_DEVELOPER_INFO,
}


def app_dir() -> Path:
    """Folder containing the app (next to the .exe when packaged with PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_settings_path() -> Path:
    return app_dir() / "data" / "settings.json"


@dataclass(frozen=True)
class Settings:
    theme: str = DEFAULTS["theme"]
    max_stack_capacity: int = DEFAULTS["max_stack_capacity"]
    max_queue_capacity: int = DEFAULTS["max_queue_capacity"]
    history_limit: int = DEFAULTS["history_limit"]
    confirm_before_clear: bool = DEFAULTS["confirm_before_clear"]
    developer_info: str = DEFAULTS["developer_info"]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -- field coercion -----------------------------------------------------
def _coerce_int(name: str, value: Any) -> int:
    low, high = LIMITS[name]
    message = f"{LABELS[name]} must be a whole number between {low} and {high}."
    if isinstance(value, bool):
        raise ValueError(message)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, str):
        text = value.strip()
        if not re.fullmatch(r"[+-]?[0-9]+", text):
            raise ValueError(message)
        value = int(text)
    if not isinstance(value, int) or not (low <= value <= high):
        raise ValueError(message)
    return value


def _coerce_theme(name: str, value: Any) -> str:
    text = str(value).strip().lower()
    if text not in THEMES:
        raise ValueError("Theme must be 'dark' or 'light'.")
    return text


def _coerce_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{LABELS[name]} must be on or off.")
    return value


def _coerce_text(name: str, value: Any) -> str:
    text = str(value).strip()
    if len(text) > MAX_DEVELOPER_INFO:
        raise ValueError(f"{LABELS[name]} must be at most {MAX_DEVELOPER_INFO} characters.")
    if not text.isprintable():
        raise ValueError(f"{LABELS[name]} contains characters that cannot be displayed.")
    return text or DEFAULT_DEVELOPER_INFO


_COERCERS = {
    "theme": _coerce_theme,
    "max_stack_capacity": _coerce_int,
    "max_queue_capacity": _coerce_int,
    "history_limit": _coerce_int,
    "confirm_before_clear": _coerce_bool,
    "developer_info": _coerce_text,
}


class SettingsManager:
    """Loads, validates and saves :class:`Settings`."""

    def __init__(self, path: Union[str, Path, None] = None) -> None:
        self.path = Path(path) if path else default_settings_path()
        self.load_warning: Optional[str] = None
        self._settings = Settings()
        self.load()

    @property
    def settings(self) -> Settings:
        return self._settings

    # -- validation ----------------------------------------------------
    def validate(self, raw: Mapping[str, Any], base: Optional[Settings] = None) -> Tuple[Settings, List[str]]:
        """Return (settings, errors). Invalid or missing fields keep the ``base`` value."""
        base_values = (base or self._settings).to_dict()
        values: Dict[str, Any] = {}
        errors: List[str] = []
        for name in DEFAULTS:
            candidate = raw.get(name, base_values[name])
            try:
                values[name] = _COERCERS[name](name, candidate)
            except ValueError as exc:
                errors.append(str(exc))
                values[name] = base_values[name]
        return Settings(**values), errors

    # -- persistence ---------------------------------------------------
    def load(self) -> Settings:
        self.load_warning = None
        defaults = Settings()
        if not self.path.exists():
            self._settings = defaults
            try:
                self._write(defaults)
            except OSError as exc:
                self.load_warning = f"Could not create the settings file: {exc}"
            return self._settings
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            self._settings = defaults
            self.load_warning = f"Settings file could not be read, defaults were used ({exc})."
            return self._settings
        if not isinstance(data, dict):
            self._settings = defaults
            self.load_warning = "Settings file has an unexpected format, defaults were used."
            return self._settings
        settings, errors = self.validate(data, base=defaults)
        self._settings = settings
        if errors:
            self.load_warning = "Some saved settings were invalid and were reset: " + " ".join(errors)
        return settings

    def commit(self, settings: Settings) -> None:
        """Save to disk first; only then make the new settings current."""
        self._write(settings)
        self._settings = settings

    def _write(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
        os.replace(temp, self.path)
