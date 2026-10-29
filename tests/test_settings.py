"""Unit tests for settings validation and persistence."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
import tempfile

from settings_manager import DEFAULTS, SettingsManager


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = pathlib.Path(self._tmp.name) / "data" / "settings.json"

    def test_first_run_creates_file_with_defaults(self):
        mgr = SettingsManager(self.path)
        self.assertTrue(self.path.exists())
        self.assertEqual(mgr.settings.to_dict(), DEFAULTS)
        self.assertIsNone(mgr.load_warning)

    def test_settings_persist_across_restart(self):
        mgr = SettingsManager(self.path)
        new, errors = mgr.validate({"theme": "light", "max_stack_capacity": "7",
                                    "max_queue_capacity": 12, "history_limit": "250",
                                    "confirm_before_clear": False, "developer_info": "  Ada  "})
        self.assertEqual(errors, [])
        mgr.commit(new)
        again = SettingsManager(self.path).settings
        self.assertEqual(again.theme, "light")
        self.assertEqual(again.max_stack_capacity, 7)
        self.assertEqual(again.max_queue_capacity, 12)
        self.assertEqual(again.history_limit, 250)
        self.assertFalse(again.confirm_before_clear)
        self.assertEqual(again.developer_info, "Ada")

    def test_invalid_values_are_rejected_and_keep_old_value(self):
        mgr = SettingsManager(self.path)
        bad = {"theme": "purple", "max_stack_capacity": "abc", "max_queue_capacity": 0,
               "history_limit": 5, "confirm_before_clear": "yes", "developer_info": "x" * 500}
        settings, errors = mgr.validate(bad)
        self.assertEqual(len(errors), 6)
        self.assertEqual(settings.to_dict(), DEFAULTS)

    def test_int_edge_cases(self):
        mgr = SettingsManager(self.path)
        for value in ("", " ", "1.5", "1_0", "-3", "101", True, None, 3.5):
            _, errors = mgr.validate({"max_stack_capacity": value})
            self.assertTrue(errors, f"{value!r} should be rejected")
        for value in ("1", " 100 ", 50, 20.0):
            _, errors = mgr.validate({"max_stack_capacity": value})
            self.assertEqual(errors, [], f"{value!r} should be accepted")

    def test_corrupt_file_falls_back_to_defaults(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        mgr = SettingsManager(self.path)
        self.assertEqual(mgr.settings.to_dict(), DEFAULTS)
        self.assertIsNotNone(mgr.load_warning)

    def test_partially_invalid_file_resets_only_bad_fields(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps({"theme": "light", "max_stack_capacity": 9999}), encoding="utf-8")
        mgr = SettingsManager(self.path)
        self.assertEqual(mgr.settings.theme, "light")
        self.assertEqual(mgr.settings.max_stack_capacity, DEFAULTS["max_stack_capacity"])
        self.assertIsNotNone(mgr.load_warning)

    def test_non_object_json_falls_back(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("[1, 2]", encoding="utf-8")
        self.assertEqual(SettingsManager(self.path).settings.to_dict(), DEFAULTS)


if __name__ == "__main__":
    unittest.main()
