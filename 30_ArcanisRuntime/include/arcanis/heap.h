#ifndef ARCANIS_HEAP_H
#define ARCANIS_HEAP_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define HEAP_MIN_BLOCK_SIZE 16
#define HEAP_MAGIC 0xDEADBEEF

typedef struct heap_block {
    uint32_t magic;
    size_t size;
    bool free;
    struct heap_block* next;
    struct heap_block* prev;
} heap_block_t;

void arc_heap_init(uint32_t start, size_t size);
void* arc_kmalloc(size_t size);
void* arc_kmalign(size_t size, size_t alignment);
void* arc_kcalloc(size_t count, size_t size);
void* arc_krealloc(void* ptr, size_t new_size);
void arc_kfree(void* ptr);
size_t arc_heap_get_used(void);
size_t arc_heap_get_free(void);
size_t arc_heap_get_total(void);
uint32_t arc_heap_get_block_count(void);

#endif
