import threading
import time
import unittest
from primitives import RWMutex
from tests.support import Threads


class TestRWMutex(unittest.TestCase):
    def test_invalid_unlock(self):
        lock = RWMutex()
        with self.assertRaises(RuntimeError):
            lock.unlock()
        with self.assertRaises(RuntimeError):
            lock.runlock()
        lock.lock()
        with self.assertRaises(RuntimeError):
            lock.runlock()
        lock.unlock()
        lock.rlock()
        with self.assertRaises(RuntimeError):
            lock.unlock()
        lock.runlock()

    def test_writer_excludes_everyone(self):
        lock = RWMutex()
        lock.lock()
        pool = Threads()
        passed = []

        def reader():
            lock.rlock()
            passed.append(1)
            lock.runlock()

        def writer():
            lock.lock()
            passed.append(1)
            lock.unlock()

        pool.start(reader)
        pool.start(writer)
        time.sleep(0.005)
        self.assertEqual(passed, [])
        lock.unlock()
        pool.join()
        self.assertEqual(len(passed), 2)

    def test_readers_go_together(self):
        lock = RWMutex()
        barrier = threading.Barrier(8)
        pool = Threads()

        def reader():
            lock.rlock()
            try:
                barrier.wait(timeout=5)
            finally:
                lock.runlock()

        for _ in range(8):
            pool.start(reader)
        pool.join()

    def test_writer_waits_for_last_reader_and_blocks_new_readers(self):
        lock = RWMutex()
        lock.rlock()
        lock.rlock()
        pool = Threads()
        order = []

        def writer():
            lock.lock()
            order.append("writer")
            lock.unlock()

        def reader():
            lock.rlock()
            order.append("reader")
            lock.runlock()

        pool.start(writer)
        deadline = time.monotonic() + 5
        while not lock._state.load() & (1 << 31):
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0)
        pool.start(reader)
        lock.runlock()
        time.sleep(0.005)
        self.assertEqual(order, [])
        lock.runlock()
        pool.join()
        self.assertEqual(order, ["writer", "reader"])

    def test_no_torn_state_or_lost_writes(self):
        lock = RWMutex()
        shared = [0]
        pool = Threads()

        def writer():
            for _ in range(60):
                lock.lock()
                try:
                    shared[0] += 1
                    time.sleep(0)
                    shared[0] += 1
                finally:
                    lock.unlock()

        def reader():
            for _ in range(60):
                lock.rlock()
                try:
                    self.assertEqual(shared[0] % 2, 0)
                    time.sleep(0)
                    self.assertEqual(shared[0] % 2, 0)
                finally:
                    lock.runlock()

        for _ in range(4):
            pool.start(writer)
        for _ in range(8):
            pool.start(reader)
        pool.join()
        self.assertEqual(shared[0], 480)
