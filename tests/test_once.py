import threading
import time
import unittest
from primitives import Once
from tests.support import Threads


class TestOnce(unittest.TestCase):
    def test_basics_and_exception(self):
        once = Once()
        calls = []
        self.assertFalse(once.done())
        for _ in range(10):
            once.do(lambda: calls.append(1))
        self.assertTrue(once.done())
        self.assertEqual(calls, [1])
        once = Once()

        def fail():
            raise ValueError("expected")

        with self.assertRaises(ValueError):
            once.do(fail)
        self.assertTrue(once.done())
        once.do(lambda: self.fail("must not retry"))

    def test_concurrent_publication(self):
        once = Once()
        calls = []
        data = []
        pool = Threads()

        def initialize():
            calls.append(1)
            time.sleep(0.01)
            data.extend(range(10))

        def worker():
            once.do(initialize)
            self.assertEqual(data, list(range(10)))

        for _ in range(100):
            pool.start(worker)
        pool.join()
        self.assertEqual(calls, [1])

    def test_waits_for_winner_even_on_base_exception(self):
        for failing in (False, True):
            once = Once()
            started, release = threading.Event(), threading.Event()
            pool = Threads()
            passed = []

            def initialize():
                started.set()
                self.assertTrue(release.wait(5))
                if failing:
                    raise KeyboardInterrupt("expected")

            def winner():
                if failing:
                    with self.assertRaises(KeyboardInterrupt):
                        once.do(initialize)
                else:
                    once.do(initialize)

            def loser():
                once.do(lambda: self.fail("already running"))
                passed.append(1)

            pool.start(winner)
            self.assertTrue(started.wait(5))
            self.assertFalse(once.done())
            for _ in range(10):
                pool.start(loser)
            time.sleep(0.005)
            self.assertEqual(passed, [])
            release.set()
            pool.join()
            self.assertTrue(once.done())
            self.assertEqual(len(passed), 10)
