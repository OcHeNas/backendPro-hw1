from internal.futex import AtomicUInt32, wait, wake_all


class Once:
    def __init__(self):
        self._state = AtomicUInt32()

    def done(self):
        return self._state.load() == 2

    def do(self, function):
        if self.done():
            return
        if self._state.compare_exchange(0, 1):
            try:
                function()
            finally:
                self._state.store(2)
                wake_all(self._state)
        else:
            while self._state.load() != 2:
                wait(self._state, 1)

    Do, Done = do, done
