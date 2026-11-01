import threading
import time
import unittest
from primitives import Semaphore
from internal.futex import MAX
from tests.support import Threads


class TestSemaphore(unittest.TestCase):
    def test_basics(self):
        semaphore = Semaphore(2)
        self.assertEqual(semaphore.available(), 2)
        semaphore.acquire()
        self.assertTrue(semaphore.try_acquire())
        self.assertFalse(semaphore.try_acquire())
        self.assertEqual(semaphore.available(), 0)
        semaphore.release()
        semaphore.release()
        self.assertEqual(semaphore.available(), 2)
        with self.assertRaises(ValueError):
            Semaphore(-1)
        with self.assertRaises(OverflowError):
            Semaphore(MAX).release()

    def test_zero_and_all_waiters_wake(self):
        semaphore = Semaphore(0)
        pool = Threads()
        passed = []

        def worker():
            semaphore.acquire()
            passed.append(1)

        for _ in range(30):
            pool.start(worker)
        time.sleep(0.01)
        self.assertEqual(passed, [])
        for _ in range(30):
            semaphore.release()
        pool.join()
        self.assertEqual(len(passed), 30)
        self.assertEqual(semaphore.available(), 0)

    def test_parallelism_and_limit(self):
        semaphore = Semaphore(3)
        gate = threading.Barrier(3)
        guard = threading.Lock()
        inside = 0
        peak = 0
        pool = Threads()

        def worker():
            nonlocal inside, peak
            semaphore.acquire()
            try:
                with guard:
                    inside += 1
                    peak = max(peak, inside)
                    self.assertLessEqual(inside, 3)
                gate.wait(timeout=5)
                time.sleep(0)
                with guard:
                    inside -= 1
            finally:
                semaphore.release()

        for _ in range(39):
            pool.start(worker)
        pool.join()
        self.assertEqual(peak, 3)
        self.assertEqual(semaphore.available(), 3)
