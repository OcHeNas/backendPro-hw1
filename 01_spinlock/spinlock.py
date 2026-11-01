from internal.futex import AtomicUInt32


class Spinlock:
    def __init__(self):
        self._locked = AtomicUInt32()

    def lock(self):
        while not self.try_lock():
            pass

    def try_lock(self):
        return self._locked.compare_exchange(0, 1)

    def unlock(self):
        if self._locked.exchange(0) == 0:
            raise RuntimeError("unlock of an unlocked spinlock")

    Lock, TryLock, Unlock = lock, try_lock, unlock


class TTAS(Spinlock):
    def lock(self):
        while True:
            while self._locked.load():
                pass
            if self.try_lock():
                return

    Lock = lock
