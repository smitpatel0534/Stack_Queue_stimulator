"""Headless smoke test of the real UI code using fake widgets (see fake_gui.py).

It proves that every page builds, every button handler runs, and the pages stay in
sync with the simulator. It cannot check pixels, so launch the app once to judge looks.
"""
import csv
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import fake_gui  # noqa: E402

_patcher = None


def _purge_ui_modules():
    for name in [m for m in sys.modules if m == "ui" or m.startswith("ui.")]:
        del sys.modules[name]


def setUpModule():
    global _patcher
    _purge_ui_modules()
    _patcher = mock.patch.dict(sys.modules, fake_gui.install())
    _patcher.start()


def tearDownModule():
    _patcher.stop()
    _purge_ui_modules()


class GuiSmokeTests(unittest.TestCase):
    def setUp(self):
        from settings_manager import SettingsManager
        from simulator import Simulator
        from ui import theme
        from ui.app import App

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = pathlib.Path(self._tmp.name)
        theme.set_mode("dark")
        self.sim = Simulator(SettingsManager(self.dir / "settings.json"))
        self.app = App(self.sim)
        self.pages = self.app.pages
        fake_gui.CONFIRM["answer"] = True

    def type_into(self, entry, text):
        entry.delete(0, "end")
        entry.insert(0, text)

    def test_every_nav_item_opens_its_page(self):
        self.assertEqual(set(self.pages), {"dashboard", "stack", "queue", "history", "visualizer",
                                           "settings", "about"})
        for key, page in self.pages.items():
            self.app.show_page(key)
            self.assertEqual(self.app.current, key)
            self.assertEqual(self.app.title_label.cget("text"), page.title)
            self.assertTrue(page.description)

    def test_stack_page_buttons(self):
        page = self.pages["stack"]
        self.app.show_page("stack")
        self.type_into(page.entry, "alpha")
        page.do_push()
        self.assertEqual(self.sim.stack.to_list(), ["alpha"])
        self.assertEqual(page.entry.get(), "")
        self.assertIn("Pushed", page.message.cget("text"))
        page.do_push()  # empty input
        self.assertIn("empty", page.message.cget("text").lower())
        self.type_into(page.entry, "beta")
        page.do_push()
        page.do_peek()
        self.assertIn("beta", page.message.cget("text"))
        page.do_is_empty()
        page.do_pop()
        self.assertEqual(self.sim.stack.to_list(), ["alpha"])
        self.assertEqual(page._info_values[1].cget("text"), "alpha")
        page.do_clear()
        self.assertTrue(self.sim.stack.is_empty())
        page.do_pop()
        self.assertIn("underflow", page.message.cget("text").lower())
        self.assertEqual(self.sim.stats()["total"], 8)

    def test_clear_respects_confirmation(self):
        page = self.pages["stack"]
        self.sim.push("x")
        fake_gui.CONFIRM["answer"] = False
        page.do_clear()
        self.assertEqual(self.sim.stack.size, 1)
        fake_gui.CONFIRM["answer"] = True
        page.do_clear()
        self.assertEqual(self.sim.stack.size, 0)

    def test_queue_page_buttons(self):
        page = self.pages["queue"]
        self.app.show_page("queue")
        for value in ("a", "b", "c"):
            self.type_into(page.entry, value)
            page.do_enqueue()
        self.assertEqual(self.sim.queue.to_list(), ["a", "b", "c"])
        page.do_front()
        self.assertIn("'a'", page.message.cget("text"))
        page.do_rear()
        self.assertIn("'c'", page.message.cget("text"))
        page.do_dequeue()
        self.assertEqual(self.sim.queue.to_list(), ["b", "c"])
        page.do_is_empty()
        page.do_clear()
        self.assertTrue(self.sim.queue.is_empty())
        page.do_dequeue()
        self.assertIn("underflow", page.message.cget("text").lower())

    def test_capacity_overflow_is_shown_not_raised(self):
        self.sim.apply_settings({**self.sim.settings.to_dict(), "max_stack_capacity": 1})
        page = self.pages["stack"]
        self.type_into(page.entry, "1")
        page.do_push()
        self.type_into(page.entry, "2")
        page.do_push()
        self.assertIn("overflow", page.message.cget("text").lower())
        self.assertEqual(self.sim.stack.to_list(), ["1"])

    def test_dashboard_stats_and_quick_actions(self):
        page = self.pages["dashboard"]
        self.app.show_page("dashboard")
        self.assertEqual(page.stat_cards["total"].value_label.cget("text"), "0")
        self.type_into(page.entry, "x")
        page.do_push()
        self.type_into(page.entry, "y")
        page.do_enqueue()
        page.do_pop()
        page.do_pop()  # fails
        page.do_dequeue()
        cards = {k: c.value_label.cget("text") for k, c in page.stat_cards.items()}
        self.assertEqual(cards, {"stack_size": "0", "queue_size": "0", "total": "5",
                                 "successful": "4", "failed": "1"})
        self.assertEqual(self.app.status_label.cget("text").strip(), "\u25cf  Last operation succeeded")

    def test_history_page_filters_search_clear_export(self):
        page = self.pages["history"]
        self.app.show_page("history")
        self.assertEqual(len(page.tree.rows), 0)
        self.sim.push("apple")
        self.sim.enqueue("banana")
        self.sim.pop()
        self.sim.pop()  # fails
        page.refresh()
        self.assertEqual(len(page.tree.rows), 4)
        self.assertEqual(page.tree.rows[0][1], ("failed",))  # newest first
        page.structure_filter.set("Queue")
        page.refresh()
        self.assertEqual(len(page.tree.rows), 1)
        page.structure_filter.set("All structures")
        page.operation_filter.set("Pop")
        page.refresh()
        self.assertEqual(len(page.tree.rows), 2)
        page.operation_filter.set("All operations")
        page.search.insert(0, "apple")
        page.refresh()
        self.assertEqual(len(page.tree.rows), 2)  # push apple + pop apple

        page.search.delete(0, "end")
        out = self.dir / "export.csv"
        fake_gui.SAVE_PATH["value"] = str(out)
        page.do_export()
        with open(out, newline="", encoding="utf-8-sig") as handle:
            self.assertEqual(len(list(csv.reader(handle))), 5)
        self.assertIn("Exported 4", page.message.cget("text"))
        fake_gui.SAVE_PATH["value"] = ""
        page.do_export()  # cancelled dialog must not crash

        page.do_clear_history()
        self.assertEqual(len(page.tree.rows), 0)
        self.assertEqual(self.sim.stack.size, 0)
        self.sim.push("keep")
        page.do_clear_history()
        self.assertEqual(self.sim.stack.to_list(), ["keep"])
        page.do_export()
        self.assertIn("no history", page.message.cget("text").lower())

    def test_settings_apply_reset_and_theme(self):
        page = self.pages["settings"]
        self.app.show_page("settings")
        self.assertEqual(page.stack_entry.get(), "10")
        self.type_into(page.stack_entry, "5")
        self.type_into(page.history_entry, "50")
        self.type_into(page.developer_entry, "Test Dev")
        page.confirm_switch.deselect()
        page.do_apply()
        self.assertEqual(self.sim.settings.max_stack_capacity, 5)
        self.assertEqual(self.sim.stack.max_capacity, 5)
        self.assertEqual(self.sim.settings.history_limit, 50)
        self.assertFalse(self.sim.settings.confirm_before_clear)
        self.assertIn("saved", page.message.cget("text").lower())

        self.type_into(page.stack_entry, "abc")
        page.do_apply()
        self.assertIn("whole number", page.message.cget("text"))
        self.assertEqual(self.sim.settings.max_stack_capacity, 5)

        page.theme_switch.deselect()
        page.on_theme_switch()
        from ui import theme
        self.assertEqual(self.sim.settings.theme, "light")
        self.assertEqual(theme.get_mode(), "light")
        self.assertEqual(sys.modules["customtkinter"].mode, "light")
        self.app.toggle_theme()
        self.assertEqual(theme.get_mode(), "dark")

        page.do_reset()
        self.assertEqual(self.sim.settings.max_stack_capacity, 10)
        self.assertEqual(page.stack_entry.get(), "10")

    def test_about_shows_developer_text(self):
        self.sim.apply_settings({**self.sim.settings.to_dict(), "developer_info": "Configured text"})
        self.app.show_page("about")
        self.assertEqual(self.pages["about"].developer_label.cget("text"), "Configured text")

    def test_visualizer_and_all_pages_survive_large_data(self):
        self.sim.apply_settings({**self.sim.settings.to_dict(), "max_stack_capacity": 100,
                                 "max_queue_capacity": 100})
        for i in range(100):
            self.sim.push(f"value-{i}-" + "x" * 8)
            self.sim.enqueue(str(i))
        for key in self.pages:
            self.app.show_page(key)
        self.assertIn("Size 100", self.pages["visualizer"].stack_info.cget("text"))
        self.assertIn("total", self.pages["stack"].elements_label.cget("text"))

    def test_theme_toggle_refreshes_every_page(self):
        calls = []
        for page in self.pages.values():
            original = page.on_theme_changed
            page.on_theme_changed = (lambda o=original: (calls.append(1), o())[1])
        self.app.toggle_theme()
        self.assertEqual(len(calls), len(self.pages))

    def test_close_cancels_clock_and_unsubscribes(self):
        self.app._handle_close()
        self.assertNotIn(self.app._on_state_change, self.sim._listeners)


if __name__ == "__main__":
    unittest.main()
