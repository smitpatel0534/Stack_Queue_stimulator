"""Tests for the pure layout maths used by the visualizer."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from visualizer import compute_queue_layout, compute_stack_layout, shorten


class LayoutTests(unittest.TestCase):
    def assert_inside(self, layout, width, height):
        for c in layout.cells:
            self.assertGreaterEqual(c.x0, 0)
            self.assertGreaterEqual(c.y0, 0)
            self.assertLessEqual(c.x1, width)
            self.assertLessEqual(c.y1, height)

    def test_empty(self):
        self.assertEqual(compute_stack_layout(0, 400, 300).cells, ())
        self.assertEqual(compute_queue_layout(0, 400, 300).cells, ())

    def test_small_stack_shows_everything_bottom_up(self):
        layout = compute_stack_layout(3, 400, 400)
        self.assertEqual(layout.hidden, 0)
        self.assertEqual([c.index for c in layout.cells], [0, 1, 2])
        ys = [c.y0 for c in layout.cells]
        self.assertEqual(ys, sorted(ys, reverse=True))  # higher index = higher on screen
        self.assert_inside(layout, 400, 400)

    def test_large_stack_never_overflows_and_keeps_top(self):
        for count in (20, 100, 1000):
            layout = compute_stack_layout(count, 420, 360)
            self.assertGreater(layout.hidden, 0)
            self.assertIn(count - 1, [c.index for c in layout.cells])
            self.assertEqual(layout.cells[0].kind, "gap")
            self.assert_inside(layout, 420, 360)
            items = [c for c in layout.cells if c.kind == "item"]
            self.assertEqual(layout.hidden + len(items), count)

    def test_cells_do_not_overlap_in_stack(self):
        layout = compute_stack_layout(30, 400, 400)
        cells = sorted(layout.cells, key=lambda c: c.y0)
        for upper, lower in zip(cells, cells[1:]):
            self.assertLessEqual(upper.y1, lower.y0 + 1e-6)

    def test_small_queue_is_left_to_right(self):
        layout = compute_queue_layout(4, 800, 300)
        self.assertEqual([c.index for c in layout.cells], [0, 1, 2, 3])
        xs = [c.x0 for c in layout.cells]
        self.assertEqual(xs, sorted(xs))
        self.assert_inside(layout, 800, 300)

    def test_large_queue_keeps_front_and_rear_with_gap(self):
        for width in (320, 560, 900):
            layout = compute_queue_layout(100, width, 300)
            indices = [c.index for c in layout.cells if c.kind == "item"]
            self.assertEqual(indices[0], 0)
            self.assertEqual(indices[-1], 99)
            self.assertEqual(sum(1 for c in layout.cells if c.kind == "gap"), 1)
            self.assertEqual(layout.hidden + len(indices), 100)
            self.assert_inside(layout, width, 300)

    def test_shorten(self):
        self.assertEqual(shorten("abc", 5), "abc")
        self.assertEqual(shorten("abcdefghij", 5), "abcd\u2026")
        self.assertEqual(len(shorten("abcdefghij", 5)), 5)


if __name__ == "__main__":
    unittest.main()
