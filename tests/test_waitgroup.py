import time
import unittest
from internal.futex import MAX
from primitives import WaitGroup
from tests.support import Threads


class TestWaitGroup(unittest.TestCase):
    def test_zero_negative_and_overflow(self):
        group = WaitGroup()
        group.wait()
        group.add(0)
        with self.assertRaises(RuntimeError):
            group.done()
        group.wait()
        group.add(MAX)
        with self.assertRaises(OverflowError):
            group.add(1)
        group.add(-MAX)
        group.wait()

    def test_blocks_and_wakes_all(self):
        group = WaitGroup()
        group.add(2)
        pool = Threads()
        passed = []

        def worker():
            group.wait()
            passed.append(1)

        for _ in range(30):
            pool.start(worker)
        time.sleep(0.005)
        self.assertEqual(passed, [])
        group.done()
        time.sleep(0.005)
        self.assertEqual(passed, [])
        group.done()
        pool.join()
        self.assertEqual(len(passed), 30)

    def test_reuse_and_publication(self):
        group = WaitGroup()
        for _ in range(12):
            values = [None] * 20
            pool = Threads()
            group.add(20)

            def worker(index):
                time.sleep(0)
                values[index] = index
                group.done()

            for index in range(20):
                pool.start(lambda index=index: worker(index))
            group.wait()
            self.assertEqual(values, list(range(20)))
            pool.join()
