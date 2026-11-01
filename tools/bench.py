from pathlib import Path
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if "--child" not in sys.argv:
    subprocess.run([sys.executable, __file__, "--child"], check=True, timeout=60)
    sys.exit()

from primitives import Barrier, Mutex, Once, RWMutex, Semaphore, Spinlock, TTAS, WaitGroup
from tests.support import Threads


def measure(label, operation, count=3000):
    start = time.perf_counter()
    for _ in range(count):
        operation()
    elapsed = time.perf_counter() - start
    print(f"{label:30s} {elapsed * 1e6 / count:10.2f} us/operation", flush=True)


for factory in (Spinlock, TTAS, Mutex):
    lock = factory()
    measure(factory.__name__ + " uncontended", lambda: (lock.lock(), lock.unlock()))
    pool = Threads()

    def worker():
        for _ in range(300):
            lock.lock()
            lock.unlock()

    start = time.perf_counter()
    for _ in range(4):
        pool.start(worker)
    pool.join()
    print(f"{factory.__name__ + ' contended':30s} {(time.perf_counter()-start)*1e6/1200:10.2f} us/op")

lock = threading.Lock()
measure("threading.Lock uncontended", lambda: (lock.acquire(), lock.release()))
semaphore = Semaphore(1)
measure("Semaphore acquire/release", lambda: (semaphore.acquire(), semaphore.release()))
group = WaitGroup()
measure("WaitGroup add/done/wait", lambda: (group.add(1), group.done(), group.wait()))
once = Once()
once.do(lambda: None)
measure("Once completed", lambda: once.do(lambda: None))
rw = RWMutex()
measure("RWMutex read", lambda: (rw.rlock(), rw.runlock()))
barrier = Barrier(4)
pool = Threads()
start = time.perf_counter()


def participant():
    for _ in range(300):
        barrier.wait()


for _ in range(4):
    pool.start(participant)
pool.join()
print(f"{'Barrier 4 threads':30s} {(time.perf_counter()-start)*1e6/1200:10.2f} us/pass")
