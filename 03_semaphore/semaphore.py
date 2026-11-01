from internal.futex import AtomicUInt32, MAX, uint32, wait, wake


class Semaphore:
    def __init__(self, n):
        self._permits = AtomicUInt32(uint32(n))

    def available(self):
        return self._permits.load()

    def try_acquire(self):
        while True:
            value = self._permits.load()
            if value == 0:
                return False
            if self._permits.compare_exchange(value, value - 1):
                return True

    def acquire(self):
        while not self.try_acquire():
            wait(self._permits, 0)

    def release(self):
        while True:
            value = self._permits.load()
            if value == MAX:
                raise OverflowError("semaphore counter overflow")
            if self._permits.compare_exchange(value, value + 1):
                break
        wake(self._permits)

    Acquire, TryAcquire, Release, Available = acquire, try_acquire, release, available


New = Semaphore
