"""Unit tests for the Stack (LIFO) data structure."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from errors import SimulatorError
from stack import Stack, StackOverflowError, StackUnderflowError


class StackTests(unittest.TestCase):
    def test_new_stack_is_empty(self):
        s = Stack()
        self.assertTrue(s.is_empty())
        self.assertEqual(s.size, 0)
        self.assertEqual(s.to_list(), [])

    def test_push_and_pop_follow_lifo(self):
        s = Stack()
        for value in ("a", "b", "c"):
            s.push(value)
        self.assertEqual(s.size, 3)
        self.assertEqual([s.pop(), s.pop(), s.pop()], ["c", "b", "a"])
        self.assertTrue(s.is_empty())

    def test_peek_does_not_remove(self):
        s = Stack()
        s.push(1)
        s.push(2)
        self.assertEqual(s.peek(), 2)
        self.assertEqual(s.size, 2)

    def test_to_list_is_bottom_to_top_copy(self):
        s = Stack()
        s.push(1)
        s.push(2)
        snapshot = s.to_list()
        snapshot.append(99)
        self.assertEqual(s.to_list(), [1, 2])

    def test_pop_empty_raises_underflow(self):
        with self.assertRaises(StackUnderflowError) as ctx:
            Stack().pop()
        self.assertIn("underflow", str(ctx.exception).lower())

    def test_peek_empty_raises_underflow(self):
        with self.assertRaises(StackUnderflowError):
            Stack().peek()

    def test_clear_returns_removed_count(self):
        s = Stack()
        s.push(1)
        s.push(2)
        self.assertEqual(s.clear(), 2)
        self.assertTrue(s.is_empty())
        self.assertEqual(s.clear(), 0)

    def test_capacity_overflow(self):
        s = Stack(max_capacity=2)
        s.push(1)
        self.assertFalse(s.is_full())
        s.push(2)
        self.assertTrue(s.is_full())
        with self.assertRaises(StackOverflowError) as ctx:
            s.push(3)
        self.assertIn("overflow", str(ctx.exception).lower())
        self.assertEqual(s.to_list(), [1, 2])

    def test_unlimited_when_capacity_none(self):
        s = Stack(None)
        for i in range(500):
            s.push(i)
        self.assertEqual(s.size, 500)
        self.assertFalse(s.is_full())

    def test_set_capacity_validation(self):
        s = Stack()
        s.push(1)
        s.push(2)
        for bad in (0, -1, 2.5, "3", True):
            with self.assertRaises(ValueError):
                s.set_capacity(bad)
        with self.assertRaises(ValueError):
            s.set_capacity(1)  # smaller than current size
        s.set_capacity(2)
        self.assertEqual(s.max_capacity, 2)

    def test_errors_are_simulator_errors(self):
        self.assertTrue(issubclass(StackOverflowError, SimulatorError))
        self.assertTrue(issubclass(StackUnderflowError, SimulatorError))


if __name__ == "__main__":
    unittest.main()
