PYTHON ?= python3
CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Werror
PKGS := 01_spinlock 02_mutex 03_semaphore 04_waitgroup 05_once 06_rwmutex 07_barrier
.PHONY: all build test race stress bench vet check clean one $(PKGS) spinlock mutex semaphore waitgroup once rwmutex barrier
all: check
build: internal/futex/_native.so
internal/futex/_native.so: internal/futex/native.c internal/futex/native.h
	$(CC) $(CFLAGS) -shared -fPIC $< -o $@
test: build
	$(PYTHON) tools/run_tests.py
race: build
	$(PYTHON) tools/run_tests.py --race --repeat 3
stress: build
	$(PYTHON) tools/run_tests.py --repeat 100
bench: build
	$(PYTHON) tools/bench.py
vet:
	$(PYTHON) tools/lint.py
check: vet race stress
one: build vet
	$(PYTHON) tools/run_tests.py --only $(DIR)
	$(PYTHON) tools/run_tests.py --only $(DIR) --race
	$(PYTHON) tools/run_tests.py --only $(DIR) --repeat 20
spinlock: ; @$(MAKE) --no-print-directory one DIR=spinlock
mutex: ; @$(MAKE) --no-print-directory one DIR=mutex
semaphore: ; @$(MAKE) --no-print-directory one DIR=semaphore
waitgroup: ; @$(MAKE) --no-print-directory one DIR=waitgroup
once: ; @$(MAKE) --no-print-directory one DIR=once
rwmutex: ; @$(MAKE) --no-print-directory one DIR=rwmutex
barrier: ; @$(MAKE) --no-print-directory one DIR=barrier
$(PKGS):
	@$(MAKE) --no-print-directory one DIR=$@
clean:
	$(PYTHON) tools/clean.py

.PHONY: native-test tsan
native-test:
	mkdir -p build
	$(CC) $(CFLAGS) -pthread tests/native_test.c internal/futex/native.c -o build/native_test
	$(PYTHON) -c 'import subprocess; subprocess.run(["build/native_test"], check=True, timeout=30)'
tsan:
	mkdir -p build
	$(CC) -O1 -g -std=c11 -Wall -Wextra -Werror -fsanitize=thread -pthread tests/native_test.c internal/futex/native.c -o build/native_tsan
	$(PYTHON) -c 'import subprocess; subprocess.run(["build/native_tsan"], check=True, timeout=30)'
