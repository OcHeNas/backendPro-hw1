import unittest
from primitives import Mutex
from tests.support import LockContract, Threads


class TestMutex(LockContract, unittest.TestCase):
    factory = Mutex

    def test_handoff_under_load(self):
        lock = Mutex()
        passes = [0] * 16
        pool = Threads()

        def worker(index):
            for _ in range(80):
                lock.lock()
                passes[index] += 1
                lock.unlock()

        for index in range(16):
            pool.start(lambda index=index: worker(index))
        pool.join()
        self.assertEqual(passes, [80] * 16)
