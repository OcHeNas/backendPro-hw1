from importlib import import_module
from internal.futex import AtomicUInt32, wait, wake_all

Mutex = import_module("02_mutex.mutex").Mutex
WRITER = 1 << 31


class RWMutex:
    def __init__(self):
        self._state = AtomicUInt32()
        self._writers = Mutex()

    def rlock(self):
        while True:
            value = self._state.load()
            if value & WRITER:
                wait(self._state, value)
            elif value == WRITER - 1:
                raise OverflowError("reader count overflow")
            elif self._state.compare_exchange(value, value + 1):
                return

    def runlock(self):
        while True:
            value = self._state.load()
            if value & (WRITER - 1) == 0:
                raise RuntimeError("runlock without an active reader")
            if self._state.compare_exchange(value, value - 1):
                if value & (WRITER - 1) == 1:
                    wake_all(self._state)
                return

    def lock(self):
        self._writers.lock()
        while True:
            value = self._state.load()
            if self._state.compare_exchange(value, value | WRITER):
                break
        while True:
            value = self._state.load()
            if value == WRITER:
                return
            wait(self._state, value)

    def unlock(self):
        if not self._state.compare_exchange(WRITER, 0):
            raise RuntimeError("unlock without an active writer")
        wake_all(self._state)
        self._writers.unlock()

    RLock, RUnlock, Lock, Unlock = rlock, runlock, lock, unlock
