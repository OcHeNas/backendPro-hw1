"""C11 sequentially consistent atomics and Linux private futex.

CDLL releases the GIL for every native call, including atomic operations.
The opaque allocation never moves. Each active method retains its owner.
"""

import ctypes
import os
from pathlib import Path
import sys

MAX = (1 << 32) - 1


def uint32(value):
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("expected an integer")
    if not 0 <= value <= MAX:
        raise ValueError("expected a uint32")
    return value


if sys.platform != "linux":
    raise ImportError("Linux/WSL is required for this futex backend")
_path = Path(__file__).with_name("_native.so")
if not _path.is_file():
    raise ImportError("native backend is missing: run make build")
_lib = ctypes.CDLL(str(_path))
for _name, _args, _result in (
    ("word_new", [ctypes.c_uint32], ctypes.c_void_p),
    ("word_free", [ctypes.c_void_p], None),
    ("word_load", [ctypes.c_void_p], ctypes.c_uint32),
    ("word_store", [ctypes.c_void_p, ctypes.c_uint32], None),
    ("word_cas", [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32], ctypes.c_int),
    ("word_exchange", [ctypes.c_void_p, ctypes.c_uint32], ctypes.c_uint32),
    ("word_add", [ctypes.c_void_p, ctypes.c_uint32], ctypes.c_uint32),
    ("word_wait", [ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
    ("word_wake", [ctypes.c_void_p, ctypes.c_int], ctypes.c_int),
):
    _function = getattr(_lib, _name)
    _function.argtypes = _args
    _function.restype = _result


class AtomicUInt32:
    """Fixed-lifetime native word; do not copy or mutate private fields."""

    __slots__ = ("_ptr",)

    def __init__(self, value=0):
        self._ptr = _lib.word_new(uint32(value))
        if not self._ptr:
            raise MemoryError("allocation failed or uint32 atomics are not lock-free")

    def __del__(self):
        pointer = getattr(self, "_ptr", None)
        if pointer:
            _lib.word_free(pointer)

    def __copy__(self):
        raise TypeError("atomic words cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("atomic words cannot be copied")

    def load(self):
        return _lib.word_load(self._ptr)

    def store(self, value):
        _lib.word_store(self._ptr, uint32(value))

    def compare_exchange(self, expected, desired):
        return bool(_lib.word_cas(self._ptr, uint32(expected), uint32(desired)))

    def exchange(self, value):
        return _lib.word_exchange(self._ptr, uint32(value))

    def fetch_add(self, delta):
        """Return old value; arithmetic wraps modulo 2**32, including subtraction."""
        if not isinstance(delta, int) or isinstance(delta, bool):
            raise TypeError("delta must be an integer")
        return _lib.word_add(self._ptr, delta & MAX)


def wait(word, expected):
    error = _lib.word_wait(word._ptr, uint32(expected))
    if error:
        raise OSError(error, os.strerror(error))


def _wake(word, count):
    error = _lib.word_wake(word._ptr, count)
    if error:
        raise OSError(error, os.strerror(error))


def wake(word):
    _wake(word, 1)


def wake_all(word):
    _wake(word, (1 << 31) - 1)


Wait, Wake, WakeAll = wait, wake, wake_all
