#include "../internal/futex/native.h"
#include <assert.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>

static atomic_word *counter;
static atomic_word *signal_word;
static void *increment(void *unused) {
    (void)unused;
    for (int i = 0; i < 10000; ++i) word_add(counter, 1);
    return NULL;
}
static void *waiter(void *unused) {
    (void)unused;
    while (word_load(signal_word) == 0) assert(word_wait(signal_word, 0) == 0);
    return NULL;
}
int main(void) {
    pthread_t threads[8];
    counter = word_new(0);
    signal_word = word_new(0);
    assert(counter && signal_word);
    for (int i = 0; i < 8; ++i) assert(!pthread_create(&threads[i], NULL, increment, NULL));
    for (int i = 0; i < 8; ++i) assert(!pthread_join(threads[i], NULL));
    assert(word_load(counter) == 80000);
    assert(word_cas(counter, 80000, 1));
    assert(!word_cas(counter, 80000, 2));
    assert(word_exchange(counter, 4) == 1);
    for (int i = 0; i < 8; ++i) assert(!pthread_create(&threads[i], NULL, waiter, NULL));
    word_store(signal_word, 1);
    assert(word_wake(signal_word, INT32_MAX) == 0);
    for (int i = 0; i < 8; ++i) assert(!pthread_join(threads[i], NULL));
    assert(word_wait(signal_word, 0) == 0);
    word_free(counter);
    word_free(signal_word);
    puts("Native parallel atomics and futex: OK");
    return 0;
}
