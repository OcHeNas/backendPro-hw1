#ifndef NATIVE_H
#define NATIVE_H
#include <stdint.h>
typedef struct atomic_word atomic_word;
atomic_word *word_new(uint32_t value);
void word_free(atomic_word *word);
uint32_t word_load(atomic_word *word);
void word_store(atomic_word *word, uint32_t value);
int word_cas(atomic_word *word, uint32_t expected, uint32_t desired);
uint32_t word_exchange(atomic_word *word, uint32_t value);
uint32_t word_add(atomic_word *word, uint32_t delta);
int word_wait(atomic_word *word, uint32_t expected);
int word_wake(atomic_word *word, int count);
#endif
