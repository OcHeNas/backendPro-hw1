import copy
from importlib import import_module
import threading
import time
import unittest
from unittest.mock import patch
from internal.futex import AtomicUInt32, MAX, wait, wake, wake_all
from primitives import Mutex
from tests.support import Threads


class TestFutex(unittest.TestCase):
    def test_operations_and_validation(self):
        word = AtomicUInt32(7)
        self.assertEqual(word.load(), 7)
        self.assertFalse(word.compare_exchange(6, 8))
        self.assertTrue(word.compare_exchange(7, 9))
        self.assertEqual(word.exchange(3), 9)
        self.assertEqual(word.fetch_add(-1), 3)
        self.assertEqual(word.load(), 2)
        word.store(MAX)
        self.assertEqual(word.fetch_add(1), MAX)
        self.assertEqual(word.load(), 0)
        with self.assertRaises(ValueError):
            word.store(-1)
        with self.assertRaises(TypeError):
            AtomicUInt32(1.5)
        with self.assertRaises(TypeError):
            copy.copy(word)
        with self.assertRaises(TypeError):
            copy.deepcopy(word)

    def test_parallel_cas_and_add(self):
        cas = AtomicUInt32()
        added = AtomicUInt32()
        pool = Threads()

        def worker():
            for _ in range(100):
                added.fetch_add(1)
                while True:
                    old = cas.load()
                    if cas.compare_exchange(old, old + 1):
                        break

        for _ in range(8):
            pool.start(worker)
        pool.join()
        self.assertEqual(cas.load(), 800)
        self.assertEqual(added.load(), 800)

    def test_mismatch_and_wake_before_wait(self):
        word = AtomicUInt32()
        word.store(1)
        wake_all(word)
        wait(word, 0)

    def test_spurious_wake_does_not_change_predicate(self):
        word = AtomicUInt32()
        pool = Threads()
        finished = threading.Event()

        def worker():
            while word.load() == 0:
                wait(word, 0)
            finished.set()

        pool.start(worker)
        for _ in range(10):
            wake(word)
            time.sleep(0)
        self.assertFalse(finished.is_set())
        word.store(1)
        wake_all(word)
        pool.join()
        self.assertTrue(finished.is_set())

    def test_forced_unlock_between_check_and_wait(self):
        module = import_module("02_mutex.mutex")
        lock = Mutex()
        lock.lock()
        at_wait, proceed = threading.Event(), threading.Event()
        pool = Threads()
        original_wait = module.wait

        def delayed_wait(word, expected):
            at_wait.set()
            self.assertTrue(proceed.wait(5))
            original_wait(word, expected)

        def worker():
            lock.lock()
            lock.unlock()

        with patch.object(module, "wait", delayed_wait):
            pool.start(worker)
            self.assertTrue(at_wait.wait(5))
            lock.unlock()
            proceed.set()
            pool.join()
