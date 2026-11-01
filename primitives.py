from importlib import import_module

Spinlock = import_module("01_spinlock.spinlock").Spinlock
TTAS = import_module("01_spinlock.spinlock").TTAS
Mutex = import_module("02_mutex.mutex").Mutex
Semaphore = import_module("03_semaphore.semaphore").Semaphore
WaitGroup = import_module("04_waitgroup.waitgroup").WaitGroup
Once = import_module("05_once.once").Once
RWMutex = import_module("06_rwmutex.rwmutex").RWMutex
Barrier = import_module("07_barrier.barrier").Barrier
