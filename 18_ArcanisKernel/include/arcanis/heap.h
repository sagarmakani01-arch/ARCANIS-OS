#ifndef ARCANIS_HEAP_H
#define ARCANIS_HEAP_H

#include <arcanis/types.h>

typedef struct heap_block {
    size_t size;
    bool   free;
    struct heap_block* next;
} heap_block_t;

void heap_initialize(uint32_t start, size_t size);
void* kmalloc(size_t size);
void* kmalloc_aligned(size_t size);
void  kfree(void* ptr);
size_t heap_get_used(void);
size_t heap_get_free(void);

#endif
