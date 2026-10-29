"""Entry point for the P17 Stack & Queue Operations Simulator."""
from __future__ import annotations

import sys


def main() -> int:
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print("CustomTkinter is not installed.\nRun:  python -m pip install -r requirements.txt")
        return 1

    from settings_manager import SettingsManager
    from simulator import Simulator
    from ui.app import App

    settings_manager = SettingsManager()
    if settings_manager.load_warning:
        print("Settings notice:", settings_manager.load_warning)
    App(Simulator(settings_manager)).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
