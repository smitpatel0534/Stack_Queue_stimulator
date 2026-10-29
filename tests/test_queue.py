"""Unit tests for the Queue (FIFO) data structure."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from errors import SimulatorError
from queue_structure import Queue, QueueOverflowError, QueueUnderflowError


class QueueTests(unittest.TestCase):
    def test_new_queue_is_empty(self):
        q = Queue()
        self.assertTrue(q.is_empty())
        self.assertEqual(q.size, 0)

    def test_enqueue_and_dequeue_follow_fifo(self):
        q = Queue()
        for value in ("a", "b", "c"):
            q.enqueue(value)
        self.assertEqual([q.dequeue(), q.dequeue(), q.dequeue()], ["a", "b", "c"])
        self.assertTrue(q.is_empty())

    def test_front_and_rear(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        self.assertEqual(q.front(), 1)
        self.assertEqual(q.rear(), 3)
        self.assertEqual(q.size, 3)

    def test_single_element_is_front_and_rear(self):
        q = Queue()
        q.enqueue("x")
        self.assertEqual(q.front(), q.rear())

    def test_to_list_is_front_to_rear(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        self.assertEqual(q.to_list(), [1, 2])

    def test_empty_operations_raise_underflow(self):
        q = Queue()
        for call in (q.dequeue, q.front, q.rear):
            with self.assertRaises(QueueUnderflowError):
                call()

    def test_dequeue_underflow_message(self):
        with self.assertRaises(QueueUnderflowError) as ctx:
            Queue().dequeue()
        self.assertIn("underflow", str(ctx.exception).lower())

    def test_clear(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        self.assertEqual(q.clear(), 2)
        self.assertTrue(q.is_empty())

    def test_capacity_overflow(self):
        q = Queue(max_capacity=2)
        q.enqueue(1)
        q.enqueue(2)
        self.assertTrue(q.is_full())
        with self.assertRaises(QueueOverflowError) as ctx:
            q.enqueue(3)
        self.assertIn("overflow", str(ctx.exception).lower())
        self.assertEqual(q.to_list(), [1, 2])

    def test_space_is_reused_after_dequeue(self):
        q = Queue(max_capacity=2)
        q.enqueue(1)
        q.enqueue(2)
        q.dequeue()
        q.enqueue(3)
        self.assertEqual(q.to_list(), [2, 3])

    def test_set_capacity_validation(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        for bad in (0, -5, 1.5, "2", False):
            with self.assertRaises(ValueError):
                q.set_capacity(bad)
        with self.assertRaises(ValueError):
            q.set_capacity(1)

    def test_errors_are_simulator_errors(self):
        self.assertTrue(issubclass(QueueOverflowError, SimulatorError))
        self.assertTrue(issubclass(QueueUnderflowError, SimulatorError))


if __name__ == "__main__":
    unittest.main()
