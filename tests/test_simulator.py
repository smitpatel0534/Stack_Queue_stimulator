"""Tests for the Simulator service layer (stack + queue + history + settings together)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import csv
import tempfile

from constants import MAX_VALUE_LENGTH
from settings_manager import SettingsManager
from simulator import Simulator


class SimulatorTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.settings_path = pathlib.Path(self._tmp.name) / "settings.json"
        self.sim = Simulator(SettingsManager(self.settings_path))
        self.events = 0
        self.sim.subscribe(self._on_event)

    def _on_event(self):
        self.events += 1


class StackOperationTests(SimulatorTestCase):
    def test_push_pop_peek_modify_real_stack(self):
        self.assertTrue(self.sim.push("A").success)
        self.assertTrue(self.sim.push("B").success)
        self.assertEqual(self.sim.stack.to_list(), ["A", "B"])
        peek = self.sim.peek()
        self.assertTrue(peek.success)
        self.assertEqual(peek.value, "B")
        pop = self.sim.pop()
        self.assertEqual(pop.value, "B")
        self.assertEqual(self.sim.stack.to_list(), ["A"])

    def test_pop_and_peek_on_empty_fail_gracefully(self):
        for result in (self.sim.pop(), self.sim.peek()):
            self.assertFalse(result.success)
            self.assertTrue(result.message)
        self.assertEqual(self.sim.history.failed_operations, 2)

    def test_invalid_input_never_crashes_and_is_recorded(self):
        for bad in ("", "   ", None, "x" * (MAX_VALUE_LENGTH + 1), "bad\x00value", "tab\there"):
            result = self.sim.push(bad)
            self.assertFalse(result.success, repr(bad))
        self.assertEqual(self.sim.stack.size, 0)
        self.assertEqual(self.sim.history.failed_operations, 6)

    def test_value_is_trimmed_and_non_text_is_accepted(self):
        self.sim.push("  42  ")
        self.sim.push(7)
        self.assertEqual(self.sim.stack.to_list(), ["42", "7"])

    def test_stack_overflow_uses_configured_capacity(self):
        errors = self.sim.apply_settings({**self.sim.settings.to_dict(), "max_stack_capacity": 2})
        self.assertEqual(errors, [])
        self.sim.push("1")
        self.sim.push("2")
        result = self.sim.push("3")
        self.assertFalse(result.success)
        self.assertIn("overflow", result.message.lower())
        self.assertEqual(self.sim.stack.to_list(), ["1", "2"])

    def test_is_empty_and_clear(self):
        self.assertIn("empty", self.sim.stack_is_empty().message.lower())
        self.sim.push("a")
        self.assertIn("not empty", self.sim.stack_is_empty().message.lower())
        result = self.sim.clear_stack()
        self.assertTrue(result.success)
        self.assertIn("1", result.message)
        self.assertTrue(self.sim.stack.is_empty())
        self.assertTrue(self.sim.clear_stack().success)  # clearing an empty stack is fine


class QueueOperationTests(SimulatorTestCase):
    def test_enqueue_dequeue_front_rear(self):
        for v in ("A", "B", "C"):
            self.assertTrue(self.sim.enqueue(v).success)
        self.assertEqual(self.sim.peek_front().value, "A")
        self.assertEqual(self.sim.peek_rear().value, "C")
        self.assertEqual(self.sim.dequeue().value, "A")
        self.assertEqual(self.sim.queue.to_list(), ["B", "C"])

    def test_empty_queue_operations_fail_gracefully(self):
        for result in (self.sim.dequeue(), self.sim.peek_front(), self.sim.peek_rear()):
            self.assertFalse(result.success)
        self.assertIn("underflow", self.sim.dequeue().message.lower())

    def test_queue_overflow_and_invalid_input(self):
        self.sim.apply_settings({**self.sim.settings.to_dict(), "max_queue_capacity": 1})
        self.assertTrue(self.sim.enqueue("a").success)
        overflow = self.sim.enqueue("b")
        self.assertFalse(overflow.success)
        self.assertIn("overflow", overflow.message.lower())
        self.assertFalse(self.sim.enqueue("").success)

    def test_is_empty_and_clear(self):
        self.assertTrue(self.sim.queue_is_empty().success)
        self.sim.enqueue("a")
        self.sim.enqueue("b")
        self.assertIn("2", self.sim.clear_queue().message)
        self.assertTrue(self.sim.queue.is_empty())


class HistoryIntegrationTests(SimulatorTestCase):
    def test_history_matches_operations_performed(self):
        self.sim.push("x")
        self.sim.pop()
        self.sim.pop()  # fails
        self.sim.enqueue("y")
        records, matched = self.sim.query_history()
        self.assertEqual(matched, 4)
        self.assertEqual([r.number for r in records], [4, 3, 2, 1])
        self.assertEqual([r.operation for r in records], ["Enqueue", "Pop", "Pop", "Push"])
        self.assertEqual([r.structure for r in records], ["Queue", "Stack", "Stack", "Stack"])
        self.assertEqual([r.success for r in records], [True, False, True, True])
        self.assertEqual(records[3].value, "x")
        self.assertEqual(records[2].value, "x")  # the popped value
        self.assertEqual(records[1].value, "")

    def test_statistics_are_accurate(self):
        self.sim.push("a")
        self.sim.push("b")
        self.sim.enqueue("c")
        self.sim.dequeue()
        self.sim.dequeue()  # fails
        self.assertEqual(self.sim.stats(), {"stack_size": 2, "queue_size": 0,
                                            "total": 5, "successful": 4, "failed": 1})

    def test_display_limit_does_not_change_totals(self):
        raw = self.sim.settings.to_dict()
        raw.update(history_limit=10, max_stack_capacity=100)
        self.assertEqual(self.sim.apply_settings(raw), [])
        for i in range(25):
            self.sim.push(str(i))
        shown, matched = self.sim.query_history()
        self.assertEqual(len(shown), 10)
        self.assertEqual(matched, 25)
        self.assertEqual(self.sim.stats()["total"], 25)
        self.assertEqual(shown[0].value, "24")

    def test_filters_and_search_through_simulator(self):
        self.sim.push("apple")
        self.sim.enqueue("banana")
        self.sim.dequeue()
        self.assertEqual(self.sim.query_history(structure="Queue")[1], 2)
        self.assertEqual(self.sim.query_history(operation="Push")[1], 1)
        self.assertEqual(self.sim.query_history(search="apple")[1], 1)

    def test_clearing_history_does_not_touch_structures(self):
        self.sim.push("keep")
        self.sim.enqueue("me")
        self.sim.clear_history()
        self.assertEqual(self.sim.stack.to_list(), ["keep"])
        self.assertEqual(self.sim.queue.to_list(), ["me"])
        self.assertEqual(self.sim.query_history()[1], 0)
        self.assertEqual(self.sim.stats()["total"], 0)
        self.assertEqual(self.sim.stats()["stack_size"], 1)

    def test_clearing_structures_does_not_touch_history(self):
        self.sim.push("a")
        self.sim.clear_stack()
        self.assertEqual(self.sim.query_history()[1], 2)

    def test_listeners_fire_once_per_operation(self):
        self.sim.push("a")
        self.sim.pop()
        self.sim.pop()
        self.assertEqual(self.events, 3)
        self.sim.clear_history()
        self.assertEqual(self.events, 4)

    def test_csv_export_respects_filters_and_is_valid(self):
        self.sim.push("a")
        self.sim.enqueue("b")
        self.sim.enqueue("")
        path = pathlib.Path(self._tmp.name) / "history.csv"
        ok, message = self.sim.export_history(str(path), structure="Queue")
        self.assertTrue(ok, message)
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(len(rows), 3)  # header + 2 queue records
        self.assertEqual(rows[1][2], "Enqueue")  # oldest first
        self.assertEqual(rows[1][4], "Success")
        self.assertEqual(rows[2][4], "Failed")

    def test_export_with_nothing_or_bad_path_reports_error(self):
        path = pathlib.Path(self._tmp.name) / "none.csv"
        self.assertFalse(self.sim.export_history(str(path))[0])
        self.assertFalse(path.exists())
        self.sim.push("a")
        ok, message = self.sim.export_history(str(pathlib.Path(self._tmp.name) / "no_dir" / "x.csv"))
        self.assertFalse(ok)
        self.assertIn("failed", message.lower())


class SettingsIntegrationTests(SimulatorTestCase):
    def test_invalid_settings_are_not_applied(self):
        before = self.sim.settings.to_dict()
        errors = self.sim.apply_settings({**before, "max_stack_capacity": "0", "history_limit": "x"})
        self.assertEqual(len(errors), 2)
        self.assertEqual(self.sim.settings.to_dict(), before)
        self.assertEqual(self.sim.stack.max_capacity, before["max_stack_capacity"])

    def test_cannot_lower_capacity_below_current_size(self):
        for i in range(5):
            self.sim.push(str(i))
        for i in range(4):
            self.sim.enqueue(str(i))
        errors = self.sim.apply_settings({**self.sim.settings.to_dict(),
                                          "max_stack_capacity": 3, "max_queue_capacity": 2})
        self.assertEqual(len(errors), 2)
        self.assertEqual(self.sim.stack.max_capacity, 10)

    def test_settings_persist_and_apply_after_restart(self):
        self.assertEqual(self.sim.apply_settings({**self.sim.settings.to_dict(), "theme": "light",
                                                  "max_stack_capacity": 3, "max_queue_capacity": 4}), [])
        restarted = Simulator(SettingsManager(self.settings_path))
        self.assertEqual(restarted.settings.theme, "light")
        self.assertEqual(restarted.stack.max_capacity, 3)
        self.assertEqual(restarted.queue.max_capacity, 4)

    def test_set_theme_and_reset(self):
        self.assertEqual(self.sim.set_theme("light"), [])
        self.assertEqual(self.sim.settings.theme, "light")
        self.assertTrue(self.sim.set_theme("neon"))
        self.assertEqual(self.sim.settings.theme, "light")
        self.assertEqual(self.sim.reset_settings(), [])
        self.assertEqual(self.sim.settings.theme, "dark")
        self.assertEqual(SettingsManager(self.settings_path).settings.theme, "dark")

    def test_unwritable_settings_path_is_reported_not_raised(self):
        blocker = pathlib.Path(self._tmp.name) / "blocker"
        blocker.write_text("file, not a folder")
        sim = Simulator(SettingsManager(blocker / "settings.json"))
        errors = sim.apply_settings({**sim.settings.to_dict(), "theme": "light"})
        self.assertTrue(errors)
        self.assertEqual(sim.settings.theme, "dark")


if __name__ == "__main__":
    unittest.main()
