from internal.futex import AtomicUInt32, MAX, wait, wake_all


class WaitGroup:
    def __init__(self):
        self._count = AtomicUInt32()

    def add(self, delta):
        if not isinstance(delta, int) or isinstance(delta, bool):
            raise TypeError("delta must be an integer")
        while True:
            old = self._count.load()
            new = old + delta
            if new < 0:
                raise RuntimeError("negative WaitGroup counter")
            if new > MAX:
                raise OverflowError("WaitGroup counter overflow")
            if self._count.compare_exchange(old, new):
                if new == 0:
                    wake_all(self._count)
                return

    def done(self):
        self.add(-1)

    def wait(self):
        while True:
            value = self._count.load()
            if value == 0:
                return
            wait(self._count, value)

    Add, Done, Wait = add, done, wait
