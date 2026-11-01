import unittest
from primitives import Spinlock, TTAS
from tests.support import LockContract


class TestSpinlock(LockContract, unittest.TestCase):
    factory = Spinlock


class TestTTAS(LockContract, unittest.TestCase):
    factory = TTAS
