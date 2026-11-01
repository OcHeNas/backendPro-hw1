import time
import unittest
from internal.futex import MAX
from primitives import Barrier
from tests.support import Threads


class TestBarrier(unittest.TestCase):
    def test_single_and_invalid(self):
        barrier = Barrier(1)
        for _ in range(20):
            barrier.wait()
        for n in (0, -1, MAX + 1):
            with self.assertRaises(ValueError):
                Barrier(n)

    def test_nobody_passes_early(self):
        barrier = Barrier(3)
        passed = []
        pool = Threads()

        def worker():
            barrier.wait()
            passed.append(1)

        pool.start(worker)
        pool.start(worker)
        time.sleep(0.005)
        self.assertEqual(passed, [])
        pool.start(worker)
        pool.join()
        self.assertEqual(len(passed), 3)

    def test_reuse_and_generation_separation(self):
        barrier = Barrier(6)
        arrivals = [[False] * 6 for _ in range(100)]
        pool = Threads()

        def worker(index):
            for generation in range(100):
                if index == generation % 6:
                    time.sleep(0.0001)
                arrivals[generation][index] = True
                barrier.wait()
                self.assertTrue(all(arrivals[generation]))

        for index in range(6):
            pool.start(lambda index=index: worker(index))
        pool.join()
        self.assertTrue(all(all(row) for row in arrivals))

    def test_generation_wrap(self):
        barrier = Barrier(4)
        barrier._round.store(MAX - 1)
        pool = Threads()

        def worker():
            for _ in range(4):
                barrier.wait()

        for _ in range(4):
            pool.start(worker)
        pool.join()
        self.assertEqual(barrier._round.load(), 2)
