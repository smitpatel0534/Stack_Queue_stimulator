"""Minimal in-memory stand-ins for customtkinter / tkinter.

They let the real UI code (pages, handlers, layout calls) run on machines
without a display, so wiring mistakes are caught by the test-suite. They do NOT
render anything, so they cannot verify appearance.
"""
from __future__ import annotations

import sys
import types

SAVE_PATH = {"value": ""}
CONFIRM = {"answer": True}


class FakeWidget:
    def __init__(self, *args, **kwargs):
        self._value = kwargs.get("text", "")
        self._kw = dict(kwargs)
        self.master = args[0] if args else None
        self._calls = []

    def configure(self, **kwargs):
        self._kw.update(kwargs)
        if "text" in kwargs:
            self._value = kwargs["text"]

    config = configure

    def cget(self, name):
        return self._kw.get(name)

    def get(self):
        return self._value

    def set(self, value):
        self._value = value

    def after(self, ms, func=None, *args):
        return "job"

    def winfo_width(self):
        return 640

    def winfo_height(self):
        return 420

    def winfo_screenwidth(self):
        return 1920

    def winfo_screenheight(self):
        return 1080

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None


class FakeEntry(FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = ""

    def insert(self, index, text):
        self._value = str(text)

    def delete(self, first, last=None):
        self._value = ""


class FakeSwitch(FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = 0

    def select(self, *a):
        self._value = 1

    def deselect(self, *a):
        self._value = 0


class FakeOption(FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        values = kwargs.get("values") or [""]
        self._value = values[0]


class FakeTree(FakeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = []

    def insert(self, parent, index, values=(), tags=()):
        self.rows.append((tuple(values), tuple(tags)))
        return str(len(self.rows))

    def get_children(self, *a):
        return [str(i + 1) for i in range(len(self.rows))]

    def delete(self, *ids):
        self.rows = []


class FakeStyle:
    def __init__(self, *a, **k):
        pass

    def configure(self, *a, **k):
        pass

    def map(self, *a, **k):
        pass

    def theme_use(self, *a):
        pass


class FakeFont:
    def __init__(self, *a, **k):
        pass


def install():
    """Insert fake modules into sys.modules. Returns the dict of installed names."""
    ctk = types.ModuleType("customtkinter")
    for name in ("CTk", "CTkFrame", "CTkLabel", "CTkButton", "CTkScrollbar"):
        setattr(ctk, name, type(name, (FakeWidget,), {}))
    ctk.CTkEntry = FakeEntry
    ctk.CTkSwitch = FakeSwitch
    ctk.CTkOptionMenu = FakeOption
    ctk.CTkFont = FakeFont
    ctk.mode = "dark"
    ctk.set_appearance_mode = lambda m: setattr(ctk, "mode", m)
    ctk.get_appearance_mode = lambda: ctk.mode.title()

    tk = types.ModuleType("tkinter")
    tk.Canvas = type("Canvas", (FakeWidget,), {})
    tk.Frame = type("Frame", (FakeWidget,), {})
    tk.TclError = type("TclError", (Exception,), {})

    messagebox = types.ModuleType("tkinter.messagebox")
    messagebox.askyesno = lambda *a, **k: CONFIRM["answer"]
    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.asksaveasfilename = lambda *a, **k: SAVE_PATH["value"]
    ttk = types.ModuleType("tkinter.ttk")
    ttk.Style = FakeStyle
    ttk.Treeview = FakeTree
    tk.messagebox, tk.filedialog, tk.ttk = messagebox, filedialog, ttk

    return {"customtkinter": ctk, "tkinter": tk, "tkinter.messagebox": messagebox,
            "tkinter.filedialog": filedialog, "tkinter.ttk": ttk}
