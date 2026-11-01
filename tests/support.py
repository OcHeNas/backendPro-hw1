import threading
import time
import unittest


class Threads:

    def __init__(self):
        self.threads = []
        self.errors = []
        self.guard = threading.Lock()

    def start(self, function):
        def run():
            try:
                function()
            except BaseException as error:
                with self.guard:
                    self.errors.append(error)

        thread = threading.Thread(target=run, daemon=True)
        self.threads.append(thread)
        thread.start()
        return thread

    def join(self, timeout=15):
        deadline = time.monotonic() + timeout
        for thread in self.threads:
            thread.join(max(0, deadline - time.monotonic()))
        if any(thread.is_alive() for thread in self.threads):
            raise AssertionError("worker timeout (possible lost wakeup/deadlock)")
        if self.errors:
            raise self.errors[0]


class LockContract:
    def test_basics(self):
        lock = self.factory()
        for _ in range(2):
            lock.lock()
            lock.unlock()
        with self.assertRaises(RuntimeError):
            lock.unlock()
        self.assertTrue(lock.try_lock())
        pool = Threads()
        pool.start(lambda: self.assertFalse(lock.try_lock()))
        pool.join()
        lock.unlock()
        self.assertTrue(lock.try_lock())
        lock.unlock()

    def test_blocks_and_wakes_every_waiter(self):
        lock = self.factory()
        lock.lock()
        pool = Threads()
        passed = []

        def worker():
            lock.lock()
            try:
                passed.append(1)
            finally:
                lock.unlock()

        for _ in range(16):
            pool.start(worker)
        time.sleep(0.01)
        self.assertEqual(passed, [])
        lock.unlock()
        pool.join()
        self.assertEqual(len(passed), 16)

    def test_exclusion_and_no_lost_updates(self):
        lock = self.factory()
        counter = [0]
        inside = [0]
        pool = Threads()

        def worker():
            for _ in range(40):
                lock.lock()
                try:
                    inside[0] += 1
                    self.assertEqual(inside[0], 1)
                    old = counter[0]
                    time.sleep(0)
                    counter[0] = old + 1
                    inside[0] -= 1
                finally:
                    lock.unlock()

        for _ in range(8):
            pool.start(worker)
        pool.join()
        self.assertEqual(counter[0], 320)
