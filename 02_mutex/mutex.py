from internal.futex import AtomicUInt32, wait, wake


class Mutex:
    def __init__(self):
        self._state = AtomicUInt32()

    def try_lock(self):
        return self._state.compare_exchange(0, 1)

    def lock(self):
        if self.try_lock():
            return
        while self._state.exchange(2) != 0:
            wait(self._state, 2)

    def unlock(self):
        old = self._state.exchange(0)
        if old == 0:
            raise RuntimeError("unlock of an unlocked mutex")
        if old == 2:
            wake(self._state)

    Lock, TryLock, Unlock = lock, try_lock, unlock
