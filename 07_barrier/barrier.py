from importlib import import_module
from internal.futex import AtomicUInt32, uint32, wait, wake_all

Mutex = import_module("02_mutex.mutex").Mutex


class Barrier:
    def __init__(self, n):
        self._need = uint32(n)
        if n == 0:
            raise ValueError("barrier needs at least one participant")
        self._arrived = AtomicUInt32()
        self._round = AtomicUInt32()
        self._gate = Mutex()

    def wait(self):
        self._gate.lock()
        try:
            generation = self._round.load()
            last = self._arrived.fetch_add(1) + 1 == self._need
            if last:
                self._arrived.store(0)
                self._round.fetch_add(1)
        finally:
            self._gate.unlock()
        if last:
            wake_all(self._round)
        else:
            while self._round.load() == generation:
                wait(self._round, generation)

    Wait = wait


New = Barrier
