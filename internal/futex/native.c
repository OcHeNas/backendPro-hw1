#define _GNU_SOURCE
#include "native.h"
#include <stdatomic.h>
#include <stdlib.h>
#include <errno.h>
#include <stddef.h>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>

struct atomic_word { _Atomic uint32_t value; };
_Static_assert(sizeof(_Atomic uint32_t) == 4, "futex needs 32 bits");
_Static_assert(_Alignof(struct atomic_word) >= 4, "futex needs alignment");
_Static_assert(offsetof(struct atomic_word, value) == 0, "word layout");

atomic_word *word_new(uint32_t value) {
    atomic_word *word = malloc(sizeof(*word));
    if (!word) return NULL;
    atomic_init(&word->value, value);
    if (!atomic_is_lock_free(&word->value)) { free(word); return NULL; }
    return word;
}
void word_free(atomic_word *word) { free(word); }
uint32_t word_load(atomic_word *word) { return atomic_load(&word->value); }
void word_store(atomic_word *word, uint32_t v) { atomic_store(&word->value, v); }
int word_cas(atomic_word *word, uint32_t expected, uint32_t desired) {
    return atomic_compare_exchange_strong(&word->value, &expected, desired);
}
uint32_t word_exchange(atomic_word *word, uint32_t v) {
    return atomic_exchange(&word->value, v);
}
uint32_t word_add(atomic_word *word, uint32_t delta) {
    return atomic_fetch_add(&word->value, delta);
}
int word_wait(atomic_word *word, uint32_t expected) {
    long rc = syscall(SYS_futex, &word->value, FUTEX_WAIT_PRIVATE,
                      expected, NULL, NULL, 0);
    if (rc == 0 || errno == EAGAIN || errno == EINTR) return 0;
    return errno;
}
int word_wake(atomic_word *word, int count) {
    long rc = syscall(SYS_futex, &word->value, FUTEX_WAKE_PRIVATE,
                      count, NULL, NULL, 0);
    return rc < 0 ? errno : 0;
}
