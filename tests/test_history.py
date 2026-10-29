"""Unit tests for the history manager."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import csv
import tempfile
from datetime import datetime

from history_manager import CSV_HEADER, HistoryManager


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.h = HistoryManager()

    def test_add_numbers_records_and_counts(self):
        r1 = self.h.add("Stack", "Push", "1", True, "ok")
        r2 = self.h.add("Stack", "Pop", "", False, "underflow")
        self.assertEqual((r1.number, r2.number), (1, 2))
        self.assertEqual(self.h.total_operations, 2)
        self.assertEqual(self.h.successful_operations, 1)
        self.assertEqual(self.h.failed_operations, 1)
        self.assertEqual(r2.status, "Failed")

    def test_query_is_newest_first_and_limited(self):
        for i in range(5):
            self.h.add("Stack", "Push", str(i))
        self.assertEqual([r.value for r in self.h.query(limit=2)], ["4", "3"])

    def test_filters_and_search(self):
        self.h.add("Stack", "Push", "apple")
        self.h.add("Queue", "Enqueue", "banana")
        self.h.add("Queue", "Dequeue", "banana")
        self.assertEqual(len(self.h.query(structure="Queue")), 2)
        self.assertEqual(len(self.h.query(operation="Push")), 1)
        self.assertEqual(len(self.h.query(structure="Queue", operation="Dequeue")), 1)
        self.assertEqual(len(self.h.query(search="BANANA")), 2)
        self.assertEqual(self.h.query(search="zzz"), [])

    def test_totals_survive_storage_cap(self):
        small = HistoryManager(max_records=3)
        for i in range(10):
            small.add("Stack", "Push", str(i))
        self.assertEqual(len(small), 3)
        self.assertEqual(small.total_operations, 10)

    def test_clear_resets_everything(self):
        self.h.add("Stack", "Push", "1")
        self.h.clear()
        self.assertEqual(len(self.h), 0)
        self.assertEqual(self.h.total_operations, 0)
        self.assertEqual(self.h.add("Stack", "Push", "1").number, 1)

    def test_export_csv_is_valid(self):
        self.h.add("Stack", "Push", "a,b", True, 'said "hi"', datetime(2026, 1, 2, 3, 4, 5))
        self.h.add("Queue", "Dequeue", "", False, "empty")
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "out.csv"
            self.assertEqual(self.h.export_csv(path), 2)
            with open(path, newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.reader(handle))
        self.assertEqual(tuple(rows[0]), CSV_HEADER)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1][3], "a,b")
        self.assertEqual(rows[1][5], 'said "hi"')
        self.assertEqual(rows[1][6], "2026-01-02 03:04:05")

    def test_invalid_storage_size(self):
        with self.assertRaises(ValueError):
            HistoryManager(max_records=0)


if __name__ == "__main__":
    unittest.main()
